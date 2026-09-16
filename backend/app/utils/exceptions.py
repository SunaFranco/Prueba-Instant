from flask import jsonify
from pydantic import ValidationError

class AppException(Exception):
    """Excepción base para errores de la aplicación con código HTTP configurable."""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

def register_error_handlers(app):
    """Registra manejadores de error globales para respuestas JSON consistentes."""
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        response = {"error": e.message}
        if e.details:
            response["details"] = e.details
        return jsonify(response), e.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({
            "error": "Error de validación en la solicitud",
            "details": e.errors()
        }), 422

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500
