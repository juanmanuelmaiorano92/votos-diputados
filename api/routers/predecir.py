from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import modelo
from api.db import get_db
from api.schemas import PrediccionDiputado, PrediccionRequest, PrediccionResponse
from api.seguridad import usuario_actual
from api.tablas import Prediccion, Usuario

router = APIRouter(tags=["predecir"])


def _guardar_historial(
    db: Session, usuario: Usuario, request: PrediccionRequest, tema_label: str, predicciones: list[dict]
) -> None:
    """Cuenta los votos de la lista YA devuelta por el modelo (datos genericos: solo mira
    la clave 'voto_predicho') y guarda un resumen en la base. No conoce nada interno del
    modelo -- si el modelo cambia, esta funcion sigue sirviendo igual."""
    conteo = Counter(p["voto_predicho"] for p in predicciones)
    fila = Prediccion(
        usuario_id=usuario.id,
        titulo=request.titulo,
        autor=request.autor,
        tema=tema_label,
        n_afirmativo=conteo.get("AFIRMATIVO", 0),
        n_negativo=conteo.get("NEGATIVO", 0),
        n_abstencion=conteo.get("ABSTENCION", conteo.get("ABSTENCIÓN", 0)),
    )
    db.add(fila)
    db.commit()


@router.post("/predecir", response_model=PrediccionResponse)
def predecir(
    request: PrediccionRequest,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    try:
        predicciones, tema_id, tema_label, bloque_autor = modelo.predecir_votos(
            request.titulo, request.autor
        )
    except modelo.AutorInvalidoError as e:
        raise HTTPException(status_code=422, detail=str(e))

    _guardar_historial(db, usuario, request, tema_label, predicciones)

    return PrediccionResponse(
        titulo=request.titulo,
        autor=request.autor,
        bloque_autor=bloque_autor,
        tema_asignado=tema_label,
        predicciones=[PrediccionDiputado(**p) for p in predicciones],
    )
