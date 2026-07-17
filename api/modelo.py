import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from api import database as db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Mismas columnas META/TARGET que STG_6/STG_8 usan para definir el orden de las features
META = ["diputado", "titulo_base", "fecha_votacion", "bloque", "provincia", "tema_label"]
TARGET = "voto"


@lru_cache(maxsize=1)
def _orden_features() -> list[str]:
    """Orden exacto de columnas que espera el modelo (el mismo que uso al entrenarse)."""
    columnas = pd.read_csv(DATA_DIR / "df_entrenamiento.csv", nrows=0).columns
    return [c for c in columnas if c not in META + [TARGET]]


@lru_cache(maxsize=1)
def cargar_modelo():
    return joblib.load(DATA_DIR / "modelo_lgbm.joblib")


@lru_cache(maxsize=1)
def cargar_le_voto():
    return joblib.load(DATA_DIR / "le_voto.joblib")


@lru_cache(maxsize=1)
def _cargar_kmeans():
    return joblib.load(DATA_DIR / "kmeans_temas.joblib")


@lru_cache(maxsize=1)
def _cargar_mapa_temas() -> dict[int, str]:
    with open(DATA_DIR / "mapa_temas.json", encoding="utf-8") as f:
        mapa = json.load(f)
    return {int(k): v for k, v in mapa.items()}


@lru_cache(maxsize=1)
def _cargar_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def _asignar_tema(embedding: np.ndarray) -> tuple[int, str]:
    """Asigna el cluster mas cercano con .predict() — nunca se reajusta el KMeans."""
    kmeans = _cargar_kmeans()
    tema_id = int(kmeans.predict(embedding.reshape(1, -1))[0])
    tema_label = _cargar_mapa_temas().get(tema_id, "desconocido")
    return tema_id, tema_label


def construir_features(titulo: str) -> tuple[pd.DataFrame, pd.DataFrame, int, str]:
    """Arma el vector de features de los 394 que espera el modelo, una fila por diputado,
    a partir de un titulo de ley nuevo. Si en el futuro se agrega una feature al modelo,
    esta es la unica funcion que hay que actualizar (ademas del reentrenamiento).

    Devuelve (X, meta, tema_id, tema_label): X son las features en el orden que el modelo
    espera; meta trae diputado y bloque, en el mismo orden de filas que X.
    """
    embedder = _cargar_embedder()
    # float64: mismo dtype que los embeddings leidos desde CSV con los que se entrenaron
    # el KMeans (STG_4/T4) y el LGBM (STG_6/T2) -- sentence-transformers devuelve float32
    # por defecto, y mezclar dtypes rompe el predict() de KMeans (buffer dtype mismatch).
    embedding = np.asarray(embedder.encode(titulo), dtype=np.float64)
    tema_id, tema_label = _asignar_tema(embedding)

    snap_dip = db.cargar_snapshot_diputado().copy()
    snap_tema = db.cargar_snapshot_diputado_tema()
    snap_bloque_tema = db.cargar_snapshot_bloque_tema()

    # Tasa del diputado en el tema asignado (NaN si nunca voto sobre ese tema)
    snap_dip = snap_dip.merge(
        snap_tema.loc[snap_tema["tema_id"] == tema_id, ["diputado", "tasa_afirmativo_tema_hist"]],
        on="diputado",
        how="left",
    )

    # Tasa del bloque en el tema asignado (NaN si el bloque nunca voto sobre ese tema)
    snap_dip = snap_dip.merge(
        snap_bloque_tema.loc[snap_bloque_tema["tema_id"] == tema_id, ["bloque", "tasa_afirmativo_bloque_tema"]],
        on="bloque",
        how="left",
    )

    # Cascada de relleno identica a STG_5: tema/ventana/bloque-tema -> tasa individual del diputado -> 0.5 neutro
    for col in ["tasa_afirmativo_tema_hist", "tasa_afirmativo_desde_2023",
                "tasa_afirmativo_2026", "tasa_afirmativo_bloque_tema"]:
        snap_dip[col] = snap_dip[col].fillna(snap_dip["tasa_afirmativo_hist"])
    for col in ["tasa_afirmativo_hist", "tasa_afirmativo_tema_hist", "tasa_alineacion_bloque_hist",
                "tasa_afirmativo_desde_2023", "tasa_afirmativo_2026", "tasa_afirmativo_bloque_tema"]:
        snap_dip[col] = snap_dip[col].fillna(0.5)

    orden = _orden_features()
    emb_cols = [c for c in orden if c.startswith("emb_")]
    emb_df = pd.DataFrame(
        np.tile(embedding, (len(snap_dip), 1)), columns=emb_cols, index=snap_dip.index
    )

    tabla = pd.concat([snap_dip, emb_df], axis=1)
    tabla["tema_id"] = tema_id

    X = tabla[orden]
    meta = tabla[["diputado", "bloque"]].reset_index(drop=True)
    return X, meta, tema_id, tema_label


def precargar_artefactos() -> None:
    """Fuerza la carga de todos los artefactos pesados (modelo, KMeans, embedder, datos)
    una sola vez, para llamarla al iniciar la API y que el primer pedido no tenga que
    esperar."""
    cargar_modelo()
    cargar_le_voto()
    _cargar_kmeans()
    _cargar_mapa_temas()
    _cargar_embedder()
    _orden_features()
    db.cargar_consolidado()
    db.cargar_snapshot_diputado()
    db.cargar_snapshot_diputado_tema()
    db.cargar_snapshot_bloque_tema()


def predecir_votos(titulo: str) -> tuple[list[dict], int, str]:
    """Predice el voto de todos los diputados del snapshot para un titulo de ley nuevo."""
    X, meta, tema_id, tema_label = construir_features(titulo)

    modelo = cargar_modelo()
    le_voto = cargar_le_voto()

    pred_enc = modelo.predict(X.values)
    votos = le_voto.inverse_transform(pred_enc)

    predicciones = [
        {"diputado": diputado, "bloque": bloque, "voto_predicho": voto}
        for diputado, bloque, voto in zip(meta["diputado"], meta["bloque"], votos)
    ]
    return predicciones, tema_id, tema_label
