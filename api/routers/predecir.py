from fastapi import APIRouter

from api import modelo
from api.schemas import PrediccionDiputado, PrediccionRequest, PrediccionResponse

router = APIRouter(tags=["predecir"])


@router.post("/predecir", response_model=PrediccionResponse)
def predecir(request: PrediccionRequest):
    predicciones, tema_id, tema_label = modelo.predecir_votos(request.titulo)
    return PrediccionResponse(
        titulo=request.titulo,
        tema_asignado=tema_label,
        predicciones=[PrediccionDiputado(**p) for p in predicciones],
    )
