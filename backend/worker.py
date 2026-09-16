import json
import logging
import time
import datetime
from app.config import Config
from app.db import init_supabase, get_supabase
from app.queue.producer import get_redis_client
from app.queue.rate_limiter import TokenBucketRateLimiter
from app.services.likes_service import LikesService
from app.services.groq_service import GroqService
from app.services.tmdb_service import TmdbService

# Configuración de logs para el worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER-%(levelname)s]: %(message)s"
)
logger = logging.getLogger("worker")

def process_recommendation_job(job_data: dict, rate_limiter: TokenBucketRateLimiter):
    """Procesa un único trabajo de recomendación con control de tasa y persistencia."""
    job_id = job_data.get("job_id")
    user_id = job_data.get("user_id")
    username = job_data.get("username", "Usuario")

    logger.info(f"==> Iniciando procesamiento de trabajo {job_id} para usuario {username} ({user_id})")
    supabase = get_supabase()

    # 1. Actualizar estado a PROCESSING
    if supabase:
        try:
            supabase.table("recommendations").update({
                "status": "PROCESSING"
            }).eq("job_id", job_id).execute()
        except Exception as e:
            logger.error(f"No se pudo actualizar estado a PROCESSING: {str(e)}")

    try:
        # 2. Obtener lista de películas favoritas del usuario
        user_likes = []
        if supabase:
            try:
                user_likes = LikesService.get_user_likes(user_id)
            except Exception as e:
                logger.warning(f"No se pudieron leer likes de Supabase ({str(e)}). Continuando...")

        logger.info(f"Usuario {username} tiene {len(user_likes)} películas en favoritos.")

        # 3. Aplicar Rate Limiting para la llamada a Groq
        logger.info("Verificando cupo en el Rate Limiter de Groq...")
        acquired = rate_limiter.acquire(tokens_requested=1, timeout=60.0)
        if not acquired:
            raise TimeoutError("Se agotó el tiempo de espera por cuota de Rate Limiter.")

        # 4. Generar recomendación con el LLM (Groq)
        rec_output = GroqService.generate_movie_recommendation(
            user_likes=user_likes,
            username=username
        )
        logger.info(f"Groq recomendó: '{rec_output.title}' ({rec_output.release_year})")

        # 5. Enriquecer con metadatos y póster de TMDB
        tmdb_movie = TmdbService.find_movie_by_title_and_year(
            title=rec_output.title,
            year=rec_output.release_year
        )

        recommended_tmdb_id = None
        if tmdb_movie and tmdb_movie.get("tmdb_id"):
            recommended_tmdb_id = tmdb_movie["tmdb_id"]
            # Guardar película recomendada en tabla movies
            if supabase:
                try:
                    supabase.table("movies").upsert({
                        "tmdb_id": recommended_tmdb_id,
                        "title": tmdb_movie.get("title", rec_output.title),
                        "overview": tmdb_movie.get("overview", ""),
                        "poster_path": tmdb_movie.get("poster_path"),
                        "release_date": tmdb_movie.get("release_date"),
                        "genres": tmdb_movie.get("genres", rec_output.genres),
                        "vote_average": tmdb_movie.get("vote_average", 0.0)
                    }).execute()
                except Exception as e:
                    logger.warning(f"No se pudo guardar la película en la tabla movies: {str(e)}")

        # 6. Actualizar recomendación a COMPLETED en Supabase
        completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if supabase:
            supabase.table("recommendations").update({
                "status": "COMPLETED",
                "recommended_title": rec_output.title,
                "recommended_tmdb_id": recommended_tmdb_id,
                "rationale": rec_output.rationale,
                "completed_at": completed_at
            }).eq("job_id", job_id).execute()

        logger.info(f"✔ Trabajo {job_id} completado y persistido exitosamente.")

    except Exception as e:
        logger.error(f"✘ Fallo al procesar trabajo {job_id}: {str(e)}")
        if supabase:
            try:
                supabase.table("recommendations").update({
                    "status": "FAILED",
                    "error_message": str(e)
                }).eq("job_id", job_id).execute()
            except Exception as upd_err:
                logger.error(f"No se pudo marcar trabajo como FAILED: {str(upd_err)}")

def run_worker():
    """Bucle principal del proceso worker."""
    logger.info("Iniciando Worker de Recomendaciones...")
    init_supabase()
    redis_client = get_redis_client()

    rate_limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        key_prefix="rate_limit:groq",
        rate_per_minute=Config.GROQ_MAX_REQUESTS_PER_MINUTE
    )

    queue_name = Config.RECOMMENDATION_QUEUE_NAME
    logger.info(f"Escuchando tareas en cola de Redis '{queue_name}' (Rate Limit: {Config.GROQ_MAX_REQUESTS_PER_MINUTE} RPM)...")

    while True:
        try:
            if redis_client:
                # Lectura bloqueante de la cola con timeout de 2 segundos
                item = redis_client.blpop(queue_name, timeout=2)
                if item:
                    _, raw_data = item
                    job_data = json.loads(raw_data)
                    process_recommendation_job(job_data, rate_limiter)
                else:
                    # Timeout sin mensajes en la cola
                    time.sleep(0.5)
            else:
                # Si Redis no está disponible, reintentar conexión periódicamente
                time.sleep(3)
                redis_client = get_redis_client()
                rate_limiter.redis = redis_client

        except KeyboardInterrupt:
            logger.info("Worker detenido por el usuario.")
            break
        except Exception as e:
            logger.error(f"Error inesperado en bucle del worker: {str(e)}")
            time.sleep(2)

if __name__ == "__main__":
    run_worker()
