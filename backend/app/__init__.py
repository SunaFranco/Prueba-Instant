import logging
from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.db import init_supabase
from app.utils.exceptions import register_error_handlers
from app.routes import auth_bp, movies_bp, likes_bp, recommendations_bp, health_bp

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config) -> Flask:
    """
    Patrón Application Factory:
    Crea, configura e inicializa la aplicación Flask con todas sus extensiones y rutas.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Habilitar CORS para permitir peticiones desde el frontend de Vite/React
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 2. Inicializar cliente de Supabase
    try:
        init_supabase()
    except Exception as e:
        logger.warning(f"Advertencia al iniciar Supabase: {str(e)}")

    # 3. Registrar manejadores de error globales
    register_error_handlers(app)

    # 4. Registrar Blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(movies_bp, url_prefix="/api/movies")
    app.register_blueprint(likes_bp, url_prefix="/api/likes")
    app.register_blueprint(recommendations_bp, url_prefix="/api/recommendations")

    logger.info("Aplicación Flask inicializada exitosamente.")
    return app
