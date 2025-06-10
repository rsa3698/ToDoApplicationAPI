from fastapi import APIRouter,Depends, HTTPException, status, Path
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .. import models
from ..database import SessionLocal
from .auth import get_current_user


router = APIRouter(
    prefix= "/admin",
    tags=["Admin"],
)


def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query(models.Todos).all()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(gt=0, description="The ID of the todo item to delete")
):
    if user is None or user.get("role", "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if not todo_model:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(todo_model)
    db.commit()

