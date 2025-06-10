from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
POSTGRESQL_DATABASE_URL = "postgresql://postgres:1234@localhost/ToDoApplicationDatabase"
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(db_url: str = POSTGRESQL_DATABASE_URL):
    global engine
    global SessionLocal
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example of how to initialize (call this from main.py or similar)
# if __name__ == '__main__':
#     init_db()