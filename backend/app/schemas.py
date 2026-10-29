from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Union, Any
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
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None

    class Config:
        from_attributes = True

class TopBetPredictionDetail(BaseModel):
    source_name: str
    source_type: str
    predicted_outcome: str
    odds: float
    confidence_score: Optional[float] = None
    source_weight: Optional[float] = 1.0
    sport_winrate: Optional[float] = None
    tier: Optional[str] = None
    reasoning: Optional[str] = None
    status: Optional[str] = None

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
    value_badge: Optional[str] = None
    ev_percent: Optional[float] = None
    cappers_reasoning: Optional[str] = None
    tactical_analysis: Optional[str] = None
    key_factors: List[str] = []
    h2h_summary: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    country_name: Optional[str] = None
    country_flag_url: Optional[str] = None
    country_flag_emoji: Optional[str] = None
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None
    status: Optional[str] = "upcoming"
    bet_result: Optional[str] = None
    daily_rank: Optional[int] = None
    slot_label: Optional[str] = None
    all_predictions: List[TopBetPredictionDetail] = []
  
class SourceStatusResponse(BaseModel):  
    id: int  
    name: str  
    source_type: str  
    is_active: bool  
    recent_predictions_count: int  
    last_parsed_at: Optional[datetime] = None  
    status: str 

class PerformanceOverview(BaseModel):
    total_matches: int
    wins: int
    losses: int
    refunds: int
    winrate_pct: float
    roi_pct: float
    net_profit_units: float

class SourceLeaderboardItem(BaseModel):
    source_name: str
    source_type: str
    sport: Optional[str] = "All"
    total_bets: int
    wins: int
    losses: int
    refunds: int
    winrate_pct: float
    roi_pct: float
    net_profit: float
    dynamic_weight: Optional[float] = 1.0
    tier: Optional[str] = "neutral"

class PerformanceStatsResponse(BaseModel):
    overview: PerformanceOverview
    leaderboard: List[SourceLeaderboardItem]
    sports_breakdown: Optional[Dict[str, List[SourceLeaderboardItem]]] = {}
    available_sports: Optional[List[str]] = []

class ParlayItem(BaseModel):
    match_id: Union[int, str]
    match_name: str
    match_date: datetime
    sport_type: str
    league: str
    outcome: str
    odds: float
    confidence_score: float
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None

class ParlayCard(BaseModel):
    title: str
    type: str
    tag: str
    total_odds: float
    items_count: int
    potential_win_1000: float
    items: List[ParlayItem] = []

class DailyParlaysResponse(BaseModel):
    ai_parlay: Optional[ParlayCard] = None
    safe_parlay: Optional[ParlayCard] = None
    hot_parlay: Optional[ParlayCard] = None

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    demo: Optional[bool] = False

class TelegramAuthRequest(BaseModel):
    init_data: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
