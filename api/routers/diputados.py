from fastapi import APIRouter, Depends, HTTPException

from api import database as db
from api.schemas import DiputadoHistorial, DiputadoResumen
from api.seguridad import usuario_actual

router = APIRouter(
    prefix="/diputados", tags=["diputados"], dependencies=[Depends(usuario_actual)]
)


@router.get("", response_model=list[DiputadoResumen])
def listar_diputados():
    """Nombre y bloque actual de los 257 diputados, para poblar los selectores de la app
    sin leer el CSV."""
    return db.listar_diputados()


@router.get("/{id}", response_model=DiputadoHistorial)
def obtener_diputado(id: str):
    """El 'id' es el nombre completo del diputado (los datos no tienen un ID numerico)."""
    historial = db.obtener_historial_diputado(id)
    if historial is None:
        raise HTTPException(status_code=404, detail=f"No se encontro al diputado '{id}'")
    return historial
