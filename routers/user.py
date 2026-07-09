# routers/users.py
from pydantic import BaseModel
from typing import Optional

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None

@router.put("/users/profile")
async def update_profile(
    data: UserUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    if data.nickname is not None:
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
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "nickname": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "country": user.country,
        "city": user.city,
        "region": user.region,
        "avatar_url": user.avatar_url,
    }