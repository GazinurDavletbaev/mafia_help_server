from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract
from models.db import User, Club, Game, GamePlayer
from core.database import get_db
from .core import get_current_user

router = APIRouter()

@router.get("/{club_id}/rating")
async def get_club_rating(
    club_id: int,
    month: int,
    year: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    games = db.query(Game).filter(
        Game.club_id == club_id,
        extract('year', Game.game_date) == year,
        extract('month', Game.game_date) == month
    ).all()
    
    if not games:
        return {
            "month": month,
            "year": year,
            "games_played": 0,
            "has_games": False,
            "club_name": club.title,
            "players": [],
        }
    
    stats = {}
    
    for game in games:
        game_players = db.query(GamePlayer).filter(GamePlayer.game_id == game.id).all()
        for gp in game_players:
            if gp.user_id not in stats:
                stats[gp.user_id] = {
                    "username": gp.player_name or "Игрок",
                    "points": 0,
                    "bonus": 0,
                    "wins": 0,
                }
            
            stats[gp.user_id]["points"] += gp.points
            stats[gp.user_id]["bonus"] += float(gp.bonus) if gp.bonus else 0
            
            if game.winner == "red" and gp.role in ["citizen", "sheriff"]:
                stats[gp.user_id]["wins"] += 1
            elif game.winner == "black" and gp.role in ["mafia", "don"]:
                stats[gp.user_id]["wins"] += 1
    
    sorted_players = sorted(
        stats.values(),
        key=lambda x: x["points"] + x["bonus"],
        reverse=True
    )
    
    return {
        "month": month,
        "year": year,
        "games_played": len(games),
        "has_games": True,
        "club_name": club.title,
        "players": sorted_players,
    }