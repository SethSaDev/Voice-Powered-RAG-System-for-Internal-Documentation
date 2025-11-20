from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid

router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

@router.post("/register")
async def register(user_data: UserRegister):
    # Simplified registration endpoint
    return {"message": "User registered successfully", "user_id": str(uuid.uuid4())}

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    # Simplified login endpoint
    token = jwt.encode(
        {"sub": user_data.email, "exp": datetime.utcnow() + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return TokenResponse(access_token=token, expires_in=1800)
