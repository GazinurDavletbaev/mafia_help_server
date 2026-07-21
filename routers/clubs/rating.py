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
        extract('month', Game.game_date) == month,
        Game.counts_in_rating == True  # ✅ ТОЛЬКО ТЕ, КТО В РЕЙТИНГЕ
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
            player_name = gp.player_name or f"Игрок {gp.seat_number}"
            
            if player_name not in stats:
                stats[player_name] = {
                    "username": player_name,
                    "games_played": 0,
                    "points": 0,
                    "bonus": 0.0,
                    "wins": 0,
                }
            
            stats[player_name]["games_played"] += 1
            stats[player_name]["points"] += gp.points
            stats[player_name]["bonus"] += float(gp.bonus) if gp.bonus else 0
            
            if game.winner == "red" and gp.role in ["citizen", "sheriff"]:
                stats[player_name]["wins"] += 1
            elif game.winner == "black" and gp.role in ["mafia", "don"]:
                stats[player_name]["wins"] += 1
    
    sorted_players = sorted(
        stats.values(),
        key=lambda x: x["points"] + x["bonus"],
        reverse=True
    )
    
    # ✅ Округляем бонусы и считаем total
    for player in sorted_players:
        player["bonus"] = round(player["bonus"], 1)
        player["total"] = round(player["points"] + player["bonus"], 1)
    
    return {
        "month": month,
        "year": year,
        "games_played": len(games),
        "has_games": True,
        "club_name": club.title,
        "players": sorted_players,
    }
