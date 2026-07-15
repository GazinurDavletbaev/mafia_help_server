from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import auth, games, rating, protocol, clubs, user

app = FastAPI(title="Mafia API", version="1.0.0")
app.mount("/uploads", StaticFiles(directory="/root/mafia_excel_api/uploads"), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clubs_router, prefix="/games", tags=["games"])
app.include_router(rating.router, prefix="/rating", tags=["rating"])
app.include_router(protocol.router, prefix="/protocol", tags=["protocol"])
app.include_router(clubs.router, prefix="/clubs", tags=["clubs"])
app.include_router(user.router, prefix="/user", tags=["user"])

@app.get("/")
async def root():
    return {"message": "Mafia API работает"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)