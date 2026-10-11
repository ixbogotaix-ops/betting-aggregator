from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .models import SourceType, MatchStatus, ResultStatus

# --- Source Schemas ---
class SourceBase(BaseModel):
    name: str
    url: Optional[str] = None
    source_type: SourceType
    is_active: bool = True

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    id: int

    class Config:
        from_attributes = True

# --- Prediction Schemas ---
class PredictionBase(BaseModel):
    source_id: int
    predicted_outcome: str
    odds: float
    confidence_score: Optional[float] = None

class PredictionCreate(PredictionBase):
    match_id: int

class PredictionResponse(PredictionBase):
    id: int
    match_id: int
    created_at: datetime
    source: SourceResponse

    class Config:
        from_attributes = True

# --- Historical Result Schemas ---
class HistoricalResultBase(BaseModel):
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None
    match_status: ResultStatus

class HistoricalResultCreate(HistoricalResultBase):
    match_id: int

class HistoricalResultResponse(HistoricalResultBase):
    id: int
    match_id: int

    class Config:
        from_attributes = True

# --- Match Schemas ---
class MatchBase(BaseModel):
    sport_type: str
    league: str
    home_team: str
    away_team: str
    match_date: datetime
    status: MatchStatus = MatchStatus.upcoming

class MatchCreate(MatchBase):
    pass

class MatchResponse(MatchBase):
    id: int
    predictions: List[PredictionResponse] = []

    class Config:
        from_attributes = True

class TopBetPredictionDetail(BaseModel):
    source_name: str
    source_type: str
    predicted_outcome: str
    odds: float
    confidence_score: Optional[float] = None
    source_weight: Optional[float] = 1.0
    reasoning: Optional[str] = None

# --- Consensus Schemas ---
class TopBetResponse(BaseModel):
    match_id: int
    match_name: str
    match_date: datetime
    league: str
    sport_type: str
    recommended_outcome: str
    average_odds: float
    confidence_score: float
    supporting_sources: List[str]
    is_bet_of_the_day: bool = False
    ai_insight: Optional[str] = None
    cappers_reasoning: Optional[str] = None
    tactical_analysis: Optional[str] = None
    key_factors: List[str] = []
    h2h_summary: Optional[str] = None
    all_predictions: List[TopBetPredictionDetail] = []
  
class SourceStatusResponse(BaseModel):  
    id: int  
    name: str  
    source_type: str  
    is_active: bool  
    recent_predictions_count: int  
    last_parsed_at: Optional[datetime] = None  
    status: str 
