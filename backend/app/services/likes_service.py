import logging
from typing import Dict, Any, List
from app.db import get_supabase
from app.services.tmdb_service import TmdbService
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

class LikesService:
    """Gestión de 'Me Gusta' (Favoritos) del usuario en Supabase."""

    @staticmethod
    def get_user_likes(user_id: str) -> List[Dict[str, Any]]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        try:
            # Consultar likes haciendo join con la tabla movies
            res = supabase.table("user_likes") \
                .select("id, created_at, tmdb_id, movies(tmdb_id, title, overview, poster_path, release_date, genres, vote_average)") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .execute()

            likes = []
            for row in (res.data or []):
                movie_data = row.get("movies") or {}
                likes.append({
                    "like_id": row["id"],
                    "tmdb_id": row["tmdb_id"],
                    "title": movie_data.get("title", f"Película #{row['tmdb_id']}"),
                    "overview": movie_data.get("overview", ""),
                    "poster_path": movie_data.get("poster_path"),
                    "release_date": movie_data.get("release_date"),
                    "genres": movie_data.get("genres") or [],
                    "vote_average": float(movie_data.get("vote_average", 0.0)) if movie_data.get("vote_average") is not None else 0.0,
                    "created_at": row["created_at"]
                })
            return likes
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error listando likes de usuario {user_id}: {str(e)}")
            raise AppException("Error al obtener lista de favoritos", 500)

    @staticmethod
    def add_like(user_id: str, tmdb_id: int, movie_data: Dict[str, Any] = None) -> Dict[str, Any]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        # 1. Asegurar que la película exista en la tabla movies (upsert)
        if not movie_data or not movie_data.get("title"):
            try:
                fetched = TmdbService.get_movie_details(tmdb_id)
                movie_data = fetched
            except Exception:
                movie_data = movie_data or {}

        try:
            supabase.table("movies").upsert({
                "tmdb_id": tmdb_id,
                "title": movie_data.get("title", f"Película #{tmdb_id}"),
                "overview": movie_data.get("overview", ""),
                "poster_path": movie_data.get("poster_path"),
                "release_date": movie_data.get("release_date"),
                "genres": movie_data.get("genres") or [],
                "vote_average": movie_data.get("vote_average", 0.0)
            }).execute()
        except Exception as e:
            logger.warning(f"No se pudo hacer upsert de la película en movies: {str(e)}")

        # 2. Insertar el like del usuario
        try:
            existing = supabase.table("user_likes").select("id").eq("user_id", user_id).eq("tmdb_id", tmdb_id).execute()
            if existing.data and len(existing.data) > 0:
                return {"message": "La película ya está en favoritos", "tmdb_id": tmdb_id}

            insert_res = supabase.table("user_likes").insert({
                "user_id": user_id,
                "tmdb_id": tmdb_id
            }).execute()

            return {
                "message": "Película agregada a favoritos exitosamente",
                "tmdb_id": tmdb_id,
                "like_id": insert_res.data[0]["id"] if insert_res.data else None
            }
        except Exception as e:
            logger.error(f"Error agregando like: {str(e)}")
            raise AppException("Error al agregar la película a favoritos", 500)

    @staticmethod
    def remove_like(user_id: str, tmdb_id: int) -> Dict[str, Any]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        try:
            supabase.table("user_likes").delete().eq("user_id", user_id).eq("tmdb_id", tmdb_id).execute()
            return {"message": "Película eliminada de favoritos exitosamente", "tmdb_id": tmdb_id}
        except Exception as e:
            logger.error(f"Error eliminando like: {str(e)}")
            raise AppException("Error al eliminar la película de favoritos", 500)
