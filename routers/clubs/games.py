from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from models.db import User, Club, ClubJudge, Game, GamePlayer, NightAction, VoteRound, VoteItem
from core.database import get_db
from .core import get_current_user

router = APIRouter()

@router.post("/save")
async def save_game(
    game_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Сохраняет завершённую игру в клуб (только президент или судья)"""
    
    club_id = game_data.get('club_id')
    if not club_id:
        raise HTTPException(status_code=400, detail="club_id обязателен")
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    is_president = club.president_id == current_user.id
    is_judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == current_user.id
    ).first() is not None
    
    if not is_president and not is_judge:
        raise HTTPException(
            status_code=403,
            detail="Только президент или судья клуба могут сохранять игры"
        )
    
    game_date = None
    if game_data.get('date'):
        try:
            game_date = datetime.strptime(game_data['date'], "%Y-%m-%d").date()
        except:
            pass
    
    game_time = None
    if game_data.get('time'):
        try:
            game_time = datetime.strptime(game_data['time'], "%H:%M").time()
        except:
            pass
    
    game = Game(
        club_id=club_id,
        judge_id=current_user.id,
        tournament=game_data.get('tournament'),
        stage=game_data.get('stage'),
        table_number=game_data.get('table'),
        game_number=game_data.get('game'),
        game_date=game_date,
        game_time=game_time,
        winner=game_data.get('winner'),
        best_move=game_data.get('bestMove'),
        protest=game_data.get('protest'),
        protest_comment=game_data.get('protestComment'),
    )
    db.add(game)
    db.flush()
    
    for player in game_data.get('players', []):
        game_player = GamePlayer(
            game_id=game.id,
            user_id=None,
            seat_number=player.get('seat', 0),
            player_name=player.get('name', ''),
            role=player.get('role', ''),
            fouls=player.get('fouls', 0),
            points=player.get('points', 0),
            bonus=player.get('bonus', 0),
            removed_rule=player.get('rule'),
            is_removed=bool(player.get('rule')),
        )
        db.add(game_player)
    
    night_actions = game_data.get('nightActions', [])
    for i in range(0, len(night_actions), 3):
        night = NightAction(
            game_id=game.id,
            night_number=i // 3 + 1,
            kill_target=night_actions[i] if i < len(night_actions) and night_actions[i] > 0 else None,
            don_check=night_actions[i+1] if i+1 < len(night_actions) and night_actions[i+1] > 0 else None,
            sheriff_check=night_actions[i+2] if i+2 < len(night_actions) and night_actions[i+2] > 0 else None,
        )
        db.add(night)
    
    vote_history = game_data.get('voteHistory', {})
    for day_str, day_data in vote_history.items():
        try:
            day = int(day_str)
        except:
            continue
        
        rounds = day_data.get('rounds', [])
        result = day_data.get('result', [])
        elimination_votes = day_data.get('eliminationVotes', 0)
        
        for round_idx, round_votes in enumerate(rounds):
            vote_round = VoteRound(
                game_id=game.id,
                day_number=day,
                round_number=round_idx + 1,
                is_elimination=False,
                elimination_votes=elimination_votes if round_idx == len(rounds) - 1 else 0,
                result=", ".join(map(str, result)) if result else "",
            )
            db.add(vote_round)
            db.flush()
            
            if isinstance(round_votes, dict):
                for seat_str, count in round_votes.items():
                    try:
                        vote_item = VoteItem(
                            vote_round_id=vote_round.id,
                            player_seat=int(seat_str),
                            votes_count=count,
                        )
                        db.add(vote_item)
                    except:
                        pass
    
    db.commit()
    
    return {
        "success": True,
        "game_id": game.id,
        "message": "Игра сохранена"
    }


@router.get("/club/{club_id}")
async def get_club_games(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все игры клуба (доступно всем авторизованным)"""
    
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
            "game_date": game.game_date.isoformat() if game.game_date else None,
            "game_time": game.game_time.isoformat() if game.game_time else None,
            "winner": game.winner,
            "judge_name": judge.username if judge else None,
            "created_at": game.created_at.isoformat() if game.created_at else None,
        })
    
    return result


@router.get("/{game_id}")
async def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить полные данные игры по ID (доступно всем авторизованным)"""
    
    # ✅ Ищем ИГРУ, а не клуб
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    players = db.query(GamePlayer).filter(GamePlayer.game_id == game.id).all()
    players_data = [{
        "seat": p.seat_number,
        "name": p.player_name,
        "role": p.role,
        "fouls": p.fouls,
        "points": p.points,
        "bonus": float(p.bonus) if p.bonus else 0,
        "rule": p.removed_rule,
    } for p in players]
    
    night_actions = db.query(NightAction).filter(NightAction.game_id == game.id).order_by(
        NightAction.night_number
    ).all()
    night_data = [{
        "night": n.night_number,
        "kill": n.kill_target or 0,
        "don": n.don_check or 0,
        "sheriff": n.sheriff_check or 0,
    } for n in night_actions]
    
    vote_rounds = db.query(VoteRound).filter(VoteRound.game_id == game.id).all()
    vote_history = {}
    for vr in vote_rounds:
        day_key = str(vr.day_number)
        if day_key not in vote_history:
            vote_history[day_key] = {
                "rounds": [],
                "result": [],
                "eliminationVotes": 0,
            }
        
        items = db.query(VoteItem).filter(VoteItem.vote_round_id == vr.id).all()
        votes = {str(item.player_seat): item.votes_count for item in items}
        vote_history[day_key]["rounds"].append(votes)
        
        if vr.result:
            try:
                vote_history[day_key]["result"] = [int(x.strip()) for x in vr.result.split(",") if x.strip()]
            except:
                pass
        vote_history[day_key]["eliminationVotes"] = vr.elimination_votes
    
    judge = db.query(User).filter(User.id == game.judge_id).first()
    
    return {
        "id": game.id,
        "club_id": game.club_id,
        "tournament": game.tournament,
        "stage": game.stage,
        "table": game.table_number,
        "game": game.game_number,
        "date": game.game_date.isoformat() if game.game_date else None,
        "time": game.game_time.isoformat() if game.game_time else None,
        "judge": judge.username if judge else None,
        "winner": game.winner,
        "best_move": game.best_move,
        "protest": game.protest,
        "protest_comment": game.protest_comment,
        "players": players_data,
        "night_actions": night_data,
        "vote_history": vote_history,
    }
