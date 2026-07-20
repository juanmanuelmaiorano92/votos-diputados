import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _url_base_datos() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta la variable de entorno DATABASE_URL")
    return url


# pool_pre_ping evita errores por conexiones que Supabase cierra por inactividad
# (el pooler externo ya administra el pool de conexiones del lado del servidor).
engine = create_engine(_url_base_datos(), pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
