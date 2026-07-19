from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def cargar_consolidado() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "df_consolidado.csv", parse_dates=["fecha_votacion"])


@lru_cache(maxsize=1)
def cargar_snapshot_diputado_autor() -> pd.DataFrame:
    """Snapshot de STG_8.2 (spec 014): tasas historicas por diputado, 257 personas
    (historial de grafias duplicadas combinado, ver Osuna/Pichetto)."""
    return pd.read_csv(DATA_DIR / "snapshot_diputado_autor.csv")


@lru_cache(maxsize=1)
def cargar_snapshot_diputado_tema_autor() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "snapshot_diputado_tema_autor.csv")


@lru_cache(maxsize=1)
def cargar_snapshot_bloque_tema_autor() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "snapshot_bloque_tema_autor.csv")


@lru_cache(maxsize=1)
def cargar_nomina() -> pd.DataFrame:
    """Nomina canonica de 257 diputados (spec 014, STG_8.2): un nombre canonico por
    persona, con sus grafias historicas absorbidas (ver caso Osuna/Pichetto, que hoy
    aparecen con dos grafias distintas en el historico crudo)."""
    df = pd.read_csv(DATA_DIR / "nomina_diputados.csv")
    df["grafias_historicas"] = df["grafias_historicas"].str.split(";")
    return df


def listar_diputados() -> list[dict]:
    """Nombre y bloque actual de los 257 diputados, para poblar tanto el selector de
    historial como el selector de autor de la app (que muestra el bloque junto al nombre)."""
    nomina = cargar_nomina().sort_values("diputado")
    return [
        {"diputado": fila.diputado, "bloque": fila.bloque_actual}
        for fila in nomina.itertuples()
    ]


def obtener_historial_diputado(nombre: str) -> dict | None:
    """Devuelve bloque, provincia, conteo de votos y ultimas 10 votaciones de un diputado
    (nombre canonico, el que devuelve listar_diputados()). El historial combina TODAS las
    grafias historicas de esa persona (ver nomina_diputados.csv), asi Osuna y Pichetto -que
    en el CSV crudo aparecen repartidos en dos nombres distintos- muestran su historial
    completo en una sola respuesta. None si el nombre no existe en la nomina."""
    nomina = cargar_nomina()
    fila_nomina = nomina[nomina["diputado"] == nombre]
    if fila_nomina.empty:
        return None
    fila_nomina = fila_nomina.iloc[0]

    df = cargar_consolidado()
    df_dip = df[df["diputado"].isin(fila_nomina["grafias_historicas"])]

    conteo = df_dip["voto"].value_counts()
    df_dip_desc = df_dip.sort_values("fecha_votacion", ascending=False)
    ultimas = df_dip_desc.head(10)[["titulo_base", "fecha_votacion", "voto"]]

    # Bloque/provincia actuales: los de la nomina (spec 014), no el voto mas reciente
    # calculado en el momento -- ya verificados contra diputados_actuales.csv en STG_8.2 T3,
    # y es el mismo criterio que usa /predecir (snapshot_diputado_autor.csv).
    return {
        "diputado": nombre,
        "bloque": fila_nomina["bloque_actual"],
        "provincia": fila_nomina["provincia_actual"],
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
