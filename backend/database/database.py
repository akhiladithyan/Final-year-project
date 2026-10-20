from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import config

engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for API routes to obtain a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
