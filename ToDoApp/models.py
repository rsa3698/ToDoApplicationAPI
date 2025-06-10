from sqlalchemy import ForeignKey, Integer, String, Boolean, Column
from .database import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String, nullable=True)  # Optional field for phone number

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)  # Default priority set to 1
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))  # Foreign key to Users table

    def __str__(self):
        return f"Todos(id={self.id}, title={self.title}, complete={self.complete})"