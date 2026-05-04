import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class League(Base):
    __tablename__ = 'leagues'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    country = Column(String)
    matches = relationship('Match', back_populates='league')

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True) 
    logo_url = Column(String, nullable=True)

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True)

    league_id = Column(Integer, ForeignKey('leagues.id'))
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))

    date = Column(DateTime)
    season = Column(String)
    status = Column(String)

    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)
    
    home_ppda = Column(Float, nullable=True)
    away_ppda = Column(Float, nullable=True)
    home_deep = Column(Integer, nullable=True)
    away_deep = Column(Integer, nullable=True)

    home_elo = Column(Float, nullable=True)
    away_elo = Column(Float, nullable=True)

    league = relationship('League', back_populates='matches')
    home_team = relationship('Team', foreign_keys=[home_team_id])
    away_team = relationship('Team', foreign_keys=[away_team_id])
    predictions = relationship('Prediction', back_populates='match')

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), unique=True)

    prob_h = Column(Float)
    prob_d = Column(Float)
    prob_a = Column(Float)
    predicted_outcome = Column(String)

    total_over_2_5_probability = Column(Float)
    predicted_exact_score = Column(String)

    model_version = Column(String, default='1.0')
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship('Match', back_populates='predictions')

def init_db():
    Base.metadata.create_all(bind = engine)
    print("Таблицы успешно созданы!")

if __name__ == "__main__":
    init_db()