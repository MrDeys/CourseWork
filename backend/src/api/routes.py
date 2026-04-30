# backend/src/api/routes.py
from flask import Blueprint, jsonify, request
from ..services.match_service import MatchService

bp = Blueprint('matches_api', __name__)
match_service = MatchService()

@bp.route('/', methods=['GET'])
def get_matches_route():
    league = request.args.get('league') # Например: ?league=Premier_League
    
    # Теперь мы отдаем только будущие матчи, чтобы не перегружать браузер 20к матчами
    matches = match_service.get_upcoming_matches(league_name=league)
    return jsonify(matches)

@bp.route('/<int:match_id>', methods=['GET'])
def get_match_by_id_route(match_id: int):
    match = match_service.get_match_id(match_id)

    if match:
        return jsonify(match)
    else:
        return jsonify({"error": "Match not found"}), 404