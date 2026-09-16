from flask import Blueprint, request, jsonify, g
from app.services.likes_service import LikesService
from app.utils.security import jwt_required

likes_bp = Blueprint("likes", __name__)

@likes_bp.route("", methods=["GET"])
@jwt_required
def get_likes():
    likes = LikesService.get_user_likes(g.user_id)
    return jsonify({"likes": likes}), 200

@likes_bp.route("/<int:tmdb_id>", methods=["POST"])
@jwt_required
def add_like(tmdb_id: int):
    movie_data = request.get_json() or {}
    result = LikesService.add_like(g.user_id, tmdb_id, movie_data)
    return jsonify(result), 201

@likes_bp.route("/<int:tmdb_id>", methods=["DELETE"])
@jwt_required
def remove_like(tmdb_id: int):
    result = LikesService.remove_like(g.user_id, tmdb_id)
    return jsonify(result), 200
