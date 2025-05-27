from flask import Blueprint, jsonify, request
from ..services.match_service import MatchService

bp = Blueprint('matches_api', __name__)

match_service = MatchService()

@bp.route('/', methods=['GET'])
def get_matches_route():
    league_code = request.args.get('league')

    if league_code:
        matches = match_service.get_matches_league(league_code.upper())
    else:
        matches = match_service.get_all_matches()

    return jsonify(matches)

@bp.route('/<int:match_id>', methods=['GET'])
def get_match_by_id_route(match_id: int):
    match = match_service.get_match_id(match_id)

    if match:
        return jsonify(match)
    else:
        return jsonify({"error": "Match not found"}), 404