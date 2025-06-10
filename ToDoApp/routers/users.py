from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext

from models import Users
from database import SessionLocal
from .auth import get_current_user, db_dependency

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

class UpdatePhoneRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15, description="The new phone number")

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_user(user: Annotated[dict, Depends(get_current_user)], db: db_dependency):
    user_model = db.query(Users).filter(Users.id == user["id"]).first()
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user_model.id,
        "username": user_model.username,
        "email": user_model.email,
        "first_name": user_model.first_name,
        "last_name": user_model.last_name,
        "role": user_model.role,
        "is_active": user_model.is_active,
        "phone_number": user_model.phone_number
    }

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user: Annotated[dict, Depends(get_current_user)],
    db: db_dependency,
    passwords: ChangePasswordRequest
):
    user_model = db.query(Users).filter(Users.id == user["id"]).first()
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt_context.verify(passwords.old_password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    user_model.hashed_password = bcrypt_context.hash(passwords.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.put("/phone", status_code=status.HTTP_200_OK)
async def update_phone_number(
    user: Annotated[dict, Depends(get_current_user)],
    db: db_dependency,
    phone_request: UpdatePhoneRequest
):
    user_model = db.query(Users).filter(Users.id == user["id"]).first()
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_model.phone_number = phone_request.phone_number
    db.commit()
    return {"message": "Phone number updated successfully"}