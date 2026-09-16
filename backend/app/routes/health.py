from flask import Blueprint, jsonify
from app.config import Config
from app.queue.producer import get_redis_client
from app.db import get_supabase

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint de estado para Docker healthcheck y monitoreo."""
    redis_ok = False
    supabase_ok = False

    # Chequear Redis
    try:
        client = get_redis_client()
        if client and client.ping():
            redis_ok = True
    except Exception:
        redis_ok = False

    # Chequear Supabase
    try:
        supabase = get_supabase()
        if supabase:
            supabase_ok = True
    except Exception:
        supabase_ok = False

    return jsonify({
        "status": "healthy",
        "environment": Config.FLASK_ENV,
        "services": {
            "redis": "connected" if redis_ok else "disconnected",
            "supabase": "configured" if supabase_ok else "unconfigured",
            "tmdb": "configured" if bool(Config.TMDB_API_KEY) else "mock_mode",
            "groq": "configured" if bool(Config.GROQ_API_KEY) else "mock_mode"
        }
    }), 200
