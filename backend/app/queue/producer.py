import json
import logging
from typing import Optional, Dict, Any
import redis
from app.config import Config

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Inicializa y retorna la conexión singleton a Redis."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2
            )
            _redis_client.ping()
            logger.info("Conexión a Redis establecida correctamente.")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis ({str(e)}). El encolamiento usará modo fallback o directo.")
            _redis_client = None
    return _redis_client

def enqueue_recommendation_job(payload: Dict[str, Any]) -> bool:
    """Inserta una tarea de recomendación en la lista/cola de Redis."""
    client = get_redis_client()
    if client is None:
        logger.error("Redis no está disponible para encolar el trabajo.")
        return False
    try:
        serialized = json.dumps(payload)
        client.rpush(Config.RECOMMENDATION_QUEUE_NAME, serialized)
        logger.info(f"Trabajo encolado en '{Config.RECOMMENDATION_QUEUE_NAME}': {payload.get('job_id')}")
        return True
    except Exception as e:
        logger.error(f"Error al encolar trabajo en Redis: {str(e)}")
        return False
