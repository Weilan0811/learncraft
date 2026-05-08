from sqlmodel import Session, create_engine

from app.core.config import get_settings


settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=settings.db_log_echo, future=True)


def get_session():
    with Session(engine) as session:
        yield session
