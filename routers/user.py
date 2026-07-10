from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from models.db import User
from core.database import get_db
from core.security import decode_token
import shutil
import os

router = APIRouter()

UPLOAD_DIR = "/root/mafia_excel_api/uploads/avatars"

# Создаём папку, если её нет
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-avatar")
async def upload_avatar(
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    # Сохраняем файл
    filename = f"{user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Сохраняем URL в БД
    avatar_url = f"http://161.104.46.234:8001/uploads/avatars/{filename}"
    user.avatar_url = avatar_url
    db.commit()
    
    return {"avatar_url": avatar_url}

# ============================================================
# СХЕМЫ
# ============================================================

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    avatar_url: Optional[str] = None  # ✅ ДОБАВИТЬ

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
# ЭНДПОИНТЫ
# ============================================================

# ---------- ОБНОВИТЬ ПРОФИЛЬ ----------
@router.put("/profile")
async def update_profile(
    data: UserUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    if data.nickname is not None:
        # Проверяем, что никнейм не занят
        existing = db.query(User).filter(
            User.username == data.nickname,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Этот никнейм уже занят")
        user.username = data.nickname
    
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.country is not None:
        user.country = data.country
    if data.city is not None:
        user.city = data.city
    if data.region is not None:
        user.region = data.region
    if data.avatar_url is not None:  # ✅ ДОБАВИТЬ
        user.avatar_url = data.avatar_url
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "country": user.country,
        "city": user.city,
        "region": user.region,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "phone": user.phone,
        "phone_verified": user.phone_verified,
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at,
    }

# ---------- ПОЛУЧИТЬ ПРОФИЛЬ ----------
@router.get("/profile")
async def get_profile(
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "country": user.country,
        "city": user.city,
        "region": user.region,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "phone": user.phone,
        "phone_verified": user.phone_verified,
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at,
    }
