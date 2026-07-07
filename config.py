import os

DATABASE_URL = "postgresql://mafia_user:abrakadabra@localhost/mafia_db"
SECRET_KEY = "abrakadabra"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
