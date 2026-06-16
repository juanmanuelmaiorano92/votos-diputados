import base64
from pathlib import Path

import pandas as pd
import streamlit as st


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


@st.cache_data
def cargar_datos():
    return pd.read_csv("data/df_consolidado.csv", parse_dates=["fecha_votacion"])


df = cargar_datos()

diputados = sorted(df["diputado"].unique())

diputado_sel = st.selectbox("Diputado", diputados)

if st.button("Consultar"):
    df_diputado = df[df["diputado"] == diputado_sel]

    bloque = df_diputado["bloque"].iloc[0]
    provincia = df_diputado["provincia"].iloc[0]
    conteo = df_diputado["voto"].value_counts()

    st.subheader(f"Datos de {diputado_sel}")
    st.write(f"**Bloque:** {bloque}")
    st.write(f"**Provincia:** {provincia}")
    st.write(f"**Votos registrados:** AFIRMATIVO {conteo.get('AFIRMATIVO', 0)} | NEGATIVO {conteo.get('NEGATIVO', 0)} | ABSTENCIÓN {conteo.get('ABSTENCION', conteo.get('ABSTENCIÓN', 0))}")

    st.subheader("Últimas 10 votaciones")
    ultimas = (
        df_diputado
        .sort_values("fecha_votacion", ascending=False)
        .head(10)[["titulo_base", "fecha_votacion", "voto"]]
        .copy()
    )
    ultimas["titulo_base"] = ultimas["titulo_base"].str[:80]
    ultimas.columns = ["Proyecto", "Fecha", "Voto"]
    ultimas["Fecha"] = ultimas["Fecha"].dt.strftime("%d/%m/%Y")
    st.dataframe(ultimas, hide_index=True)

    st.divider()
    st.write("**Predicción de voto:**")
    st.write("Próximamente podrás ingresar el texto de un proyecto de ley, indicar su autor y ver cómo votaría cada uno de los 257 diputados.")
