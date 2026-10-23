import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "secpulse.db"
_DB_PATH = Path(os.getenv("SECPULSE_DB_PATH", str(_DEFAULT_DB_PATH))).expanduser()
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# URL.create handles platform-specific path escaping (including Windows paths).
SQLALCHEMY_DATABASE_URL = URL.create("sqlite", database=str(_DB_PATH))
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
