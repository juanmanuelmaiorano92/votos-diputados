from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def cargar_consolidado() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "df_consolidado.csv", parse_dates=["fecha_votacion"])


@lru_cache(maxsize=1)
def cargar_snapshot_diputado() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "snapshot_diputado.csv")


@lru_cache(maxsize=1)
def cargar_snapshot_diputado_tema() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "snapshot_diputado_tema.csv")


@lru_cache(maxsize=1)
def cargar_snapshot_bloque_tema() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "snapshot_bloque_tema.csv")


def listar_diputados() -> list[str]:
    return sorted(cargar_snapshot_diputado()["diputado"].unique())


def obtener_historial_diputado(nombre: str) -> dict | None:
    """Devuelve bloque, provincia, conteo de votos y ultimas 10 votaciones de un diputado.
    None si el nombre no existe en el historial."""
    df = cargar_consolidado()
    df_dip = df[df["diputado"] == nombre]
    if df_dip.empty:
        return None

    conteo = df_dip["voto"].value_counts()
    df_dip_desc = df_dip.sort_values("fecha_votacion", ascending=False)
    ultimas = df_dip_desc.head(10)[["titulo_base", "fecha_votacion", "voto"]]

    # Bloque/provincia del voto MAS RECIENTE (no el primero del CSV, que no esta
    # ordenado por fecha) -- algunos diputados cambiaron de bloque, y esto debe
    # coincidir con el criterio de snapshot_diputado.csv (usado en /predecir).
    return {
        "diputado": nombre,
        "bloque": df_dip_desc["bloque"].iloc[0],
        "provincia": df_dip_desc["provincia"].iloc[0],
        "conteo_votos": {
            "AFIRMATIVO": int(conteo.get("AFIRMATIVO", 0)),
            "NEGATIVO": int(conteo.get("NEGATIVO", 0)),
            "ABSTENCION": int(conteo.get("ABSTENCION", conteo.get("ABSTENCIÓN", 0))),
        },
        "ultimas_votaciones": [
            {
                "titulo": fila.titulo_base,
                "fecha": fila.fecha_votacion.strftime("%Y-%m-%d"),
                "voto": fila.voto,
            }
            for fila in ultimas.itertuples()
        ],
    }
