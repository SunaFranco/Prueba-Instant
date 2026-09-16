from flask import Blueprint, request, jsonify
from app.services.tmdb_service import TmdbService

movies_bp = Blueprint("movies", __name__)

@movies_bp.route("", methods=["GET"])
def get_movies():
    page = request.args.get("page", default=1, type=int)
    query = request.args.get("query", default=None, type=str)
    
    response = TmdbService.get_movies(page=page, query=query)
    return jsonify(response), 200

@movies_bp.route("/<int:tmdb_id>", methods=["GET"])
def get_movie_detail(tmdb_id: int):
    detail = TmdbService.get_movie_details(tmdb_id)
    return jsonify(detail), 200
