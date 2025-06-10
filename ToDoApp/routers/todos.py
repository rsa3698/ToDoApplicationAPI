from fastapi import APIRouter,Depends, HTTPException, status, Path
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .. import models
from ..database import SessionLocal
from .auth import get_current_user


router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)


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
    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()
    if not todos:
        return {"message": "No todos found."}
    return todos


@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0, description="The ID of the todo item to retrieve")):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).first()
    if todo_model:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found")

@router.post("/", status_code=status.HTTP_201_CREATED) # Changed path from /todo to /
async def create_todo(user: user_dependency, todo: TodoRequest, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = models.Todos(**todo.model_dump(), owner_id=user.get("id")) # Changed todo.dict() to todo.model_dump() for Pydantic v2
    db.add(todo_model)
    db.commit()
    # Return the created todo item, as per common REST API practice and test expectations
    # The test expects a 201 response with the created item.
    # Refresh to get DB-assigned values like ID.
    db.refresh(todo_model)
    return todo_model


@router.put("/{todo_id}", status_code=status.HTTP_200_OK) # Changed /todo/{todo_id} to /{todo_id} and 204 to 200 to return content
async def update_todo(
    user: user_dependency,
    todo_request: TodoRequest,
    db: db_dependency,
    todo_id: int = Path(gt=0, description="The ID of the todo item to update")
):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.commit()
    db.refresh(todo_model)
    return todo_model

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT) # Changed /todo/{todo_id} to /{todo_id}
async def delete_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(gt=0, description="The ID of the todo item to delete")
):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo_model)
    db.commit()