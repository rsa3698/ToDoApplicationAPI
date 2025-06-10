from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .. import models
from passlib.context import CryptContext
from ..database import SessionLocal  # Adjust the import path as needed
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt

SECRET_KEY = "8fe520e9940e506b7399e0e8a66e310d45d5a788e218e10846246b187b05bd15"
ALGORITHM = "HS256"
router = APIRouter(
    prefix= "/auth",
    tags=["Authentication"],
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="The username of the user")
    password: str = Field(min_length=6, max_length=100, description="The password of the user")
    email: str = Field(min_length=5, max_length=100, description="The email of the user")
    first_name: str = Field(min_length=1, max_length=50, description="The first name of the user")
    last_name: str = Field(min_length=1, max_length=50, description="The last name of the user")    
    role: str
    phone_number: str = Field(min_length=10, max_length=15, description="The phone number of the user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "password": "password123",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "phone_number": "1234567890"
            }
        }
    }

class UserResponse(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.Users).filter(models.Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id:int, role: str, expires_delta: timedelta):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role
    }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/", status_code=201, response_model=UserResponse)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = models.Users (
        username=create_user_request.username,
        hashed_password= bcrypt_context.hash(create_user_request.password),
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True  
    )

    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)

   
    return UserResponse(
        username=create_user_model.username,
        email=create_user_model.email,
        first_name=create_user_model.first_name,
        last_name=create_user_model.last_name,
        role=create_user_model.role
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return {
            "username": username,
            "id": user_id,
            "role": user_role
        }
    except jwt.JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    

@router.post("/token", response_model=Token, status_code=200)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=30)  # Token valid for 30 minutes
    )
    return {"access_token": token, "token_type": "bearer"}