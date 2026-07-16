from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.db import User, Club, ClubJudge, ClubRequest, Game, NightAction, VoteItem, VoteRound, GamePlayer, ClubRating
from core.database import get_db
from .core import get_current_user

router = APIRouter()

@router.get("/{club_id}/members")
async def get_club_members(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    # ✅ Все участники клуба (у кого club_id == club_id)
    users = db.query(User).filter(User.club_id == club_id).all()
    
    # ✅ Все судьи клуба
    judge_ids = [j.judge_id for j in db.query(ClubJudge).filter(ClubJudge.club_id == club_id).all()]
    
    members = []
    for u in users:
        members.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_president": u.id == club.president_id,
            "is_judge": u.id in judge_ids,
            "joined_at": u.created_at,
        })
    
    return {"members": members}

@router.delete("/{club_id}/members/{user_id}")
async def remove_member(
    club_id: int,
    user_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только президент может удалять участников")
    
    if club.president_id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить президента клуба")
    
    judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user_id
    ).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Пользователь не состоит в клубе")
    
    db.delete(judge)
    db.commit()
    
    return {"message": "Участник удалён из клуба"}

@router.delete("/{club_id}/leave")
async def leave_club(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    is_president = club.president_id == user.id
    
    is_member = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Вы не состоите в этом клубе")
    
    if is_president:
        games = db.query(Game).filter(Game.club_id == club_id).all()
        game_ids = [game.id for game in games]
        
        if game_ids:
            db.query(NightAction).filter(NightAction.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(VoteItem).filter(VoteItem.vote_round_id.in_(
                db.query(VoteRound.id).filter(VoteRound.game_id.in_(game_ids))
            )).delete(synchronize_session=False)
            db.query(VoteRound).filter(VoteRound.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(GamePlayer).filter(GamePlayer.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(Game).filter(Game.id.in_(game_ids)).delete(synchronize_session=False)
        
        db.query(ClubJudge).filter(ClubJudge.club_id == club_id).delete()
        db.query(ClubRating).filter(ClubRating.club_id == club_id).delete()
        db.query(ClubRequest).filter(ClubRequest.club_id == club_id).delete(synchronize_session=False)
        db.delete(club)
        db.commit()
        
        return {"message": "Клуб удалён. Все данные стёрты."}
    else:
        db.query(ClubJudge).filter(
            ClubJudge.club_id == club_id,
            ClubJudge.judge_id == user.id
        ).delete()
        db.commit()
        
        return {"message": "Вы покинули клуб"}