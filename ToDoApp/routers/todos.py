from fastapi import APIRouter,Depends, HTTPException, status, Path
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import models
from database import SessionLocal
from .auth import get_current_user


router = APIRouter()


def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=100, description="The title of the todo item")
    description: str = Field(min_length=3, max_length=500, description="The description of the todo item")
    priority: int = Field(gt=0, le=6,description="The priority of the todo item (1-6)")
    complete: bool = False

@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    todos = db.query(models.TodoS).filter(models.TodoS.owner_id == user.get("id")).all()
    if not todos:
        return {"message": "No todos found."}
    return todos


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0, description="The ID of the todo item to retrieve")):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = db.query(models.TodoS).filter(models.TodoS.id == todo_id, models.TodoS.owner_id == user.get("id")).first()
    if todo_model:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")

@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, todo: TodoRequest, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = models.TodoS(**todo.dict(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_dependency,
    todo_request: TodoRequest,
    db: db_dependency,
    todo_id: int = Path(gt=0, description="The ID of the todo item to update")
):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = db.query(models.TodoS).filter(models.TodoS.id == todo_id, models.TodoS.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.commit()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(gt=0, description="The ID of the todo item to delete")
):
    todo_model = db.query(models.TodoS).filter(models.TodoS.id == todo_id, models.TodoS.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo_model)
    db.commit()