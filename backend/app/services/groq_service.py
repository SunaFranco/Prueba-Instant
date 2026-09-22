import json
import logging
import random
import time
from typing import List, Dict, Any, Optional
from groq import Groq, RateLimitError, APIError
from app.config import Config
from app.schemas.dtos import GroqRecommendationOutput

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
    def generate_movie_recommendation(
        cls,
        user_likes: List[Dict[str, Any]],
        username: str = "Usuario"
    ) -> GroqRecommendationOutput:
        """
        Genera una recomendación de película personalizada basada en la lista de películas
        que le gustaron al usuario.
        """
        client = cls._get_groq_client()
        if client is None:
            logger.warning("Cliente de Groq no disponible. Usando recomendación simulada.")
            return cls._get_mock_recommendation(user_likes)

        # 1. Construcción del resumen de películas favoritas
        liked_movies_summary = []
        for m in user_likes[:15]: # Limitar a las últimas 15 películas para optimizar TPM
            title = m.get("title", "")
            genres = ", ".join(m.get("genres", [])) if isinstance(m.get("genres"), list) else ""
            year = m.get("release_date", "")[:4] if m.get("release_date") else ""
            liked_movies_summary.append(f"- {title} ({year}) [Géneros: {genres}]")

        context_text = "\n".join(liked_movies_summary) if liked_movies_summary else "El usuario aún no tiene películas marcadas con 'Me gusta'."

        # 2. System y User Prompts
        system_prompt = (
            "Eres un experto curador de cine y crítico cinematográfico de clase mundial. "
            "Tu objetivo es recomendar UNA ÚNICA película altamente afín a los gustos del usuario, "
            "explicando de manera convincente, atractiva y personalizada por qué le encantará.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. Debes responder EXCLUSIVAMENTE en formato JSON válido.\n"
            "2. El JSON debe tener exactamente esta estructura:\n"
            "{\n"
            '  "title": "Nombre de la película recomendada",\n'
            '  "release_year": 2014,\n'
            '  "rationale": "Explicación detallada de 2 a 4 oraciones conectando sus películas favoritas con esta recomendación.",\n'
            '  "genres": ["Ciencia ficción", "Aventura"]\n'
            "}\n"
            "3. NO recomiendes ninguna película que ya esté en la lista de películas que le gustaron al usuario.\n"
            "4. Idioma de la justificación: Español."
        )

        user_prompt = (
            f"Usuario: {username}\n"
            f"Películas que le gustaron recientemente:\n{context_text}\n\n"
            f"Por favor recomiéndale una excelente película basada en sus preferencias."
        )

        # 3. Invocación a Groq con reintentos y Exponential Backoff
        attempts = 0
        max_attempts = Config.GROQ_RETRY_MAX_ATTEMPTS

        while attempts < max_attempts:
            attempts += 1
            try:
                logger.info(f"Llamando a Groq API ({Config.GROQ_MODEL}), intento {attempts}/{max_attempts}...")
                chat_completion = client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=500
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
                # Validar con Pydantic
                recommendation = GroqRecommendationOutput(**parsed_json)
                return recommendation

            except RateLimitError as e:
                logger.warning(f"Groq Rate Limit alcanzado (429) en intento {attempts}: {str(e)}")
                if attempts >= max_attempts:
                    raise e
                # Backoff exponencial con jitter
                backoff_time = (2 ** attempts) + random.uniform(0.5, 1.5)
                logger.info(f"Esperando {backoff_time:.2f}s antes de reintentar llamada a Groq...")
                time.sleep(backoff_time)

            except Exception as e:
                logger.error(f"Error durante inferencia en Groq: {str(e)}")
                if attempts >= max_attempts:
                    raise e
                time.sleep(1.5)

        raise RuntimeError("No se pudo obtener recomendación de Groq tras múltiples intentos.")

    @staticmethod
    def _get_mock_recommendation(user_likes: List[Dict[str, Any]]) -> GroqRecommendationOutput:
        """Recomendación simulada en caso de no contar con API key de Groq."""
        has_sci_fi = any("Ciencia" in str(m.get("genres", [])) for m in user_likes)
        if has_sci_fi:
            return GroqRecommendationOutput(
                title="Blade Runner 2049",
                release_year=2017,
                rationale="Basado en tu interés por la ciencia ficción profunda y los dilemas existenciales, esta secuela dirigida por Denis Villeneuve ofrece una atmósfera visual inigualable y una narrativa filosófica cautivadora.",
                genres=["Ciencia ficción", "Drama", "Misterio"]
            )
        return GroqRecommendationOutput(
            title="The Grand Budapest Hotel",
            release_year=2014,
            rationale="Te recomendamos esta obra maestra de Wes Anderson por su estilo visual único, ritmo dinámico y personajes inolvidables que garantizan una experiencia cinematográfica enriquecedora.",
            genres=["Comedia", "Aventura", "Drama"]
        )
