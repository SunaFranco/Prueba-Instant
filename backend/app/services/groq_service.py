import json
import logging
import random
import time
from typing import List, Dict, Any, Optional
from groq import Groq, RateLimitError, APIError
from app.config import Config
from app.schemas.dtos import GroqMovieItem, GroqRecommendationListOutput

logger = logging.getLogger(__name__)

class GroqService:
    """Servicio de inferencia con Groq Cloud API y estructuración de respuestas."""

    @staticmethod
    def _get_groq_client() -> Optional[Groq]:
        if not Config.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY no configurada.")
            return None
        return Groq(api_key=Config.GROQ_API_KEY)

    @classmethod
    def generate_movie_recommendations(
        cls,
        user_likes: List[Dict[str, Any]],
        excluded_titles: Optional[List[str]] = None,
        username: str = "Usuario"
    ) -> List[GroqMovieItem]:
        """
        Genera una lista de 10 recomendaciones de películas diversas basadas en los gustos
        del usuario, excluyendo películas ya vistas o recomendadas previamente.
        """
        client = cls._get_groq_client()
        if client is None:
            logger.warning("Cliente de Groq no disponible. Usando recomendaciones simuladas.")
            return cls._get_mock_recommendations(user_likes)

        # 1. Construcción del resumen de películas favoritas
        liked_movies_summary = []
        for m in user_likes[:15]: # Limitar a las últimas 15 películas para optimizar tokens
            title = m.get("title", "")
            genres = ", ".join(m.get("genres", [])) if isinstance(m.get("genres"), list) else ""
            year = m.get("release_date", "")[:4] if m.get("release_date") else ""
            liked_movies_summary.append(f"- {title} ({year}) [Géneros: {genres}]")

        context_text = "\n".join(liked_movies_summary) if liked_movies_summary else "El usuario aún no tiene películas marcadas con 'Me gusta'."

        # 2. Resumen de películas ya recomendadas para instruir al LLM a evitar repetirlas
        excluded_summary = ""
        if excluded_titles:
            sample_excluded = excluded_titles[:25]
            excluded_summary = "\nPelículas que YA vio o que YA se le recomendaron (NO las vuelvas a recomendar):\n" + "\n".join([f"- {t}" for t in sample_excluded])

        # 3. System y User Prompts
        system_prompt = (
            "Eres un experto curador de cine y crítico cinematográfico de clase mundial. "
            "Tu objetivo es recomendar una lista variada y de alta calidad de 10 (DIEZ) películas afines a los gustos del usuario, "
            "explicando de manera convincente, atractiva y personalizada por qué le encantará cada una.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. Debes responder EXCLUSIVAMENTE en formato JSON válido.\n"
            "2. El JSON debe contener una propiedad raíz 'recommendations' con un array de exactamente 10 objetos con esta estructura:\n"
            "{\n"
            '  "recommendations": [\n'
            '    {\n'
            '      "title": "Nombre de la película",\n'
            '      "release_year": 2014,\n'
            '      "rationale": "Explicación detallada de 2 a 3 oraciones conectando sus películas favoritas con esta recomendación.",\n'
            '      "genres": ["Ciencia ficción", "Aventura"]\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "3. NO incluyas ninguna película que ya esté en la lista de favoritos ni en la lista de películas ya recomendadas.\n"
            "4. Idioma de la justificación: Español."
        )

        user_prompt = (
            f"Usuario: {username}\n"
            f"Películas que le gustaron recientemente:\n{context_text}\n"
            f"{excluded_summary}\n\n"
            f"Por favor recomiéndale 10 películas excelentes y no repetidas basadas en sus preferencias."
        )

        # 4. Invocación a Groq con reintentos y Exponential Backoff
        attempts = 0
        max_attempts = Config.GROQ_RETRY_MAX_ATTEMPTS

        while attempts < max_attempts:
            attempts += 1
            try:
                logger.info(f"Llamando a Groq API ({Config.GROQ_MODEL}) para 10 recomendaciones, intento {attempts}/{max_attempts}...")
                chat_completion = client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=2500
                )

                content = (chat_completion.choices[0].message.content or "").strip()
                logger.debug(f"Respuesta cruda de Groq: {content}")

                # Limpieza de posibles bloques markdown de código (```json ... ```)
                if content.startswith("```"):
                    lines = content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()

                parsed_json = json.loads(content)

                # Si el modelo devolvió {"recommendations": [...]} o una lista directa
                if isinstance(parsed_json, dict) and "recommendations" in parsed_json:
                    items = parsed_json["recommendations"]
                elif isinstance(parsed_json, list):
                    items = parsed_json
                else:
                    items = [parsed_json]

                validated_items = []
                for item in items:
                    try:
                        validated_items.append(GroqMovieItem(**item))
                    except Exception as val_err:
                        logger.warning(f"Item descartado por validación inválida: {val_err}")

                if validated_items:
                    return validated_items
                raise ValueError("No se pudieron extraer items válidos de la respuesta de Groq.")

            except RateLimitError as e:
                logger.warning(f"Groq Rate Limit alcanzado (429) en intento {attempts}: {str(e)}")
                if attempts >= max_attempts:
                    raise e
                backoff_time = (2 ** attempts) + random.uniform(0.5, 1.5)
                logger.info(f"Esperando {backoff_time:.2f}s antes de reintentar llamada a Groq...")
                time.sleep(backoff_time)

            except Exception as e:
                logger.error(f"Error durante inferencia en Groq: {str(e)}")
                if attempts >= max_attempts:
                    raise e
                time.sleep(1.5)

        raise RuntimeError("No se pudo obtener recomendación de Groq tras múltiples intentos.")

    # Retrocompatibilidad para llamadas que esperen un único item
    @classmethod
    def generate_movie_recommendation(
        cls,
        user_likes: List[Dict[str, Any]],
        username: str = "Usuario"
    ) -> GroqMovieItem:
        recs = cls.generate_movie_recommendations(user_likes=user_likes, username=username)
        return recs[0]

    @staticmethod
    def _get_mock_recommendations(user_likes: List[Dict[str, Any]]) -> List[GroqMovieItem]:
        """Recomendaciones simuladas en caso de no contar con API key de Groq."""
        return [
            GroqMovieItem(
                title="Blade Runner 2049",
                release_year=2017,
                rationale="Basado en tu interés por la ciencia ficción profunda y los dilemas existenciales, esta secuela dirigida por Denis Villeneuve ofrece una atmósfera visual inigualable.",
                genres=["Ciencia ficción", "Drama", "Misterio"]
            ),
            GroqMovieItem(
                title="The Grand Budapest Hotel",
                release_year=2014,
                rationale="Te recomendamos esta obra maestra de Wes Anderson por su estilo visual único, ritmo dinámico y personajes inolvidables.",
                genres=["Comedia", "Aventura", "Drama"]
            ),
            GroqMovieItem(
                title="Arrival",
                release_year=2016,
                rationale="Una fascinante exploración de la comunicación y el tiempo que desafía las convenciones del cine de ciencia ficción.",
                genres=["Ciencia ficción", "Drama", "Misterio"]
            )
        ]

