import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

class Config:
    """Configuración centralizada y validada de la aplicación."""
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "5000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # TMDB API
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    TMDB_IMAGE_BASE_URL: str = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/w500")

    # Groq Cloud API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("GROQ_MAX_REQUESTS_PER_MINUTE", "20"))
    GROQ_RETRY_MAX_ATTEMPTS: int = int(os.getenv("GROQ_RETRY_MAX_ATTEMPTS", "5"))

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    RECOMMENDATION_QUEUE_NAME: str = os.getenv("RECOMMENDATION_QUEUE_NAME", "recommendation_jobs")

    @classmethod
    def validate(cls):
        """Verifica que las variables críticas estén presentes en producción."""
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.TMDB_API_KEY:
            missing.append("TMDB_API_KEY")
        if not cls.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        
        if missing and cls.FLASK_ENV == "production":
            raise ValueError(f"Faltan variables de entorno requeridas: {', '.join(missing)}")
