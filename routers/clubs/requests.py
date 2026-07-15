from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.db import User, Club, ClubJudge, ClubRequest
from core.database import get_db
from .core import get_current_user

router = APIRouter()

@router.post("/{club_id}/join")
async def join_club(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    existing = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже в этом клубе")
    
    existing_request = db.query(ClubRequest).filter(
        ClubRequest.club_id == club_id,
        ClubRequest.user_id == user.id,
        ClubRequest.status == "pending"
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Заявка уже отправлена")
    
    request = ClubRequest(
        club_id=club_id,
        user_id=user.id,
        status="pending"
    )
    db.add(request)
    db.commit()
    
    return {"message": "Заявка отправлена"}

@router.get("/{club_id}/requests")
async def get_club_requests(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != user.id:
        raise HTTPException(status_code=403, detail="Только президент может просматривать заявки")
    
    requests = db.query(ClubRequest).filter(
        ClubRequest.club_id == club_id,
        ClubRequest.status == "pending"
    ).all()
    
    result = []
    for req in requests:
        applicant = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "username": applicant.username if applicant else "Неизвестен",
            "email": applicant.email if applicant else "",
            "created_at": req.created_at,
        })
    
    return result

@router.post("/requests/{request_id}/approve")
async def approve_request(
    request_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    request = db.query(ClubRequest).filter(ClubRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    club = db.query(Club).filter(Club.id == request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != user.id:
        raise HTTPException(status_code=403, detail="Только президент может принимать заявки")
    
    judge = ClubJudge(
        club_id=club.id,
        judge_id=request.user_id
    )
    db.add(judge)
    request.status = "approved"
    db.commit()
    
    return {"message": "Заявка принята"}

@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    request = db.query(ClubRequest).filter(ClubRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    club = db.query(Club).filter(Club.id == request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != user.id:
        raise HTTPException(status_code=403, detail="Только президент может отклонять заявки")
    
    request.status = "rejected"
    db.commit()
    
    return {"message": "Заявка отклонена"}

@router.get("/requests/pending-count")
async def get_pending_requests_count(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    clubs = db.query(Club).filter(Club.president_id == user.id).all()
    if not clubs:
        return {"count": 0}
    
    club_ids = [club.id for club in clubs]
    
    count = db.query(ClubRequest).filter(
        ClubRequest.club_id.in_(club_ids),
        ClubRequest.status == "pending"
    ).count()
    
    return {"count": count}