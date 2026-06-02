import pandas as pd
import re
from unidecode import unidecode

# =========================
# CARGAR DATASET
# =========================

df = pd.read_csv("diputados_historico1.7.csv")

# =========================
# CREAR NOMBRE COMPLETO
# =========================

df["nombre_completo"] = (
    df["NOMBRE"].fillna("") + " " + df["APELLIDO"].fillna("")
)

# =========================
# FUNCIÓN DE NORMALIZACIÓN
# =========================

def normalizar_nombre(nombre):

    if pd.isna(nombre):
        return None

    # minúsculas
    nombre = nombre.lower()

    # quitar tildes
    nombre = unidecode(nombre)

    # eliminar caracteres raros
    nombre = re.sub(r"[^a-z\s]", "", nombre)

    # eliminar espacios duplicados
    nombre = re.sub(r"\s+", " ", nombre)

    # quitar espacios extremos
    nombre = nombre.strip()

    return nombre

# =========================
# NORMALIZAR
# =========================

df["nombre_normalizado"] = df["nombre_completo"].apply(normalizar_nombre)

# =========================
# GUARDAR NUEVO CSV
# =========================

df.to_csv("diputados_normalizados.csv", index=False)

print("Normalización terminada")