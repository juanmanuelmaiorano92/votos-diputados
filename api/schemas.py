from pydantic import BaseModel, Field, field_validator


class DiputadoResumen(BaseModel):
    diputado: str
    bloque: str


class VotacionHistorial(BaseModel):
    titulo: str
    fecha: str
    voto: str


class ConteoVotos(BaseModel):
    AFIRMATIVO: int
    NEGATIVO: int
    ABSTENCION: int


class DiputadoHistorial(BaseModel):
    diputado: str
    bloque: str
    provincia: str
    conteo_votos: ConteoVotos
    ultimas_votaciones: list[VotacionHistorial]


class PrediccionRequest(BaseModel):
    titulo: str = Field(..., min_length=1, description="Titulo del proyecto de ley a predecir")
    autor: str = Field(
        ...,
        min_length=1,
        description=(
            "Autor del proyecto: el nombre canonico de uno de los 257 diputados actuales "
            "(el que devuelve GET /diputados) o 'Poder Ejecutivo Nacional'."
        ),
    )

    @field_validator("titulo", "autor")
    @classmethod
    def campo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacio")
        return v


class PrediccionDiputado(BaseModel):
    diputado: str
    bloque: str
    voto_predicho: str


class PrediccionResponse(BaseModel):
    titulo: str
    autor: str
    bloque_autor: str
    tema_asignado: str
    predicciones: list[PrediccionDiputado]
