from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import decode_token
from models.db import User

def get_current_user(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user