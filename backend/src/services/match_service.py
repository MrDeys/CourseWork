import soccerdata as sd
import datetime
import os
import numpy as np
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from ..database.tables import SessionLocal, Match, League, Team, Prediction
from .net_service import InferenceService

class MatchService:
    def __init__(self):
        self.inference = InferenceService()

    @staticmethod
    def _safe_float(val, default=0.0):
        if val is None: return float(default)
        try: return float(val)
        except: return float(default)

    @staticmethod
    def _safe_int(val, default=0):
        if val is None: return int(default)
        try: return int(val)
        except: return int(default)

    def get_stats_for_single_team(self, session, team_id, date):
        past = session.query(Match).filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == 'FINISHED', Match.date < date
        ).order_by(Match.date.desc()).limit(5).all()

        empty = {"xg_for":0.0, "xg_against":0.0, "ppda":0.0, "deep":0.0, "gf":0.0, "ga":0.0, "form":[]}
        if not past: return {"stats": empty, "history": []}

        s = {"xg_for":[], "xg_against":[], "ppda":[], "deep":[], "gf":[], "ga":[]}
        form, history = [], []

        for m in past:
            is_h = m.home_team_id == team_id
            gf = self._safe_int(m.home_goals if is_h else m.away_goals, 0)
            ga = self._safe_int(m.away_goals if is_h else m.home_goals, 0)
            
            s["xg_for"].append(self._safe_float(m.home_xg if is_h else m.away_xg, 1.0))
            s["xg_against"].append(self._safe_float(m.away_xg if is_h else m.home_xg, 1.0))
            s["ppda"].append(self._safe_float(m.home_ppda if is_h else m.away_ppda, 10.0))
            s["deep"].append(self._safe_int(m.home_deep if is_h else m.away_deep, 5))
            s["gf"].append(gf)
            s["ga"].append(ga)

            res = "D"
            if gf > ga: res = "W"
            elif ga > gf: res = "L"
            form.append(res)

            opp = m.away_team if is_h else m.home_team
            history.append({
                "opponent": getattr(opp, 'name_ru', opp.name),
                "opponent_logo": opp.logo_url,
                "score": f"{m.home_goals}:{m.away_goals}",
                "res": res, "is_home": is_h
            })

        avg_stats = {k: float(np.mean(v)) for k, v in s.items()}
        avg_stats["form"] = form
        return {"stats": avg_stats, "history": history}

    def _format_match(self, session, match, detailed=False):
        pred = match.predictions[-1] if match.predictions else None
        
        status = "FINISHED" if match.home_goals is not None else match.status

        data = {
            "id": match.id,
            "utcDate": match.date.isoformat() + "Z",
            "league": match.league.name,
            "status": status,
            "homeTeam": {
                "id": match.home_team_id, 
                "name": match.home_team.name, 
                "name_ru": getattr(match.home_team, 'name_ru', match.home_team.name), 
                "logo_url": match.home_team.logo_url, 
                "elo": self._safe_float(match.home_elo, 1500.0)
            },
            "awayTeam": {
                "id": match.away_team_id,
                "name": match.away_team.name, 
                "name_ru": getattr(match.away_team, 'name_ru', match.away_team.name), 
                "logo_url": match.away_team.logo_url, 
                "elo": self._safe_float(match.away_elo, 1500.0)
            },
            "score": {"home": match.home_goals, "away": match.away_goals},
            "prediction": None
        }

        if pred:
            data["prediction"] = {
                "prob_home": round(self._safe_float(pred.prob_h)*100, 1),
                "prob_draw": round(self._safe_float(pred.prob_d)*100, 1),
                "prob_away": round(self._safe_float(pred.prob_a)*100, 1),
                "outcome": pred.predicted_outcome,
                "exact_score": pred.predicted_exact_score,
                "total_over_2_5": round(self._safe_float(pred.total_over_2_5_probability)*100, 1)
            }

        if detailed:
            h_d = self.get_stats_for_single_team(session, match.home_team_id, match.date)
            a_d = self.get_stats_for_single_team(session, match.away_team_id, match.date)
            data["homeTeam"].update({"stats_last_5": h_d["stats"], "history": h_d["history"]})
            data["awayTeam"].update({"stats_last_5": a_d["stats"], "history": a_d["history"]})
            
            h2h_raw = session.query(Match).filter(
                or_(
                    and_(Match.home_team_id == match.home_team_id, Match.away_team_id == match.away_team_id),
                    and_(Match.home_team_id == match.away_team_id, Match.away_team_id == match.home_team_id)
                ), 
                Match.status == 'FINISHED', 
                Match.date < match.date
            ).order_by(Match.date.desc()).limit(5).all()

            data["h2h"] = [{
                "date": m.date.strftime('%d.%m.%y'),
                "home": m.home_team.name_ru or m.home_team.name,
                "home_logo": m.home_team.logo_url,
                "home_id": m.home_team_id,
                "away": m.away_team.name_ru or m.away_team.name,
                "away_logo": m.away_team.logo_url,
                "away_id": m.away_team_id,
                "score": f"{m.home_goals}:{m.away_goals}"
            } for m in h2h_raw]

        return data

    def get_upcoming_matches(self, league_name=None) -> list:
        session = SessionLocal()
        try:
            start_date = datetime.datetime.utcnow() - datetime.timedelta(days=10)
            query = session.query(Match).options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.league), joinedload(Match.predictions)).filter(Match.date >= start_date)
            if league_name: query = query.join(League).filter(League.name.like(f"%{league_name}%"))
            matches = query.order_by(Match.date.asc()).all()
            return [self._format_match(session, m, detailed=False) for m in matches]
        finally: session.close()

    def get_match_id(self, match_id: int) -> dict | None:
        session = SessionLocal()
        try:
            match = session.query(Match).options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.league), joinedload(Match.predictions)).filter(Match.id == match_id).first()
            return self._format_match(session, match, detailed=True) if match else None
        finally: session.close()

    def get_team_comparison(self, t1_n, t2_n):
        session = SessionLocal()
        try:
            t1 = session.query(Team).filter(or_(Team.name == t1_n, Team.name_ru == t1_n)).first()
            t2 = session.query(Team).filter(or_(Team.name == t2_n, Team.name_ru == t2_n)).first()
            if not t1 or not t2: return None
            now = datetime.datetime.utcnow()
            h_d, a_d = self.get_stats_for_single_team(session, t1.id, now), self.get_stats_for_single_team(session, t2.id, now)
            t1_l = session.query(Match).filter(or_(Match.home_team_id == t1.id, Match.away_team_id == t1.id), Match.status == 'FINISHED').order_by(Match.date.desc()).first()
            t2_l = session.query(Match).filter(or_(Match.home_team_id == t2.id, Match.away_team_id == t2.id), Match.status == 'FINISHED').order_by(Match.date.desc()).first()
            t1_e = self._safe_float(getattr(t1_l, 'home_elo' if t1_l and t1_l.home_team_id == t1.id else 'away_elo', 1500), 1500)
            t2_e = self._safe_float(getattr(t2_l, 'home_elo' if t2_l and t2_l.home_team_id == t2.id else 'away_elo', 1500), 1500)
            
            h2h = session.query(Match).filter(
                or_(
                    and_(Match.home_team_id == t1.id, Match.away_team_id == t2.id), 
                    and_(Match.home_team_id == t2.id, Match.away_team_id == t1.id)
                ), 
                Match.status == 'FINISHED', 
                Match.date < now
            ).order_by(Match.date.desc()).limit(5).all()
            
            return {
                "team1": {
                    "id": t1.id,
                    "name": t1.name_ru or t1.name, 
                    "logo_url": t1.logo_url, 
                    "elo": t1_e, 
                    "stats": h_d["stats"], 
                    "history": h_d["history"]
                },
                "team2": {
                    "id": t2.id,
                    "name": t2.name_ru or t2.name, 
                    "logo_url": t2.logo_url, 
                    "elo": t2_e, 
                    "stats": a_d["stats"], 
                    "history": a_d["history"]
                },
                "h2h": [{
                    "date": m.date.strftime('%d.%m.%y'), 
                    "home": m.home_team.name_ru or m.home_team.name, 
                    "home_logo": m.home_team.logo_url,
                    "home_id": m.home_team_id,
                    "away": m.away_team.name_ru or m.away_team.name, 
                    "away_logo": m.away_team.logo_url,
                    "away_id": m.away_team_id,
                    "score": f"{m.home_goals}:{m.away_goals}"
                } for m in h2h] ,
                "prediction": self.inference.predict(h_d["stats"], a_d["stats"], t1_e, t2_e)
            }
        finally: session.close()
