import base64
import os
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.environ.get("LEGISTRACK_API_URL", "http://127.0.0.1:8000")


def _inyectar_fondo():
    ruta = Path(__file__).parent / "assets" / "fondo_combinado.jpg"
    if not ruta.exists():
        return
    datos = base64.b64encode(ruta.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{datos}");
            background-size: 100% auto;
            background-position: top center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Panel frosted-glass sobre el contenido */
        .block-container {{
            background-color: rgba(5, 10, 30, 0.55);
            border-radius: 14px;
            padding: 2rem 2.5rem !important;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        }}
        /* Texto blanco en toda la app */
        html, body, [class*="css"] {{
            color: #f0f0f0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


_inyectar_fondo()

st.title("LegisTrack — Predictor de Votaciones")
st.write("Consultá el historial de votaciones de un diputado y próximamente su predicción de voto.")


AUTOR_PODER_EJECUTIVO = "Poder Ejecutivo Nacional"


@st.cache_data
def listar_diputados():
    """Nombre y bloque actual de los 257 diputados (ordenados por nombre)."""
    r = requests.get(f"{API_BASE_URL}/diputados", timeout=10)
    r.raise_for_status()
    return sorted(r.json(), key=lambda d: d["diputado"])


@st.cache_data
def consultar_historial(nombre):
    r = requests.get(f"{API_BASE_URL}/diputados/{quote(nombre, safe='')}", timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def predecir_votos(titulo, autor):
    r = requests.post(
        f"{API_BASE_URL}/predecir", json={"titulo": titulo, "autor": autor}, timeout=30
    )
    if r.status_code == 422:
        return None
    r.raise_for_status()
    return r.json()


try:
    diputados = listar_diputados()
except requests.exceptions.RequestException:
    st.error(
        f"No se pudo conectar con la API en {API_BASE_URL}. "
        "Verificá que este corriendo (`uvicorn api.main:app`)."
    )
    st.stop()

nombres_diputados = [d["diputado"] for d in diputados]
diputado_sel = st.selectbox("Diputado", nombres_diputados)

if st.button("Consultar"):
    try:
        historial = consultar_historial(diputado_sel)
    except requests.exceptions.RequestException:
        st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
        st.stop()

    if historial is None:
        st.error(f"No se encontró historial para {diputado_sel}.")
        st.stop()

    conteo = historial["conteo_votos"]

    st.subheader(f"Datos de {diputado_sel}")
    st.write(f"**Bloque:** {historial['bloque']}")
    st.write(f"**Provincia:** {historial['provincia']}")
    st.write(
        f"**Votos registrados:** AFIRMATIVO {conteo['AFIRMATIVO']} | "
        f"NEGATIVO {conteo['NEGATIVO']} | ABSTENCIÓN {conteo['ABSTENCION']}"
    )

    st.subheader("Últimas 10 votaciones")
    ultimas = pd.DataFrame(historial["ultimas_votaciones"])
    ultimas["titulo"] = ultimas["titulo"].str[:80]
    ultimas["fecha"] = pd.to_datetime(ultimas["fecha"]).dt.strftime("%d/%m/%Y")
    ultimas.columns = ["Proyecto", "Fecha", "Voto"]
    st.dataframe(ultimas, hide_index=True)

st.divider()
st.subheader("Predicción de voto")
st.write(
    "Ingresá el título de un proyecto de ley y quién lo firma para ver cómo votaría "
    "cada diputado."
)

# Opciones del selector de autor: el Poder Ejecutivo primero, despues los 257 diputados
# actuales identificados con su bloque vigente (para poder encontrarlos facil). El valor
# que se envia a la API es siempre el nombre canonico -- se guarda en un diccionario
# etiqueta -> nombre para traducir la seleccion.
opciones_autor = {AUTOR_PODER_EJECUTIVO: AUTOR_PODER_EJECUTIVO}
for d in diputados:
    opciones_autor[f"{d['diputado']} ({d['bloque']})"] = d["diputado"]

with st.form("form_prediccion"):
    titulo_ley = st.text_area("Título del proyecto de ley", height=100)
    autor_etiqueta = st.selectbox("Autor del proyecto", list(opciones_autor.keys()))
    enviar_prediccion = st.form_submit_button("Predecir")

if enviar_prediccion:
    if not titulo_ley.strip():
        st.warning("Ingresá un título antes de predecir.")
        st.stop()

    autor_sel = opciones_autor[autor_etiqueta]

    try:
        resultado = predecir_votos(titulo_ley, autor_sel)
    except requests.exceptions.RequestException:
        st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
        st.stop()

    if resultado is None:
        st.warning("Ingresá un título antes de predecir.")
        st.stop()

    st.write(f"**Autor:** {resultado['autor']} — **Bloque asignado:** {resultado['bloque_autor']}")
    st.write(f"**Tema detectado:** {resultado['tema_asignado']}")

    predicciones = pd.DataFrame(resultado["predicciones"])
    conteo_pred = predicciones["voto_predicho"].value_counts()
    st.write(
        f"**Distribución de la predicción:** AFIRMATIVO {conteo_pred.get('AFIRMATIVO', 0)} | "
        f"NEGATIVO {conteo_pred.get('NEGATIVO', 0)} | "
        f"ABSTENCIÓN {conteo_pred.get('ABSTENCION', conteo_pred.get('ABSTENCIÓN', 0))}"
    )

    predicciones.columns = ["Diputado", "Bloque", "Voto predicho"]
    st.dataframe(predicciones, hide_index=True)
