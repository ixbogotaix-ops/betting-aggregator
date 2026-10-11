from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import Base

class SourceType(str, enum.Enum):
    prediction_site = "prediction_site"
    github_script = "github_script"
    hf_model = "hf_model"
    telegram_channel = "telegram_channel"

class MatchStatus(str, enum.Enum):
    upcoming = "upcoming"
    finished = "finished"

class ResultStatus(str, enum.Enum):
    win = "win"
    loss = "loss"
    refund = "refund"

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, nullable=True)
    source_type = Column(Enum(SourceType), nullable=False)
    weight = Column(Float, default=1.0) # Вес доверия к источнику (от 1.0 до 5.0)
    is_active = Column(Boolean, default=True)

    predictions = relationship("Prediction", back_populates="source")

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    sport_type = Column(String, index=True, nullable=False)
    league = Column(String, index=True, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    match_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(MatchStatus), default=MatchStatus.upcoming)
    final_score_home = Column(Integer, nullable=True)
    final_score_away = Column(Integer, nullable=True)

    # Новые поля для ИИ-парсера
    is_bet_of_the_day = Column(Boolean, default=False)
    ai_insight = Column(String, nullable=True)
    cappers_reasoning = Column(String, nullable=True)
    tactical_analysis = Column(String, nullable=True)
    key_factors = Column(String, nullable=True)

    predictions = relationship("Prediction", back_populates="match")
    result = relationship("HistoricalResult", back_populates="match", uselist=False)

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    predicted_outcome = Column(String, nullable=False) # e.g., 'home_win', 'draw', 'total_over_2.5'
    odds = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)
    reasoning = Column(String, nullable=True)
    status = Column(Enum(ResultStatus), nullable=True) # win, loss, refund
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="predictions")
    source = relationship("Source", back_populates="predictions")

class HistoricalResult(Base):
    __tablename__ = "historical_results"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)
    final_score_home = Column(Integer, nullable=True)
    final_score_away = Column(Integer, nullable=True)
    match_status = Column(Enum(ResultStatus), nullable=False)

    match = relationship("Match", back_populates="result")
