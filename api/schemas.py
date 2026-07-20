from datetime import datetime

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


class RegistroRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # max_length=72: bcrypt ignora en silencio todo lo que pase el byte 72 de la clave;
    # se limita aca para que el usuario no crea que eligio una clave mas larga de lo
    # que realmente se usa.
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("username")
    @classmethod
    def username_sin_espacios_extra(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El usuario debe tener al menos 3 caracteres (sin contar espacios)")
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PrediccionGuardada(BaseModel):
    id: int
    fecha: datetime
    titulo: str
    autor: str
    tema: str
    n_afirmativo: int
    n_negativo: int
    n_abstencion: int
