# backend/src/services/match_service.py
from sqlalchemy.orm import joinedload
# Убедись, что путь импорта правильный относительно твоего проекта
from src.database.tables import SessionLocal, Match, League

class MatchService:
    def _format_match(self, match):
        """Форматирует объект SQLAlchemy в красивый JSON для React-фронтенда"""
        # Если для матча есть прогноз (берем первый из списка связей)
        pred = match.predictions[0] if match.predictions else None
        
        # Базовая информация о матче
        data = {
            "id": match.id,
            "utcDate": match.date.isoformat() + "Z", # Формат времени, понятный JS
            "league": match.league.name if match.league else None,
            "homeTeam": {"name": match.home_team.name, "logo_url": match.home_team.logo_url},
            "awayTeam": {"name": match.away_team.name, "logo_url": match.away_team.logo_url},
            "status": match.status,
            "score": {
                "homeTeam": match.home_goals,
                "awayTeam": match.away_goals
            },
            "prediction": None
        }
        
        # Если прогноз сгенерирован, добавляем его в JSON
        if pred:
            data["prediction"] = {
                "prob_home": round(pred.prob_h * 100, 1) if pred.prob_h else None,
                "prob_draw": round(pred.prob_d * 100, 1) if pred.prob_d else None,
                "prob_away": round(pred.prob_a * 100, 1) if pred.prob_a else None,
                "outcome": pred.predicted_outcome,
                "exact_score": pred.predicted_exact_score,
                "total_over_2_5": round(pred.total_over_2_5_probability * 100, 1) if pred.total_over_2_5_probability else None,
                "model_version": pred.model_version
            }
            
        return data

    def get_upcoming_matches(self, league_name=None) -> list:
        """Получает будущие матчи с прогнозами"""
        session = SessionLocal()
        
        # joinedload позволяет за 1 запрос вытащить и матч, и команды, и прогнозы (быстро)
        query = session.query(Match).options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.league),
            joinedload(Match.predictions)
        ).filter(Match.status == 'SCHEDULED')
        
        if league_name:
            query = query.join(League).filter(League.name == league_name)
            
        query = query.order_by(Match.date.asc())
        matches = query.all()
        session.close()
        
        return [self._format_match(m) for m in matches]

    def get_match_id(self, match_id: int) -> dict | None:
        """Получает детальную информацию по одному матчу"""
        session = SessionLocal()
        match = session.query(Match).options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.league),
            joinedload(Match.predictions)
        ).filter(Match.id == match_id).first()
        session.close()
        
        if match:
            return self._format_match(match)
        return None