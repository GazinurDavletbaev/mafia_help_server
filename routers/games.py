from fastapi import APIRouter, Depends, HTTPException, status
from core.database import get_db
from sqlalchemy.orm import Session
from core.security import get_current_user
from models.db import User, Club, Game, GamePlayer, NightAction, VoteRound, VoteItem, ClubJudge

router = APIRouter()

@router.post("/save")
async def save_game():
    return {"message": "Save game - будет реализовано позже"}

@router.get("/history/{club_id}")
async def get_history(club_id: int):
    return {"message": f"History for club {club_id} - будет реализовано позже"}

@router.get("/club/{club_id}")
async def get_club_games(
    club_id: int,
    current_user: User = Depends(get_current_user),  # ✅ ТАК
    db: Session = Depends(get_db)
):
    # Проверяем доступ к клубу
    is_member = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == current_user.id
    ).first() is not None
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    games = db.query(Game).filter(Game.club_id == club_id).order_by(
        Game.game_date.desc(),
        Game.created_at.desc()
    ).all()
    
    result = []
    for game in games:
        judge = db.query(User).filter(User.id == game.judge_id).first()
        result.append({
            "id": game.id,
            "tournament": game.tournament,
            "stage": game.stage,
            "table_number": game.table_number,
            "game_number": game.game_number,
            "game_date": game.game_date,
            "game_time": game.game_time,
            "winner": game.winner,
            "judge_name": judge.username if judge else None,
            "created_at": game.created_at,
        })
    
    return result