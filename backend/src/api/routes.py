from flask import Blueprint, jsonify, request
from ..services.match_service import MatchService
from update import run_full_update 
import threading

bp = Blueprint('matches_api', __name__)
match_service = MatchService()

@bp.route('/', methods=['GET'])
def get_matches_route():
    league = request.args.get('league') 
    
    matches = match_service.get_upcoming_matches(league_name=league)
    return jsonify(matches)

@bp.route('/<int:match_id>', methods=['GET'])
def get_match_by_id_route(match_id: int):
    match = match_service.get_match_id(match_id)

    if match:
        return jsonify(match)
    else:
        return jsonify({"error": "Match not found"}), 404

@bp.route('/table/<string:league_name>', methods=['GET'])
def get_table(league_name):
    table = match_service.get_league_table(league_name)
    
    if table:
        return jsonify(table)
    else:
        return jsonify([]), 200
    
@bp.route('/compare', methods=['GET'])
def compare_teams():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    
    if not team1 or not team2:
        return jsonify({"error": "Укажите обе команды"}), 400
        
    data = match_service.get_team_comparison(team1, team2)
    if data:
        return jsonify(data)
    return jsonify({"error": "Команды не найдены"}), 404

@bp.route('/force-update-neural-data-777', methods=['GET'])
def force_update():
    threading.Thread(target=run_full_update).start()
    return "Процесс обновления запущен!", 200