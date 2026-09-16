import logging
from typing import Dict, Any, Optional
from app.db import get_supabase
from app.utils.security import hash_password, verify_password, generate_jwt
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio de negocio para registro y autenticación de usuarios en Supabase."""

    @staticmethod
    def register_user(username: str, password: str) -> Dict[str, Any]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        # 1. Verificar si el usuario ya existe
        try:
            existing = supabase.table("users").select("id").eq("username", username).execute()
            if existing.data and len(existing.data) > 0:
                raise AppException("El nombre de usuario ya está en uso", 409)
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error consultando existencia de usuario: {str(e)}")
            raise AppException("Error al procesar el registro", 500)

        # 2. Hashear la contraseña
        pwd_hash = hash_password(password)

        # 3. Insertar nuevo usuario
        try:
            insert_result = supabase.table("users").insert({
                "username": username,
                "password_hash": pwd_hash
            }).execute()

            if not insert_result.data or len(insert_result.data) == 0:
                raise AppException("No se pudo registrar el usuario", 500)

            user = insert_result.data[0]
            token = generate_jwt(user["id"], user["username"])

            return {
                "message": "Usuario registrado exitosamente",
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"]
                }
            }
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error insertando usuario en Supabase: {str(e)}")
            raise AppException(f"Error al guardar el usuario: {str(e)}", 500)

    @staticmethod
    def login_user(username: str, password: str) -> Dict[str, Any]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        try:
            res = supabase.table("users").select("id, username, password_hash").eq("username", username).execute()
            if not res.data or len(res.data) == 0:
                raise AppException("Credenciales inválidas", 401)

            user = res.data[0]
            if not verify_password(password, user["password_hash"]):
                raise AppException("Credenciales inválidas", 401)

            token = generate_jwt(user["id"], user["username"])
            return {
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"]
                }
            }
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error en login de usuario: {str(e)}")
            raise AppException("Error al iniciar sesión", 500)

    @staticmethod
    def get_user_profile(user_id: str) -> Dict[str, Any]:
        supabase = get_supabase()
        if not supabase:
            raise AppException("Servicio de base de datos no disponible", 503)

        try:
            res = supabase.table("users").select("id, username, created_at").eq("id", user_id).execute()
            if not res.data or len(res.data) == 0:
                raise AppException("Usuario no encontrado", 404)
            return res.data[0]
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}")
            raise AppException("Error al consultar el perfil", 500)
