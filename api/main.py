import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from api import modelo
from api.db import SessionLocal, engine
from api.db import Base as _Base
from api.routers import auth, diputados, historial, predecir
from api.seguridad import hashear_clave
from api.tablas import Usuario


def _sembrar_usuario_prueba() -> None:
    """Crea el usuario de prueba (credenciales del .env) solo si no existe todavia --
    idempotente, para no duplicarlo en cada reinicio del servidor."""
    username = os.environ.get("USUARIO_PRUEBA")
    password = os.environ.get("CLAVE_PRUEBA")
    if not username or not password:
        return

    db = SessionLocal()
    try:
        ya_existe = db.query(Usuario).filter(Usuario.username == username).one_or_none()
        if ya_existe is None:
            db.add(Usuario(username=username, password_hash=hashear_clave(password)))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas de usuarios/predicciones si no existen todavia.
    _Base.metadata.create_all(engine)
    _sembrar_usuario_prueba()

    # Carga el modelo, el KMeans y el embedder una sola vez al iniciar el servidor,
    # asi el primer pedido no paga el costo de cargarlos.
    modelo.precargar_artefactos()
    yield


app = FastAPI(
    title="LegisTrack API",
    description=(
        "Historial de votaciones y prediccion de voto de los diputados de la Camara de "
        "Diputados de Argentina."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(diputados.router)
app.include_router(predecir.router)
app.include_router(historial.router)


@app.get("/")
def raiz():
    return {"status": "ok", "servicio": "LegisTrack API"}
