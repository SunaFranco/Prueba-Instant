import logging
from typing import Optional
from supabase import create_client, Client
from app.config import Config

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def init_supabase() -> Client:
    """Inicializa y retorna la instancia del cliente de Supabase."""
    global _supabase_client
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        logger.warning("SUPABASE_URL o SUPABASE_KEY no están configuradas. El cliente funcionará en modo degradado.")
        return None
    try:
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        logger.info("Cliente de Supabase inicializado correctamente.")
        return _supabase_client
    except Exception as e:
        logger.error(f"Error al inicializar cliente de Supabase: {str(e)}")
        raise e

def get_supabase() -> Client:
    """Retorna el cliente singleton de Supabase."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = init_supabase()
    return _supabase_client
