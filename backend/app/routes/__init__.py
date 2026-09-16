from app.routes.auth import auth_bp
from app.routes.movies import movies_bp
from app.routes.likes import likes_bp
from app.routes.recommendations import recommendations_bp
from app.routes.health import health_bp

__all__ = ["auth_bp", "movies_bp", "likes_bp", "recommendations_bp", "health_bp"]
