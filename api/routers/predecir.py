from fastapi import APIRouter, HTTPException

from api import modelo
from api.schemas import PrediccionDiputado, PrediccionRequest, PrediccionResponse

router = APIRouter(tags=["predecir"])


@router.post("/predecir", response_model=PrediccionResponse)
def predecir(request: PrediccionRequest):
    try:
        predicciones, tema_id, tema_label, bloque_autor = modelo.predecir_votos(
            request.titulo, request.autor
        )
    except modelo.AutorInvalidoError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return PrediccionResponse(
        titulo=request.titulo,
        autor=request.autor,
        bloque_autor=bloque_autor,
        tema_asignado=tema_label,
        predicciones=[PrediccionDiputado(**p) for p in predicciones],
    )
