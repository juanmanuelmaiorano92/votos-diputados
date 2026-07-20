from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    fecha_alta: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora_utc)

    predicciones: Mapped[list["Prediccion"]] = relationship(back_populates="usuario")


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora_utc)
    titulo: Mapped[str] = mapped_column(String)
    autor: Mapped[str] = mapped_column(String)
    tema: Mapped[str] = mapped_column(String)
    n_afirmativo: Mapped[int] = mapped_column(Integer)
    n_negativo: Mapped[int] = mapped_column(Integer)
    n_abstencion: Mapped[int] = mapped_column(Integer)

    usuario: Mapped["Usuario"] = relationship(back_populates="predicciones")
