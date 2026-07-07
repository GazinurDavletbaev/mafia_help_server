from fastapi import APIRouter

router = APIRouter()

@router.post("/save")
async def save_game():
    return {"message": "Save game - будет реализовано позже"}

@router.get("/history/{club_id}")
async def get_history(club_id: int):
    return {"message": f"History for club {club_id} - будет реализовано позже"}
