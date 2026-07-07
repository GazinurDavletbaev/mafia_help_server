from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_protocol():
    return {"message": "Protocol generation (Excel) - будет перенесено позже"}
