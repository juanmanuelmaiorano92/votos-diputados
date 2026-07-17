from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import modelo
from api.routers import diputados, predecir


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(diputados.router)
app.include_router(predecir.router)


@app.get("/")
def raiz():
    return {"status": "ok", "servicio": "LegisTrack API"}
