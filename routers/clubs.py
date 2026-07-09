from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import extract

from models.db import User, Club, ClubJudge, ClubRequest, Game, GamePlayer, NightAction, VoteItem, VoteRound, ClubRating
from core.database import get_db
from core.security import decode_token

router = APIRouter()

# ============================================================
# СХЕМЫ
# ============================================================

class ClubCreate(BaseModel):
    title: str
    city: Optional[str] = None
    description: Optional[str] = None      # ✅ НОВОЕ
    country: Optional[str] = None          # ✅ НОВОЕ
    region: Optional[str] = None           # ✅ НОВОЕ

class ClubResponse(BaseModel):
    id: int
    title: str
    city: Optional[str]
    president_id: int
    president_name: Optional[str]
    logo_url: Optional[str]
    judges_count: int
    is_official: bool
    is_member: bool = False
    is_pending: bool = False
    created_at: datetime

class ClubDetailResponse(BaseModel):
    id: int
    title: str
    city: Optional[str]
    president_id: int
    president_name: Optional[str]
    description: Optional[str] = None      # ✅ ДОБАВЛЕНО
    country: Optional[str] = None          # ✅ ДОБАВЛЕНО
    region: Optional[str] = None           # ✅ ДОБАВЛЕНО
    logo_url: Optional[str]
    judges_count: int
    is_official: bool
    created_at: datetime

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_current_user(token: str, db: Session):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# ============================================================
# ЭНДПОИНТЫ КЛУБОВ
# ============================================================

# ---------- ПОЛУЧИТЬ ВСЕ КЛУБЫ -------
@router.get("/clubs", response_model=List[ClubResponse])
async def get_clubs(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    clubs = db.query(Club).all()
    result = []
    for club in clubs:
        president = db.query(User).filter(User.id == club.president_id).first()
        judges_count = db.query(ClubJudge).filter(ClubJudge.club_id == club.id).count()
        
        is_member = db.query(ClubJudge).filter(
            ClubJudge.club_id == club.id,
            ClubJudge.judge_id == user.id
        ).first() is not None
        
        pending_request = db.query(ClubRequest).filter(
            ClubRequest.club_id == club.id,
            ClubRequest.user_id == user.id,
            ClubRequest.status == "pending"
        ).first()
        is_pending = pending_request is not None
        
        result.append({
            "id": club.id,
            "title": club.title,
            "city": club.city,
            "president_id": club.president_id,
            "president_name": president.username if president else None,
            "description": club.description,        # ✅ ДОБАВЛЕНО
            "country": club.country,                # ✅ ДОБАВЛЕНО
            "region": club.region,                  # ✅ ДОБАВЛЕНО
            "logo_url": club.logo_url,
            "judges_count": judges_count,
            "is_official": club.is_official,
            "is_member": is_member,
            "is_pending": is_pending,
            "created_at": club.created_at,
        })
    
    # Сортировка: сначала официальные
    result.sort(key=lambda x: (not x["is_official"], x["title"]))
    return result

# ---------- СОЗДАТЬ КЛУБ ----------
@router.post("/clubs", response_model=ClubDetailResponse)
async def create_club(
    club_data: ClubCreate,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    # Проверка, что у пользователя нет клуба
    existing_club = db.query(Club).filter(Club.president_id == user.id).first()
    if existing_club:
        raise HTTPException(status_code=400, detail="Вы уже являетесь президентом клуба")
    
    # Проверка дубликата названия
    existing = db.query(Club).filter(Club.title == club_data.title).first()
    if existing:
        raise HTTPException(status_code=400, detail="Клуб с таким названием уже существует")
    
    club = Club(
        title=club_data.title,
        city=club_data.city,
        president_id=user.id,
        description=club_data.description,    # ✅ ДОБАВЛЕНО
        country=club_data.country,            # ✅ ДОБАВЛЕНО
        region=club_data.region,              # ✅ ДОБАВЛЕНО
        is_official=False,
    )
    db.add(club)
    db.commit()
    db.refresh(club)
    
    # Добавляем создателя как участника
    judge = ClubJudge(club_id=club.id, judge_id=user.id)
    db.add(judge)
    db.commit()
    
    return {
        "id": club.id,
        "title": club.title,
        "city": club.city,
        "president_id": club.president_id,
        "president_name": user.username,
        "description": club.description,      # ✅ ДОБАВЛЕНО
        "country": club.country,              # ✅ ДОБАВЛЕНО
        "region": club.region,                # ✅ ДОБАВЛЕНО
        "logo_url": club.logo_url,
        "judges_count": 1,
        "is_official": club.is_official,
        "created_at": club.created_at,
    }

# ---------- ПОЛУЧИТЬ КЛУБ ПО ID ----------
@router.get("/clubs/{club_id}", response_model=ClubDetailResponse)
async def get_club(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    president = db.query(User).filter(User.id == club.president_id).first()
    judges_count = db.query(ClubJudge).filter(ClubJudge.club_id == club.id).count()
    
    return {
        "id": club.id,
        "title": club.title,
        "city": club.city,
        "president_id": club.president_id,
        "president_name": president.username if president else None,
        "logo_url": club.logo_url,
        "judges_count": judges_count,
        "is_official": club.is_official,
        "created_at": club.created_at,
    }

# ---------- ПОЛУЧИТЬ МОИ КЛУБЫ ----------
@router.get("/my-clubs", response_model=List[ClubResponse])
async def get_my_clubs(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    judges = db.query(ClubJudge).filter(ClubJudge.judge_id == user.id).all()
    club_ids = [j.club_id for j in judges]
    clubs = db.query(Club).filter(Club.id.in_(club_ids)).all()
    
    result = []
    for club in clubs:
        president = db.query(User).filter(User.id == club.president_id).first()
        judges_count = db.query(ClubJudge).filter(ClubJudge.club_id == club.id).count()
        result.append({
            "id": club.id,
            "title": club.title,
            "city": club.city,
            "president_id": club.president_id,
            "president_name": president.username if president else None,
            "logo_url": club.logo_url,
            "judges_count": judges_count,
            "is_official": club.is_official,
            "is_member": True,
            "is_pending": False,
            "created_at": club.created_at,
        })
    return result

# ============================================================
# ЗАЯВКИ
# ============================================================

# ---------- ПОДАТЬ ЗАЯВКУ ----------
@router.post("/clubs/{club_id}/join")
async def join_club(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    # Проверка, не состоит ли уже
    existing = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже в этом клубе")
    
    # Проверка, нет ли уже заявки
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

# ---------- ПОЛУЧИТЬ ЗАЯВКИ КЛУБА ----------
@router.get("/clubs/{club_id}/requests")
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

# ---------- ПРИНЯТЬ ЗАЯВКУ ----------
@router.post("/clubs/requests/{request_id}/approve")
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

# ---------- ОТКЛОНИТЬ ЗАЯВКУ ----------
@router.post("/clubs/requests/{request_id}/reject")
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

# ============================================================
# УЧАСТНИКИ (ТОЛЬКО ДЛЯ ПРЕЗИДЕНТА)
# ============================================================

# ---------- ПОЛУЧИТЬ УЧАСТНИКОВ КЛУБА ------@router.get("/clubs/{club_id}/members")
@router.get("/clubs/{club_id}/members")
async def get_club_members(
    club_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    # ✅ Убираем проверку — все могут смотреть участников
    judges = db.query(ClubJudge).filter(ClubJudge.club_id == club_id).all()
    
    members = []
    judges_list = []
    
    for judge in judges:
        u = db.query(User).filter(User.id == judge.judge_id).first()
        if not u:
            continue
        
        is_president = (judge.judge_id == club.president_id)
        
        member_data = {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_president": is_president,
            "is_judge": True,
            "joined_at": judge.created_at,
        }
        members.append(member_data)
        
        if not is_president:
            judges_list.append(member_data)
    
    return {
        "members": members,
        "judges": judges_list,
    }
# ---------- УДАЛИТЬ УЧАСТНИКА ----------
@router.delete("/clubs/{club_id}/members/{user_id}")
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

# ---------- ВЫЙТИ ИЗ КЛУБА ----------
# ---------- ВЫЙТИ ИЗ КЛУБА ----------
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
    
    # Проверяем, является ли пользователь президентом
    is_president = club.president_id == user.id
    
    # Проверяем, является ли пользователь участником клуба
    is_member = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Вы не состоите в этом клубе")
    
    # Если пользователь — президент, удаляем клуб со всеми данными
    if is_president:
        # 1. Получаем все игры клуба
        games = db.query(Game).filter(Game.club_id == club_id).all()
        game_ids = [game.id for game in games]
        
        # 2. Удаляем всё, что связано с играми
        if game_ids:
            db.query(NightAction).filter(NightAction.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(VoteItem).filter(VoteItem.vote_round_id.in_(
                db.query(VoteRound.id).filter(VoteRound.game_id.in_(game_ids))
            )).delete(synchronize_session=False)
            db.query(VoteRound).filter(VoteRound.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(GamePlayer).filter(GamePlayer.game_id.in_(game_ids)).delete(synchronize_session=False)
            db.query(Game).filter(Game.id.in_(game_ids)).delete(synchronize_session=False)
        
        # 3. Удаляем связи участников
        db.query(ClubJudge).filter(ClubJudge.club_id == club_id).delete()
        
        # 4. Удаляем рейтинг клуба
        db.query(ClubRating).filter(ClubRating.club_id == club_id).delete()
        # 3.1 Удаляем все заявки в клуб
        db.query(ClubRequest).filter(ClubRequest.club_id == club_id).delete(synchronize_session=False)
        # 5. Удаляем сам клуб
        db.delete(club)
        db.commit()
        
        return {"message": "Клуб удалён. Все данные стёрты."}
    
    else:
        # Обычный участник — просто выходит
        db.query(ClubJudge).filter(
            ClubJudge.club_id == club_id,
            ClubJudge.judge_id == user.id
        ).delete()
        db.commit()
        
        return {"message": "Вы покинули клуб"}

# ---------- НАЗНАЧИТЬ СУДЬЁЙ ----------
@router.post("/clubs/{club_id}/promote/{user_id}")
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
    
    judge = db.query(ClubJudge).filter(
        ClubJudge.club_id == club_id,
        ClubJudge.judge_id == user_id
    ).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Пользователь не состоит в клубе")
    
    return {"message": "Пользователь назначен судьёй"}

# ---------- СНЯТЬ С ДОЛЖНОСТИ СУДЬИ ----------
@router.post("/clubs/{club_id}/demote/{user_id}")
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
        raise HTTPException(status_code=404, detail="Пользователь не состоит в клубе")
    
    return {"message": "Судья снят с должности"}
    
@router.get("/requests/pending-count")
async def get_pending_requests_count(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    # ✅ Проверяем, является ли пользователь президентом
    clubs = db.query(Club).filter(Club.president_id == user.id).all()
    if not clubs:
        return {"count": 0}  # ✅ Не президент → 0 заявок
    
    club_ids = [club.id for club in clubs]
    
    count = db.query(ClubRequest).filter(
        ClubRequest.club_id.in_(club_ids),
        ClubRequest.status == "pending"
    ).count()
    
    return {"count": count}

# ========== РЕЙТИНГ КЛУБА ЗА МЕСЯЦ ==========
@router.get("/clubs/{club_id}/rating")
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
    
    # ✅ Убираем проверку — все могут смотреть рейтинг
    
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
