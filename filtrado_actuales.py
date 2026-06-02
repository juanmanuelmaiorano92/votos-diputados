import pandas as pd
import re
from unidecode import unidecode

# =========================
# CARGAR DATASETS
# =========================

historico = pd.read_csv("diputados_historico1.7.csv")
actuales = pd.read_csv("diputados_actuales.csv")

# limpiar espacios invisibles
historico.columns = historico.columns.str.strip()
actuales.columns = actuales.columns.str.strip()

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
# CREAR NOMBRES COMPLETOS
# =========================

historico["nombre_completo"] = (
    historico["NOMBRE"].fillna("") + " " +
    historico["APELLIDO"].fillna("")
)

actuales["nombre_completo"] = (
    actuales["Nombre"].fillna("") + " " +
    actuales["Apellido"].fillna("")
)

# =========================
# NORMALIZAR NOMBRES
# =========================

historico["nombre_normalizado"] = (
    historico["nombre_completo"]
    .apply(normalizar_texto)
)

actuales["nombre_normalizado"] = (
    actuales["nombre_completo"]
    .apply(normalizar_texto)
)

# =========================
# EXTRAER DIPUTADOS ACTUALES
# =========================

nombres_actuales = actuales["nombre_normalizado"].unique()

# =========================
# FILTRAR HISTÓRICO
# =========================

historico_filtrado = historico[
    historico["nombre_normalizado"].isin(nombres_actuales)
]

# =========================
# GUARDAR RESULTADO
# =========================

historico_filtrado.to_csv(
    "historico_actuales.csv",
    index=False
)

# =========================
# VERIFICACIONES
# =========================

print("Diputados actuales:")
print(actuales["nombre_normalizado"].nunique())

print("\nDiputados encontrados en histórico:")
print(historico_filtrado["nombre_normalizado"].nunique())

print("\nFiltrado terminado correctamente")