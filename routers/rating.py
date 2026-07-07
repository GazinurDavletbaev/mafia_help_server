from fastapi import APIRouter

router = APIRouter()

@router.get("/players")
async def get_player_rating():
    return {"message": "Player rating - будет реализовано позже"}

@router.get("/clubs")
async def get_club_rating():
    return {"message": "Club rating - будет реализовано позже"}
