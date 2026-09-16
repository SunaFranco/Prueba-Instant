import datetime
from functools import wraps
from typing import Dict, Any, Optional
import bcrypt
import jwt
from flask import request, jsonify, g
from app.config import Config

def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña usando bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash almacenado."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def generate_jwt(user_id: str, username: str) -> str:
    """Emite un token JWT firmado con fecha de expiración."""
    payload = {
        "sub": user_id,
        "username": username,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def jwt_required(f):
    """Decorador para proteger rutas requiriendo un Bearer token válido."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "No autorizado", "message": "Token de autenticación faltante o inválido"}), 401
        
        token = auth_header.split(" ")[1].strip()
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "No autorizado", "message": "El token ha expirado o no es válido"}), 401
        
        # Almacenar datos del usuario autenticado en el contexto de la solicitud (Flask g)
        g.user_id = payload.get("sub")
        g.username = payload.get("username")
        return f(*args, **kwargs)
    return decorated_function
