from pydantic import BaseModel, Field, field_validator


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

    @field_validator("titulo")
    @classmethod
    def titulo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El titulo no puede estar vacio")
        return v


class PrediccionDiputado(BaseModel):
    diputado: str
    bloque: str
    voto_predicho: str


class PrediccionResponse(BaseModel):
    titulo: str
    tema_asignado: str
    predicciones: list[PrediccionDiputado]
