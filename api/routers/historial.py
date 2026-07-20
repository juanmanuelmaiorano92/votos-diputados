from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import PrediccionGuardada
from api.seguridad import usuario_actual
from api.tablas import Prediccion, Usuario

router = APIRouter(tags=["historial"])


@router.get("/mis-predicciones", response_model=list[PrediccionGuardada])
def mis_predicciones(
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    predicciones = (
        db.query(Prediccion)
        .filter(Prediccion.usuario_id == usuario.id)
        .order_by(Prediccion.fecha.desc())
        .all()
    )
    return predicciones
