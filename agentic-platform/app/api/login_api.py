import jwt
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(data: LoginRequest):
    """Generate JWT token on successful login"""
    # 🔐 Replace with DB lookup later
    if data.username != "admin" or data.password != "admin123":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "username": data.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )

    return {"access_token": token, "token_type": "bearer"}