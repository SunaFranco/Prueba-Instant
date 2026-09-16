import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.config import Config
from app.queue.producer import get_redis_client
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

# Mapeo de géneros estándar de TMDB
GENRE_MAP = {
    28: "Acción", 12: "Aventura", 16: "Animación", 35: "Comedia", 80: "Crimen",
    99: "Documental", 18: "Drama", 10751: "Familia", 14: "Fantasía", 36: "Historia",
    27: "Terror", 10402: "Música", 9648: "Misterio", 10749: "Romance", 878: "Ciencia ficción",
    10770: "Película de TV", 53: "Suspense", 10752: "Bélica", 37: "Western"
}

class TmdbService:
    """Cliente HTTP para la API de The Movie Database (TMDB) con caché en Redis."""

    @staticmethod
    def _get_cache_key(prefix: str, identifier: Any) -> str:
        return f"tmdb_cache:{prefix}:{identifier}"

    @classmethod
    def get_movies(cls, page: int = 1, query: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de películas populares o realiza una búsqueda por título."""
        if not Config.TMDB_API_KEY:
            logger.warning("TMDB_API_KEY no configurada. Retornando datos simulados.")
            return cls._get_mock_movies(page)

        redis_client = get_redis_client()
        cache_key = cls._get_cache_key("search" if query else "popular", f"{query or 'all'}_p{page}")

        # Intentar leer de caché
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Error al leer de caché en Redis: {str(e)}")

        endpoint = f"{Config.TMDB_BASE_URL}/search/movie" if query else f"{Config.TMDB_BASE_URL}/movie/popular"
        params = {
            "api_key": Config.TMDB_API_KEY,
            "language": "es-ES",
            "page": page
        }
        if query:
            params["query"] = query

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(endpoint, params=params)
                if res.status_code != 200:
                    logger.error(f"Error desde TMDB API ({res.status_code}): {res.text}")
                    raise AppException("Error al consultar el catálogo de TMDB", 502)

                data = res.json()
                results = []
                for item in data.get("results", []):
                    # Mapear IDs de género a nombres legibles
                    genre_ids = item.get("genre_ids", [])
                    genres = [GENRE_MAP.get(gid, "Otro") for gid in genre_ids if gid in GENRE_MAP]

                    results.append({
                        "tmdb_id": item.get("id"),
                        "title": item.get("title", ""),
                        "overview": item.get("overview", ""),
                        "poster_path": f"{Config.TMDB_IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None,
                        "release_date": item.get("release_date", ""),
                        "genres": genres,
                        "vote_average": round(float(item.get("vote_average", 0.0)), 1)
                    })

                response_payload = {
                    "page": data.get("page", 1),
                    "total_pages": min(data.get("total_pages", 1), 500),
                    "total_results": data.get("total_results", 0),
                    "results": results
                }

                # Guardar en caché por 10 minutos (600 segundos)
                if redis_client:
                    try:
                        redis_client.setex(cache_key, 600, json.dumps(response_payload))
                    except Exception as e:
                        logger.warning(f"Error al guardar en caché: {str(e)}")

                return response_payload
        except httpx.RequestError as e:
            logger.error(f"Error de red contactando a TMDB: {str(e)}")
            raise AppException("No se pudo conectar con el servicio de películas", 503)

    @classmethod
    def get_movie_details(cls, tmdb_id: int) -> Dict[str, Any]:
        """Obtiene la información detallada de una película por su ID de TMDB."""
        if not Config.TMDB_API_KEY:
            return {
                "tmdb_id": tmdb_id,
                "title": f"Película #{tmdb_id}",
                "overview": "Sinopsis de prueba",
                "poster_path": None,
                "release_date": "2024-01-01",
                "genres": ["Drama"],
                "vote_average": 7.5
            }

        redis_client = get_redis_client()
        cache_key = cls._get_cache_key("detail", tmdb_id)

        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        endpoint = f"{Config.TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {"api_key": Config.TMDB_API_KEY, "language": "es-ES"}

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(endpoint, params=params)
                if res.status_code == 404:
                    raise AppException("Película no encontrada en TMDB", 404)
                if res.status_code != 200:
                    raise AppException("Error al obtener detalle de la película", 502)

                item = res.json()
                genres = [g.get("name") for g in item.get("genres", []) if g.get("name")]

                details = {
                    "tmdb_id": item.get("id"),
                    "title": item.get("title", ""),
                    "overview": item.get("overview", ""),
                    "poster_path": f"{Config.TMDB_IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None,
                    "release_date": item.get("release_date", ""),
                    "genres": genres,
                    "vote_average": round(float(item.get("vote_average", 0.0)), 1)
                }

                if redis_client:
                    try:
                        redis_client.setex(cache_key, 3600, json.dumps(details)) # 1 hora de caché
                    except Exception:
                        pass

                return details
        except httpx.RequestError as e:
            logger.error(f"Error al consultar detalle en TMDB: {str(e)}")
            raise AppException("Error de conexión con TMDB", 503)

    @classmethod
    def find_movie_by_title_and_year(cls, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Busca una película por título para enriquecer la recomendación generada por el LLM."""
        if not Config.TMDB_API_KEY:
            return None

        endpoint = f"{Config.TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": Config.TMDB_API_KEY,
            "language": "es-ES",
            "query": title
        }
        if year:
            params["year"] = year

        try:
            with httpx.Client(timeout=6.0) as client:
                res = client.get(endpoint, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        first = results[0]
                        genre_ids = first.get("genre_ids", [])
                        genres = [GENRE_MAP.get(gid, "Otro") for gid in genre_ids if gid in GENRE_MAP]
                        return {
                            "tmdb_id": first.get("id"),
                            "title": first.get("title"),
                            "overview": first.get("overview"),
                            "poster_path": f"{Config.TMDB_IMAGE_BASE_URL}{first.get('poster_path')}" if first.get("poster_path") else None,
                            "release_date": first.get("release_date"),
                            "genres": genres,
                            "vote_average": round(float(first.get("vote_average", 0.0)), 1)
                        }
        except Exception as e:
            logger.warning(f"No se pudo enriquecer película '{title}' con TMDB: {str(e)}")
        return None

    @staticmethod
    def _get_mock_movies(page: int) -> Dict[str, Any]:
        """Datos de muestra si la API key de TMDB aún no fue provista."""
        return {
            "page": page,
            "total_pages": 1,
            "total_results": 4,
            "results": [
                {
                    "tmdb_id": 27205,
                    "title": "Inception",
                    "overview": "Un ladrón que roba secretos corporativos a través de la tecnología de compartir sueños...",
                    "poster_path": "https://image.tmdb.org/t/p/w500/ljsZTbVsrQSqZgWeep2P1P2Yum4.jpg",
                    "release_date": "2010-07-15",
                    "genres": ["Acción", "Ciencia ficción"],
                    "vote_average": 8.4
                },
                {
                    "tmdb_id": 157336,
                    "title": "Interstellar",
                    "overview": "Un equipo de exploradores viaja a través de un agujero de gusano en el espacio...",
                    "poster_path": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                    "release_date": "2014-11-05",
                    "genres": ["Aventura", "Drama", "Ciencia ficción"],
                    "vote_average": 8.4
                },
                {
                    "tmdb_id": 155,
                    "title": "The Dark Knight",
                    "overview": "Batman sube la apuesta en su guerra contra el crimen con la ayuda del teniente Jim Gordon...",
                    "poster_path": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                    "release_date": "2008-07-16",
                    "genres": ["Drama", "Acción", "Crimen"],
                    "vote_average": 8.5
                },
                {
                    "tmdb_id": 680,
                    "title": "Pulp Fiction",
                    "overview": "Las vidas de dos sicarios de la mafia, un boxeador y una pareja de bandidos se entrelazan...",
                    "poster_path": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
                    "release_date": "1994-09-10",
                    "genres": ["Suspense", "Crimen"],
                    "vote_average": 8.5
                }
            ]
        }
