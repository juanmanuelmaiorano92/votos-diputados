import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from api import database as db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOGGER = logging.getLogger(__name__)

AUTOR_PODER_EJECUTIVO = "Poder Ejecutivo Nacional"


class AutorInvalidoError(ValueError):
    """El autor recibido no es 'Poder Ejecutivo Nacional' ni un diputado de la nomina."""


def _normalizar_nombre(s) -> str:
    """Misma normalizacion que STG_5.2 (specs 011/012): es la que se uso para construir
    bloque_autor_norm / bloques_integrantes_norm / bloque_votante_norm al calcular
    es_oficialista y coincide_bloque_autor durante el entrenamiento. Hay que reproducirla
    tal cual para que la prediccion compare los bloques de la misma forma que el modelo
    aprendio."""
    if pd.isna(s):
        return ''
    s = str(s).upper().strip()
    s = s.replace('�', 'N')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(s.split())


def _normalizar_bloque_encoder(s) -> str:
    """Misma normalizacion que STG_5.3 (spec 013): es la que se uso para construir
    bloque_autor_norm, la columna sobre la que se ajusto encoder_bloque_autor.joblib.
    Es una funcion distinta de _normalizar_nombre (aunque el resultado practico coincide
    en casi todos los casos) para no romper la fidelidad con el fit original del encoder."""
    if pd.isna(s):
        return s
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')
    s = s.upper().strip()
    return re.sub(r'\s+', ' ', s)


@lru_cache(maxsize=1)
def _orden_features_autor() -> list[str]:
    """Orden exacto de las 398 features del Escenario A (spec 014 / STG_8.2). No se
    reconstruye leyendo el encabezado de un CSV: en STG_6.2 las columnas es_oficialista y
    coincide_bloque_autor se agregan AL FINAL de la lista, no en su posicion original, asi
    que leer el encabezado desalinearia esas dos columnas contra lo que el modelo aprendio."""
    with open(DATA_DIR / "orden_features_autor.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def cargar_modelo():
    return joblib.load(DATA_DIR / "modelo_lgbm_autor.joblib")


@lru_cache(maxsize=1)
def cargar_le_voto():
    return joblib.load(DATA_DIR / "le_voto_autor.joblib")


@lru_cache(maxsize=1)
def _cargar_encoder_bloque_autor():
    return joblib.load(DATA_DIR / "encoder_bloque_autor.joblib")


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


@lru_cache(maxsize=1)
def _cargar_periodos_presidenciales() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "tabla_periodos_presidenciales.csv",
        parse_dates=["fecha_inicio", "fecha_fin"],
    ).sort_values("fecha_inicio")


def _asignar_tema(embedding: np.ndarray) -> tuple[int, str]:
    """Asigna el cluster mas cercano con .predict() — nunca se reajusta el KMeans."""
    kmeans = _cargar_kmeans()
    tema_id = int(kmeans.predict(embedding.reshape(1, -1))[0])
    tema_label = _cargar_mapa_temas().get(tema_id, "desconocido")
    return tema_id, tema_label


def _periodo_vigente() -> pd.Series:
    """Periodo presidencial vigente HOY (no hardcodeado): el mas reciente cuyo fecha_inicio
    ya paso. Si algun dia la tabla queda desactualizada (hoy cae fuera de todos los periodos
    cargados, antes del primero o despues del ultimo), se usa igual el periodo mas cercano
    conocido y se deja una advertencia en el log en vez de romper la prediccion."""
    periodos = _cargar_periodos_presidenciales()
    hoy = pd.Timestamp.today().normalize()

    candidatos = periodos[periodos["fecha_inicio"] <= hoy]
    if candidatos.empty:
        fila = periodos.iloc[0]
        LOGGER.warning(
            "La fecha de hoy (%s) es anterior al primer periodo de "
            "tabla_periodos_presidenciales.csv; se usa el mas antiguo (%s, desde %s) como "
            "coalicion gobernante. Revisar el reloj del servidor o la tabla.",
            hoy.date(), fila["presidente"], fila["fecha_inicio"].date(),
        )
        return fila

    fila = candidatos.iloc[-1]
    if hoy > fila["fecha_fin"]:
        LOGGER.warning(
            "La fecha de hoy (%s) esta fuera de todos los periodos de "
            "tabla_periodos_presidenciales.csv; se usa el mas reciente (%s, vigente hasta "
            "%s) como coalicion gobernante. Actualizar la tabla.",
            hoy.date(), fila["presidente"], fila["fecha_fin"].date(),
        )
    return fila


def _resolver_autor(autor: str) -> dict:
    """Traduce el autor elegido en la app (un diputado de la nomina o 'Poder Ejecutivo
    Nacional') a las 4 features de autoria del Escenario A: bloque_autor, es_poder_ejecutivo,
    es_oficialista y el set de bloques_integrantes de la coalicion vigente (necesario para
    calcular coincide_bloque_autor cuando el autor es el Ejecutivo). Lanza
    AutorInvalidoError si el autor no es ninguna de las opciones validas."""
    fila_periodo = _periodo_vigente()
    coalicion_vigente = fila_periodo["coalicion"]
    bloques_integrantes_norm = {
        _normalizar_nombre(b) for b in fila_periodo["bloques_integrantes"].split(";")
    }

    if _normalizar_nombre(autor) == _normalizar_nombre(AUTOR_PODER_EJECUTIVO):
        bloque_autor = coalicion_vigente
        es_poder_ejecutivo = 1
        es_oficialista = 1
    else:
        nomina = db.cargar_nomina()
        fila_dip = nomina[nomina["diputado"] == autor]
        if fila_dip.empty:
            raise AutorInvalidoError(
                f"Autor invalido: '{autor}'. Debe ser '{AUTOR_PODER_EJECUTIVO}' o el nombre "
                "exacto de uno de los diputados que devuelve GET /diputados."
            )
        bloque_autor = fila_dip.iloc[0]["bloque_actual"]
        es_poder_ejecutivo = 0
        es_oficialista = int(_normalizar_nombre(bloque_autor) in bloques_integrantes_norm)

    enc_autor = _cargar_encoder_bloque_autor()
    bloque_autor_enc = int(
        enc_autor.transform([[_normalizar_bloque_encoder(bloque_autor)]])[0, 0]
    )

    return {
        "bloque_autor": bloque_autor,
        "bloque_autor_norm": _normalizar_nombre(bloque_autor),
        "bloque_autor_enc": bloque_autor_enc,
        "es_poder_ejecutivo": es_poder_ejecutivo,
        "es_oficialista": es_oficialista,
        "bloques_integrantes_norm": bloques_integrantes_norm,
    }


def construir_features(titulo: str, autor: str) -> tuple[pd.DataFrame, pd.DataFrame, int, str, str]:
    """Arma el vector de las 398 features del Escenario A, una fila por diputado, a partir
    de un titulo de ley nuevo y su autor. Si en el futuro se agrega una feature al modelo,
    esta es la unica funcion que hay que actualizar (ademas del reentrenamiento).

    Devuelve (X, meta, tema_id, tema_label, bloque_autor): X son las features en el orden
    que el modelo espera; meta trae diputado y bloque, en el mismo orden de filas que X;
    bloque_autor es el bloque asignado al autor elegido (para mostrar en la respuesta)."""
    embedder = _cargar_embedder()
    # float64: mismo dtype que los embeddings leidos desde CSV con los que se entrenaron
    # el KMeans y el LGBM -- sentence-transformers devuelve float32 por defecto, y mezclar
    # dtypes rompe el predict() de KMeans (buffer dtype mismatch, bug ya visto en spec 010).
    embedding = np.asarray(embedder.encode(titulo), dtype=np.float64)
    tema_id, tema_label = _asignar_tema(embedding)

    resolucion_autor = _resolver_autor(autor)

    snap_dip = db.cargar_snapshot_diputado_autor().copy()
    snap_tema = db.cargar_snapshot_diputado_tema_autor()
    snap_bloque_tema = db.cargar_snapshot_bloque_tema_autor()

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

    # Cascada de relleno identica a STG_5/STG_8: tema/ventana/bloque-tema -> tasa individual del diputado -> 0.5 neutro
    for col in ["tasa_afirmativo_tema_hist", "tasa_afirmativo_desde_2023",
                "tasa_afirmativo_2026", "tasa_afirmativo_bloque_tema"]:
        snap_dip[col] = snap_dip[col].fillna(snap_dip["tasa_afirmativo_hist"])
    for col in ["tasa_afirmativo_hist", "tasa_afirmativo_tema_hist", "tasa_alineacion_bloque_hist",
                "tasa_afirmativo_desde_2023", "tasa_afirmativo_2026", "tasa_afirmativo_bloque_tema"]:
        snap_dip[col] = snap_dip[col].fillna(0.5)

    # Features de autoria (Escenario A) -- misma logica que STG_5.2 T8:
    # - coincide_bloque_autor: si el autor es el Ejecutivo, compara contra el SET de bloques
    #   integrantes de la coalicion (no contra un unico texto); si es un legislador, compara
    #   texto contra texto.
    # - bloque_autor_enc puede dar -1 si el bloque actual del autor nunca aparecio como
    #   autor en el entrenamiento (documentado en el plan de la spec 014: 48/257 diputados
    #   estan en esa situacion hoy). Las otras 3 features de autoria, calculadas por texto,
    #   conservan la señal politica igual.
    snap_dip["bloque_votante_norm"] = snap_dip["bloque"].map(_normalizar_nombre)
    if resolucion_autor["es_poder_ejecutivo"] == 1:
        snap_dip["coincide_bloque_autor"] = snap_dip["bloque_votante_norm"].isin(
            resolucion_autor["bloques_integrantes_norm"]
        ).astype(int)
    else:
        snap_dip["coincide_bloque_autor"] = (
            snap_dip["bloque_votante_norm"] == resolucion_autor["bloque_autor_norm"]
        ).astype(int)

    snap_dip["es_poder_ejecutivo"] = resolucion_autor["es_poder_ejecutivo"]
    snap_dip["es_oficialista"] = resolucion_autor["es_oficialista"]
    snap_dip["bloque_autor_enc"] = resolucion_autor["bloque_autor_enc"]

    orden = _orden_features_autor()
    emb_cols = [c for c in orden if c.startswith("emb_")]
    emb_df = pd.DataFrame(
        np.tile(embedding, (len(snap_dip), 1)), columns=emb_cols, index=snap_dip.index
    )

    tabla = pd.concat([snap_dip, emb_df], axis=1)
    tabla["tema_id"] = tema_id

    X = tabla[orden]
    meta = tabla[["diputado", "bloque"]].reset_index(drop=True)
    return X, meta, tema_id, tema_label, resolucion_autor["bloque_autor"]


def precargar_artefactos() -> None:
    """Fuerza la carga de todos los artefactos pesados (modelo, KMeans, embedder, datos)
    una sola vez, para llamarla al iniciar la API y que el primer pedido no tenga que
    esperar."""
    cargar_modelo()
    cargar_le_voto()
    _cargar_encoder_bloque_autor()
    _cargar_kmeans()
    _cargar_mapa_temas()
    _cargar_embedder()
    _orden_features_autor()
    _cargar_periodos_presidenciales()
    db.cargar_consolidado()
    db.cargar_nomina()
    db.cargar_snapshot_diputado_autor()
    db.cargar_snapshot_diputado_tema_autor()
    db.cargar_snapshot_bloque_tema_autor()


def predecir_votos(titulo: str, autor: str) -> tuple[list[dict], int, str, str]:
    """Predice el voto de los 257 diputados actuales para un titulo de ley nuevo, dado su
    autor. Devuelve (predicciones, tema_id, tema_label, bloque_autor)."""
    X, meta, tema_id, tema_label, bloque_autor = construir_features(titulo, autor)

    modelo = cargar_modelo()
    le_voto = cargar_le_voto()

    pred_enc = modelo.predict(X.values)
    votos = le_voto.inverse_transform(pred_enc)

    predicciones = [
        {"diputado": diputado, "bloque": bloque, "voto_predicho": voto}
        for diputado, bloque, voto in zip(meta["diputado"], meta["bloque"], votos)
    ]
    return predicciones, tema_id, tema_label, bloque_autor
