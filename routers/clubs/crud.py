from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

from models.db import User, Club, ClubJudge, ClubRequest
from core.database import get_db
from .core import get_current_user

router = APIRouter()

UPLOAD_DIR = "/root/mafia_excel_api/uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========== СХЕМЫ ==========
class ClubCreate(BaseModel):
    title: str
    city: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None

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
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    logo_url: Optional[str]
    judges_count: int
    is_official: bool
    created_at: datetime

class ClubUpdate(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    logo_url: Optional[str] = None

# ========== ЭНДПОИНТЫ ==========

@router.get("/", response_model=List[ClubResponse])
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
            "logo_url": club.logo_url,
            "judges_count": judges_count,
            "is_official": club.is_official,
            "is_member": is_member,
            "is_pending": is_pending,
            "created_at": club.created_at,
        })
    
    result.sort(key=lambda x: (not x["is_official"], x["title"]))
    return result

@router.post("/", response_model=ClubDetailResponse)
async def create_club(
    club_data: ClubCreate,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    existing_club = db.query(Club).filter(Club.president_id == user.id).first()
    if existing_club:
        raise HTTPException(status_code=400, detail="Вы уже являетесь президентом клуба")
    
    existing = db.query(Club).filter(Club.title == club_data.title).first()
    if existing:
        raise HTTPException(status_code=400, detail="Клуб с таким названием уже существует")
    
    club = Club(
        title=club_data.title,
        city=club_data.city,
        president_id=user.id,
        description=club_data.description,
        country=club_data.country,
        region=club_data.region,
        is_official=False,
    )
    db.add(club)
    db.commit()
    db.refresh(club)
    
    # ✅ Проставляем club_id пользователю (президенту)
    user.club_id = club.id
    db.commit()
    
    judge = ClubJudge(club_id=club.id, judge_id=user.id)
    db.add(judge)
    db.commit()
    
    return {
        "id": club.id,
        "title": club.title,
        "city": club.city,
        "president_id": club.president_id,
        "president_name": user.username,
        "description": club.description,
        "country": club.country,
        "region": club.region,
        "logo_url": club.logo_url,
        "judges_count": 1,
        "is_official": club.is_official,
        "created_at": club.created_at,
    }

@router.get("/my-club")
async def get_my_club(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.president_id == user.id).first()
    
    if not club:
        judge = db.query(ClubJudge).filter(ClubJudge.judge_id == user.id).first()
        if judge:
            club = db.query(Club).filter(Club.id == judge.club_id).first()
    
    if not club:
        return {"club": None}
    
    president = db.query(User).filter(User.id == club.president_id).first()
    judges_count = db.query(ClubJudge).filter(ClubJudge.club_id == club.id).count()
    
    return {
        "id": club.id,
        "title": club.title,
        "city": club.city,
        "description": club.description,
        "country": club.country,
        "region": club.region,
        "logo_url": club.logo_url,
        "president_id": club.president_id,
        "president_name": president.username if president else None,
        "judges_count": judges_count,
        "is_official": club.is_official,
        "created_at": club.created_at,
    }

@router.get("/{club_id}", response_model=ClubDetailResponse)
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

@router.put("/{club_id}")
async def update_club(
    club_id: int,
    club_data: ClubUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != user.id:
        raise HTTPException(status_code=403, detail="Только президент может редактировать клуб")
    
    if club_data.title is not None:
        existing = db.query(Club).filter(
            Club.title == club_data.title,
            Club.id != club_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Клуб с таким названием уже существует")
        club.title = club_data.title
    
    if club_data.city is not None:
        club.city = club_data.city
    if club_data.description is not None:
        club.description = club_data.description
    if club_data.country is not None:
        club.country = club_data.country
    if club_data.region is not None:
        club.region = club_data.region
    if club_data.logo_url is not None:
        club.logo_url = club_data.logo_url
    
    db.commit()
    db.refresh(club)
    
    president = db.query(User).filter(User.id == club.president_id).first()
    judges_count = db.query(ClubJudge).filter(ClubJudge.club_id == club.id).count()
    
    return {
        "id": club.id,
        "title": club.title,
        "city": club.city,
        "description": club.description,
        "country": club.country,
        "region": club.region,
        "logo_url": club.logo_url,
        "president_id": club.president_id,
        "president_name": president.username if president else None,
        "judges_count": judges_count,
        "is_official": club.is_official,
        "created_at": club.created_at,
    }

@router.post("/{club_id}/upload-logo")
async def upload_club_logo(
    club_id: int,
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Клуб не найден")
    
    if club.president_id != user.id:
        raise HTTPException(status_code=403, detail="Только президент может менять логотип")
    
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"club_{club_id}_{datetime.now().timestamp()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logo_url = f"http://161.104.46.234:8001/uploads/avatars/{filename}"
    club.logo_url = logo_url
    db.commit()
    
    return {"logo_url": logo_url}