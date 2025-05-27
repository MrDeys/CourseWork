from flask import Flask, jsonify
from flask_cors import CORS
from .api.routes import bp
from .match_data_manager import data_manager
from flask.json.provider import DefaultJSONProvider as JSONProvider

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(bp, url_prefix='/api/matches')

    with app.app_context():
        leagues_dir = 'leagues/'
        predicts_dir = 'predictions/'

        data_manager.load_data(leagues_dir, predicts_dir)

    return app