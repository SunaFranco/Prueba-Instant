import uuid
import datetime
import logging
from flask import Blueprint, jsonify, g
from app.db import get_supabase
from app.queue.producer import enqueue_recommendation_job
from app.utils.security import jwt_required
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint("recommendations", __name__)

@recommendations_bp.route("/request", methods=["POST"])
@jwt_required
def request_recommendation():
    user_id = g.user_id
    supabase = get_supabase()

    if not supabase:
        raise AppException("Servicio de base de datos no disponible", 503)

    # 1. Generar ID único para el trabajo
    job_id = f"rec_job_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 2. Persistir registro inicial en Supabase con estado PENDING
    try:
        supabase.table("recommendations").insert({
            "user_id": user_id,
            "job_id": job_id,
            "status": "PENDING"
        }).execute()
    except Exception as e:
        logger.error(f"Error registrando solicitud de recomendación en Supabase: {str(e)}")
        raise AppException("No se pudo iniciar la solicitud de recomendación", 500)

    # 3. Encolar la tarea en Redis
    payload = {
        "job_id": job_id,
        "user_id": user_id,
        "username": g.username,
        "created_at": now_iso
    }
    
    enqueued = enqueue_recommendation_job(payload)
    if not enqueued:
        logger.warning("Redis no disponible para encolar. Procesando recomendación en segundo plano (fallback)...")
        import threading
        from app.queue.rate_limiter import TokenBucketRateLimiter
        try:
            from worker import process_recommendation_job
            limiter = TokenBucketRateLimiter(redis_client=None, rate_per_minute=20)
            t = threading.Thread(target=process_recommendation_job, args=(payload, limiter), daemon=True)
            t.start()
        except Exception as e:
            logger.error(f"Error al iniciar hilo de procesamiento fallback: {str(e)}")

    return jsonify({
        "message": "Solicitud de recomendación encolada exitosamente",
        "job_id": job_id,
        "status": "PENDING"
    }), 202

@recommendations_bp.route("/status/<string:job_id>", methods=["GET"])
@jwt_required
def get_recommendation_status(job_id: str):
    user_id = g.user_id
    supabase = get_supabase()

    if not supabase:
        raise AppException("Servicio de base de datos no disponible", 503)

    try:
        res = supabase.table("recommendations") \
            .select("id, job_id, status, recommended_title, recommended_tmdb_id, rationale, error_message, created_at, completed_at, movies(poster_path, overview, vote_average, release_date, genres)") \
            .eq("job_id", job_id) \
            .eq("user_id", user_id) \
            .execute()

        if not res.data or len(res.data) == 0:
            raise AppException("Trabajo de recomendación no encontrado", 404)

        row = res.data[0]
        status = row.get("status", "PENDING")

        response = {
            "job_id": row["job_id"],
            "status": status,
            "error_message": row.get("error_message")
        }

        if status == "COMPLETED":
            movie_meta = row.get("movies") or {}
            response["recommendation"] = {
                "id": row["id"],
                "recommended_title": row["recommended_title"],
                "recommended_tmdb_id": row.get("recommended_tmdb_id"),
                "rationale": row.get("rationale"),
                "poster_path": movie_meta.get("poster_path"),
                "overview": movie_meta.get("overview"),
                "vote_average": movie_meta.get("vote_average"),
                "release_date": movie_meta.get("release_date"),
                "genres": movie_meta.get("genres"),
                "completed_at": row.get("completed_at")
            }

        return jsonify(response), 200
    except AppException:
        raise
    except Exception as e:
        logger.error(f"Error consultando estado de recomendación: {str(e)}")
        raise AppException("Error al consultar el estado de la recomendación", 500)

@recommendations_bp.route("", methods=["GET"])
@jwt_required
def list_recommendations():
    user_id = g.user_id
    supabase = get_supabase()

    if not supabase:
        raise AppException("Servicio de base de datos no disponible", 503)

    try:
        res = supabase.table("recommendations") \
            .select("id, job_id, status, recommended_title, recommended_tmdb_id, rationale, created_at, completed_at, movies(poster_path, overview, vote_average, release_date, genres)") \
            .eq("user_id", user_id) \
            .eq("status", "COMPLETED") \
            .order("created_at", desc=True) \
            .execute()

        recs = []
        for row in (res.data or []):
            movie_meta = row.get("movies") or {}
            recs.append({
                "id": row["id"],
                "job_id": row["job_id"],
                "recommended_title": row["recommended_title"],
                "recommended_tmdb_id": row.get("recommended_tmdb_id"),
                "rationale": row.get("rationale"),
                "poster_path": movie_meta.get("poster_path"),
                "overview": movie_meta.get("overview"),
                "vote_average": movie_meta.get("vote_average"),
                "release_date": movie_meta.get("release_date"),
                "genres": movie_meta.get("genres") or [],
                "created_at": row["created_at"],
                "completed_at": row.get("completed_at")
            })

        return jsonify({"recommendations": recs}), 200
    except AppException:
        raise
    except Exception as e:
        logger.error(f"Error listando recomendaciones: {str(e)}")
        raise AppException("Error al obtener historial de recomendaciones", 500)
