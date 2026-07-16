from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, Text, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True)

    # ✅ НОВЫЕ ПОЛЯ ДЛЯ ПРОФИЛЯ
    first_name = Column(String(100), nullable=True)   # ✅ ДОБАВИТЬ
    last_name = Column(String(100), nullable=True)    # ✅ ДОБАВИТЬ
    country = Column(String(100), nullable=True)      # ✅ ДОБАВИТЬ
    city = Column(String(100), nullable=True)         # ✅ ДОБАВИТЬ
    region = Column(String(100), nullable=True)       # ✅ ДОБАВИТЬ

    # Телефон
    phone = Column(String(20), unique=True, nullable=True)
    phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(DateTime, nullable=True)

    # Email верификация
    is_email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    verification_token_used = Column(Boolean, default=False)

    # OTP для телефона
    otp_code = Column(String(6), nullable=True)
    otp_expires = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    otp_last_attempt = Column(DateTime, nullable=True)
    
    reset_code = Column(String(6), nullable=True)
    reset_code_expires = Column(DateTime, nullable=True)
    reset_code_attempts = Column(Integer, default=0)

    # Восстановление пароля
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    reset_token_used = Column(Boolean, default=False)

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    president_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)      # ✅ НОВОЕ
    country = Column(String(100), nullable=True)   # ✅ НОВОЕ
    region = Column(String(100), nullable=True)    # ✅ НОВОЕ
    logo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ✅ НОВЫЕ ПОЛЯ ДЛЯ СТАТУСА КЛУБА
    is_official = Column(Boolean, default=False)
    official_verified_at = Column(DateTime, nullable=True)
    official_verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

class ClubJudge(Base):
    __tablename__ = "club_judges"

    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True)
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

class ClubRequest(Base):
    __tablename__ = "club_requests"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Связи
    club = relationship("Club", backref="requests")
    user = relationship("User", backref="club_requests")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tournament = Column(String(100), nullable=True)
    stage = Column(String(100), nullable=True)
    table_number = Column(Integer, nullable=True)
    game_number = Column(Integer, nullable=True)
    game_date = Column(Date, nullable=True)
    game_time = Column(Time, nullable=True)
    winner = Column(String(10), nullable=True)
    best_move = Column(Text, nullable=True)
    protest = Column(Text, nullable=True)
    protest_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    seat_number = Column(Integer, nullable=False)
    player_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=True)
    fouls = Column(Integer, default=0)
    points = Column(Integer, default=0)
    bonus = Column(DECIMAL(3, 1), default=0)
    removed_rule = Column(String(50), nullable=True)
    is_removed = Column(Boolean, default=False)

class NightAction(Base):
    __tablename__ = "night_actions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    night_number = Column(Integer, nullable=False)
    kill_target = Column(Integer, nullable=True)
    don_check = Column(Integer, nullable=True)
    sheriff_check = Column(Integer, nullable=True)

class VoteRound(Base):
    __tablename__ = "vote_rounds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    is_elimination = Column(Boolean, default=False)
    elimination_votes = Column(Integer, default=0)
    result = Column(Text, nullable=True)

class VoteItem(Base):
    __tablename__ = "vote_items"

    id = Column(Integer, primary_key=True, index=True)
    vote_round_id = Column(Integer, ForeignKey("vote_rounds.id", ondelete="CASCADE"), nullable=False)
    player_seat = Column(Integer, nullable=False)
    votes_count = Column(Integer, nullable=False)

class ClubRating(Base):
    __tablename__ = "club_rating"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, unique=True)
    games_played = Column(Integer, default=0)
    red_wins = Column(Integer, default=0)
    black_wins = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PlayerStat(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    points = Column(Integer, default=0)
    bonus = Column(DECIMAL(5, 1), default=0)
    best_moves = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())