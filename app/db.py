import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.secrets import get_secret

# 1. Try to obtain the complete DATABASE_URL first.
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. If no DATABASE_URL is found, then obtain DB parameters separately. 
#    priority: environment variables/K8s -> secrets.py -> default values
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER") or get_secret("DB_USER") or "app_user"
    DB_PASSWORD = os.getenv("DB_PASSWORD") or get_secret("DB_PASSWORD") or "UserPassword123!"
    DB_HOST = os.getenv("DB_HOST") or get_secret("DB_HOST") or "127.0.0.1"
    DB_PORT = os.getenv("DB_PORT") or get_secret("DB_PORT") or "3306"
    DB_NAME = os.getenv("DB_NAME") or get_secret("DB_NAME") or "inventory_db"
    
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3. Create engine (plus pool_pre_ping to ensure stable connection)
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()