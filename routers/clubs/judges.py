from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.db import User, Club, ClubJudge
from core.database import get_db
from .core import get_current_user

router = APIRouter()

@router.post("/{club_id}/promote/{user_id}")
async def promote_to_judge(
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
        raise HTTPException(status_code=403, detail="Только президент может назначать судей")
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # ✅ Проверяем, что пользователь состоит в клубе
    if target_user.club_id != club_id:
        raise HTTPException(status_code=400, detail="Пользователь не состоит в этом клубе")
    
    # ✅ Проверяем, не судья ли уже
    existing = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже является судьёй")
    
    judge = ClubJudge(club_id=club_id, judge_id=user_id)
    db.add(judge)
    db.commit()
    
    return {"message": "Судья назначен"}

@router.post("/{club_id}/demote/{user_id}")
async def demote_from_judge(
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
        raise HTTPException(status_code=403, detail="Только президент может снимать судей")
    
    if club.president_id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя снять президента")
    
    judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user_id
    ).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Пользователь не является судьёй")
    
    db.delete(judge)
    db.commit()
    
    return {"message": "Судья снят с должности"}