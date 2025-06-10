from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth, todos, admin, users


app = FastAPI()

def create_db_and_tables():
    models.Base.metadata.create_all(bind=engine)

# app.add_event_handler("startup", create_db_and_tables)

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

