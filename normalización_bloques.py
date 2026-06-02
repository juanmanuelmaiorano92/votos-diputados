import pandas as pd
import re
from unidecode import unidecode

# =========================
# CARGAR DATASET
# =========================

df = pd.read_csv("historico_actuales.csv")

# =========================
# LIMPIAR COLUMNAS
# =========================

df.columns = df.columns.str.strip()

# =========================
# FUNCIÓN NORMALIZADORA
# =========================

def normalizar_texto(texto):

    if pd.isna(texto):
        return None

    texto = texto.lower()
    texto = unidecode(texto)

    texto = re.sub(r"[^a-z\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()

# =========================
# NORMALIZAR BLOQUES
# =========================

df["bloque_normalizado"] = (
    df["BLOQUE"]
    .apply(normalizar_texto)
)

# =========================
# VER VARIANTES
# =========================

print(
    df["bloque_normalizado"]
    .value_counts()
    .head(50)
)

# =========================
# GUARDAR
# =========================

df.to_csv(
    "historico_actuales_bloques.csv",
    index=False
)

print("\nNormalización de bloques terminada")