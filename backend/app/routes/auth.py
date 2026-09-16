from flask import Blueprint, request, jsonify, g
from app.schemas.dtos import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService
from app.utils.security import jwt_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    validated = RegisterRequest(**data)
    result = AuthService.register_user(validated.username, validated.password)
    return jsonify(result), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    validated = LoginRequest(**data)
    result = AuthService.login_user(validated.username, validated.password)
    return jsonify(result), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required
def me():
    profile = AuthService.get_user_profile(g.user_id)
    return jsonify(profile), 200
