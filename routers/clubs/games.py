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