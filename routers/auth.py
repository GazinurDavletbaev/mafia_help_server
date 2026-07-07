import secrets
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr  # ✅ ДОБАВИТЬ
from models.db import User
from models.schemas import (
    UserRegister, UserLogin, Token, UserResponse,
    PhoneSendCodeRequest, PhoneVerifyRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
)
from core.database import get_db
from core.security import get_password_hash, verify_password, create_access_token, decode_token
from core.email import send_verification_email, send_reset_code_email  # ✅ ДОБАВИТЬ send_reset_code_email
from config import ACCESS_TOKEN_EXPIRE_MINUTES

ERROR_MESSAGES = {
    "email_registered": "Пользователь с таким email уже зарегистрирован.",
    "username_taken": "Этот никнейм уже занят. Пожалуйста, выберите другой.",
    "email_not_found": "Пользователь с таким email не найден.",
    "invalid_credentials": "Неверный email или пароль.",
    "invalid_phone": "Пожалуйста, введите корректный номер телефона.",
    "phone_verified": "Этот номер телефона уже подтвержден.",
    "email_not_verified": "Подтвердите email. Проверьте почту или запросите новое письмо.",
    "invalid_verification_token": "Ссылка для подтверждения недействительна или устарела.",
    "token_expired": "Срок действия ссылки истёк. Запросите новое письмо.",
    "passwords_do_not_match": "Пароли не совпадают.",
    "password_too_short": "Пароль должен быть не менее 6 символов.",
    "missing_fields": "Пожалуйста, заполните все обязательные поля.",
    "invalid_email_format": "Неверный формат email.",
    "user_not_found": "Пользователь не найден.",
    "reset_token_invalid": "Недействительный или устаревший токен для сброса пароля.",
    "reset_link_expired": "Срок действия ссылки для сброса пароля истёк.",
    "old_password_incorrect": "Неверно указан текущий пароль.",
    "phone_taken": "Этот номер телефона уже привязан к другому аккаунту.",
    "user_already_exists": "Пользователь с такими данными уже существует.",
    "verification_already_sent": "Письмо с подтверждением уже было отправлено. Попробуйте позже.",
}

router = APIRouter()

# ========== РЕГИСТРАЦИЯ ==========
@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    print("=" * 60)
    print("📝 РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ")
    print("=" * 60)
    print(f"📧 Email: {user_data.email}")
    print(f"👤 Username: {user_data.username}")
    print(f"📱 Phone: {user_data.phone}")

    if not user_data.email or not user_data.username or not user_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES["missing_fields"]
        )

    # Проверка существующего email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES["email_registered"]
        )

    # Проверка существующего никнейма
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES["username_taken"]
        )

    # Проверка длины пароля
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES["password_too_short"]
        )
    # Проверка email
    if db.query(User).filter(User.email == user_data.email).first():
        print("❌ Email уже занят")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        print("❌ Username уже занят")
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Создаём пользователя
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Пользователь создан с ID: {user.id}")

    # Генерируем токен подтверждения
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    user.verification_token = token
    user.verification_token_expires = expires
    user.verification_token_used = False
    db.commit()
    print(f"🔑 Токен подтверждения: {token}")

    # Отправляем письмо
    print("📧 Вызываю send_verification_email...")
    email_sent = send_verification_email(user.email, token)
    
    if email_sent:
        print("✅ Письмо отправлено успешно")
    else:
        print("❌ Письмо НЕ отправлено")

    # JWT токен
    token_data = {"sub": str(user.id), "email": user.email, "username": user.username}
    jwt_token = create_access_token(token_data)
    print("✅ JWT токен создан")
    print("=" * 60)

    return {"access_token": jwt_token, "token_type": "bearer"}

# ========== ЛОГИН ==========
@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES["invalid_credentials"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES["invalid_credentials"],
            headers={"WWW-Authenticate": "Bearer"},    
    )
    token_data = {"sub": str(db_user.id), "email": db_user.email, "username": db_user.username}
    jwt_token = create_access_token(token_data)
    
    return {"access_token": jwt_token, "token_type": "bearer"}

# ========== ОТПРАВКА КОДА НА ТЕЛЕФОН ==========
@router.post("/phone/send-code")
async def send_phone_code(request: PhoneSendCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == request.phone).first()
    
    if user and user.phone_verified:
        raise HTTPException(status_code=400, detail="Phone already verified")
    
    otp = str(secrets.randbelow(1000000)).zfill(6)
    expires = datetime.utcnow() + timedelta(minutes=5)
    
    if user:
        user.otp_code = otp
        user.otp_expires = expires
        user.otp_attempts = 0
        db.commit()
    else:
        new_user = User(
            phone=request.phone,
            otp_code=otp,
            otp_expires=expires,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    
    print(f"📱 Код для {request.phone}: {otp}")
    return {"message": "Code sent", "phone": request.phone}

# ========== ПРОВЕРКА КОДА ТЕЛЕФОНА ==========
@router.post("/phone/verify")
async def verify_phone(request: PhoneVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.otp_attempts >= 5:
        raise HTTPException(status_code=400, detail="Too many attempts. Request new code.")
    
    if user.otp_code != request.code:
        user.otp_attempts += 1
        user.otp_last_attempt = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")
    
    if user.otp_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")
    
    user.phone_verified = True
    user.phone_verified_at = datetime.utcnow()
    user.otp_code = None
    user.otp_expires = None
    user.otp_attempts = 0
    db.commit()
    
    token_data = {"sub": str(user.id), "phone": user.phone}
    jwt_token = create_access_token(token_data)
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "phone_verified": user.phone_verified,
            "is_email_verified": user.is_email_verified,
            "username": user.username,
        }
    }

# ========== ОТПРАВКА ПОДТВЕРЖДЕНИЯ EMAIL ==========
@router.post("/send-verification")
async def send_verification_email_request(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    user.verification_token = token
    user.verification_token_expires = expires
    user.verification_token_used = False
    db.commit()
    
    success = send_verification_email(user.email, token)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    return {"message": "Verification email sent"}

# ========== ПРОВЕРКА EMAIL ==========
@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    if user.verification_token_used:
        raise HTTPException(status_code=400, detail="Token already used")
    
    if user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
    
    user.is_email_verified = True
    user.email_verified_at = datetime.utcnow()
    user.verification_token_used = True
    db.commit()
    
    return {"message": "Email verified successfully"}

# ========== ПРОФИЛЬ ==========
@router.get("/me", response_model=UserResponse)
async def get_me(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ========== ЗАБЫЛИ ПАРОЛЬ ==========
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Генерируем 6-значный код
    code = f"{random.randint(100000, 999999)}"
    expires = datetime.utcnow() + timedelta(minutes=15)
    
    user.reset_code = code
    user.reset_code_expires = expires
    user.reset_code_attempts = 0
    db.commit()
    
    # ✅ ОТПРАВКА КОДА В ПИСЬМЕ
    send_reset_code_email(user.email, code)
    
    print(f"🔑 Код сброса для {request.email}: {code}")
    return {"message": "Код отправлен на почту"}

# ========== МОДЕЛЬ ДЛЯ ПРОВЕРКИ КОДА ==========
class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str

# ========== ПРОВЕРКА КОДА ==========
@router.post("/verify-reset-code")
async def verify_reset_code(request: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.reset_code:
        raise HTTPException(status_code=400, detail="Код не запрошен")
    
    if user.reset_code_attempts >= 5:
        raise HTTPException(status_code=400, detail="Слишком много попыток")
    
    if user.reset_code_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Код истёк")
    
    if user.reset_code != request.code:
        user.reset_code_attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Неверный код")
    
    # ✅ Код верный — генерируем токен для сброса
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    user.reset_code = None  # Очищаем код
    user.reset_code_attempts = 0
    db.commit()
    
    return {"reset_token": token}

# ========== СБРОС ПАРОЛЯ ==========
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Недействительный токен")
    
    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Токен истёк")
    
    user.password_hash = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Пароль успешно изменён"}

# ========== ИЗМЕНЕНИЕ ПАРОЛЯ ==========
@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    token: str,
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid old password")
    
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}