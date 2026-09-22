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

        # 3. Obtener historial previo de recomendaciones del usuario para evitar duplicados
        previous_titles = []
        if supabase:
            try:
                prev_res = supabase.table("recommendations") \
                    .select("recommended_title") \
                    .eq("user_id", user_id) \
                    .neq("status", "FAILED") \
                    .execute()
                previous_titles = [r["recommended_title"] for r in (prev_res.data or []) if r.get("recommended_title")]
            except Exception as e:
                logger.warning(f"No se pudieron leer recomendaciones previas de Supabase ({str(e)}).")

        excluded_titles = list(set([m.get("title", "") for m in user_likes if m.get("title")] + previous_titles))
        normalized_excluded = {t.strip().lower() for t in excluded_titles if t}
        logger.info(f"Usuario {username} tiene {len(user_likes)} favoritos y {len(previous_titles)} recomendaciones previas ({len(normalized_excluded)} títulos excluidos).")

        # 4. Aplicar Rate Limiting para la llamada a Groq
        logger.info("Verificando cupo en el Rate Limiter de Groq...")
        acquired = rate_limiter.acquire(tokens_requested=1, timeout=60.0)
        if not acquired:
            raise TimeoutError("Se agotó el tiempo de espera por cuota de Rate Limiter.")

        # 5. Generar 10 recomendaciones candidatas con el LLM (Groq)
        groq_candidates = GroqService.generate_movie_recommendations(
            user_likes=user_likes,
            excluded_titles=excluded_titles,
            username=username
        )
        logger.info(f"Groq devolvió {len(groq_candidates)} películas candidatas.")

        # 6. Filtrar candidatos contra historial y seleccionar Top 3
        selected_candidates = []
        seen_in_batch = set()

        for item in groq_candidates:
            norm_title = item.title.strip().lower()
            if norm_title not in normalized_excluded and norm_title not in seen_in_batch:
                selected_candidates.append(item)
                seen_in_batch.add(norm_title)
            if len(selected_candidates) >= 3:
                break

        # Fallback si quedaron menos de 3 tras el filtro estricto
        if len(selected_candidates) < 3:
            for item in groq_candidates:
                norm_title = item.title.strip().lower()
                if norm_title not in seen_in_batch:
                    selected_candidates.append(item)
                    seen_in_batch.add(norm_title)
                if len(selected_candidates) >= 3:
                    break

        logger.info(f"Seleccionadas {len(selected_candidates)} recomendaciones finales para el usuario.")

        # 7. Enriquecer con TMDB todas las recomendaciones seleccionadas
        enriched_recommendations = []
        for rec_item in selected_candidates:
            tmdb_movie = TmdbService.find_movie_by_title_and_year(
                title=rec_item.title,
                year=rec_item.release_year
            )

            recommended_tmdb_id = None
            if tmdb_movie and tmdb_movie.get("tmdb_id"):
                recommended_tmdb_id = tmdb_movie["tmdb_id"]
                if supabase:
                    try:
                        supabase.table("movies").upsert({
                            "tmdb_id": recommended_tmdb_id,
                            "title": tmdb_movie.get("title", rec_item.title),
                            "overview": tmdb_movie.get("overview", ""),
                            "poster_path": tmdb_movie.get("poster_path"),
                            "release_date": tmdb_movie.get("release_date"),
                            "genres": tmdb_movie.get("genres", rec_item.genres),
                            "vote_average": tmdb_movie.get("vote_average", 0.0)
                        }).execute()
                    except Exception as e:
                        logger.warning(f"No se pudo guardar la película en tabla movies: {str(e)}")

            enriched_recommendations.append({
                "item": rec_item,
                "tmdb_id": recommended_tmdb_id
            })

        # 8. Persistir en Supabase (primero las complementarias, y al final el registro principal como COMPLETED)
        completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if supabase and enriched_recommendations:
            # Insertar registros secundarios primero (idx > 0)
            for idx in range(1, len(enriched_recommendations)):
                child_rec = enriched_recommendations[idx]
                child_job_id = f"{job_id}_{idx+1}"
                try:
                    supabase.table("recommendations").insert({
                        "user_id": user_id,
                        "job_id": child_job_id,
                        "status": "COMPLETED",
                        "recommended_title": child_rec["item"].title,
                        "recommended_tmdb_id": child_rec["tmdb_id"],
                        "rationale": child_rec["item"].rationale,
                        "completed_at": completed_at
                    }).execute()
                except Exception as ins_err:
                    logger.warning(f"No se pudo insertar recomendación secundaria {child_job_id}: {str(ins_err)}")

            # Finalmente actualizar el registro principal a COMPLETED una vez que todas las demás ya existen
            main_rec = enriched_recommendations[0]
            supabase.table("recommendations").update({
                "status": "COMPLETED",
                "recommended_title": main_rec["item"].title,
                "recommended_tmdb_id": main_rec["tmdb_id"],
                "rationale": main_rec["item"].rationale,
                "completed_at": completed_at
            }).eq("job_id", job_id).execute()

        logger.info(f"✔ Trabajo {job_id} procesado exitosamente con {len(selected_candidates)} recomendaciones persistidas.")

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
