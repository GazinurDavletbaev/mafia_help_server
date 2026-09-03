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
    
    users = db.query(User).filter(User.club_id == club_id).all()
    
    judge_ids = [j.judge_id for j in db.query(ClubJudge).filter(ClubJudge.club_id == club_id).all()]
    
    members = []
    for u in users:
        members.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "avatar_url": u.avatar_url,
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
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user:
        target_user.club_id = None
        db.commit()
    
    judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user_id
    ).first()
    if judge:
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
    
    is_judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user.id
    ).first() is not None
    
    is_member = is_judge or (user.club_id == club_id)
    
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
        user.club_id = None
        db.commit()
        
        if is_judge:
            db.query(ClubJudge).filter(
                ClubJudge.club_id == club_id,
                ClubJudge.judge_id == user.id
            ).delete()
            db.commit()
        
        return {"message": "Вы покинули клуб"}

# ============================================================
# ПОДАТЬ ЗАЯВКУ (С ПРОВЕРКОЙ НА ДРУГИЕ ЗАЯВКИ)
# ============================================================
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
    
    # ✅ Проверяем, не состоит ли пользователь уже в каком-то клубе
    if user.club_id is not None:
        raise HTTPException(
            status_code=400, 
            detail="Вы уже состоите в клубе. Покините текущий клуб, чтобы подать заявку в новый."
        )
    
    # ✅ Проверяем, не является ли пользователь судьёй в другом клубе
    existing_judge = db.query(ClubJudge).filter(ClubJudge.judge_id == user.id).first()
    if existing_judge:
        raise HTTPException(
            status_code=400,
            detail="Вы уже являетесь судьёй в другом клубе. Покините его, чтобы подать заявку."
        )
    
    # ✅ Проверяем, нет ли уже активной заявки в этот клуб
    existing_request = db.query(ClubRequest).filter(
        ClubRequest.club_id == club_id,
        ClubRequest.user_id == user.id,
        ClubRequest.status == "pending"
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Вы уже отправили заявку в этот клуб")
    
    # ✅ Проверяем, нет ли активной заявки в ДРУГОЙ клуб
    other_request = db.query(ClubRequest).filter(
        ClubRequest.user_id == user.id,
        ClubRequest.status == "pending"
    ).first()
    if other_request:
        raise HTTPException(
            status_code=400,
            detail="У вас уже есть активная заявка в другой клуб. Отзовите её, чтобы подать новую."
        )
    
    # ✅ Создаём заявку
    request = ClubRequest(
        club_id=club_id,
        user_id=user.id,
        status="pending"
    )
    db.add(request)
    db.commit()
    
    return {"message": "Заявка отправлена"}

# ============================================================
# ОСТАЛЬНЫЕ ЭНДПОИНТЫ (ЗАЯВКИ, ОТЗЫВ И Т.Д.)
# ============================================================

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
    
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if target_user:
        target_user.club_id = club.id
        db.commit()
    
    request.status = "approved"
    db.commit()
    
    return {"message": "Заявка принята. Пользователь добавлен в клуб."}

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

# ============================================================
# ОТОЗВАТЬ ЗАЯВКУ
# ============================================================
@router.delete("/requests/cancel")
async def cancel_request_by_club(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    request = db.query(ClubRequest).filter(
        ClubRequest.club_id == club_id,
        ClubRequest.user_id == user.id,
        ClubRequest.status == "pending"
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    db.delete(request)
    db.commit()
    
    return {"success": True, "message": "Заявка отозвана"}