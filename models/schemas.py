from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time

# ========== AUTH ==========
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    phone: Optional[str] = None
    phone_verified: bool = False
    is_email_verified: bool = False
    avatar_url: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# ========== PHONE ==========
class PhoneSendCodeRequest(BaseModel):
    phone: str

class PhoneVerifyRequest(BaseModel):
    phone: str
    code: str

# ========== EMAIL VERIFICATION ==========
class EmailVerificationRequest(BaseModel):
    email: EmailStr

# ========== FORGOT PASSWORD ==========
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# ========== GAME ==========
class GamePlayerSchema(BaseModel):
    seat: int
    name: str
    role: str
    fouls: int
    points: int
    bonus: float
    rule: Optional[str] = None

class NightActionSchema(BaseModel):
    night: int
    kill: int
    don: int
    sheriff: int

class VoteRoundSchema(BaseModel):
    day: int
    round: int
    votes: Dict[int, int]
    result: str

class GameSave(BaseModel):
    club_id: int
    judge_id: Optional[int] = None
    tournament: str
    stage: str
    table: int
    game: int
    date: date
    time: str
    winner: str
    best_move: str
    protest: str
    protest_comment: str
    players: List[GamePlayerSchema]
    night_actions: List[NightActionSchema]
    vote_rounds: List[VoteRoundSchema]

# ========== RATING ==========
class PlayerRating(BaseModel):
    username: str
    games_played: int
    wins: int
    points: int
    bonus: float
    best_moves: int

class ClubRatingSchema(BaseModel):
    club_name: str
    games_played: int
    red_wins: int
    black_wins: int
    total_points: int
