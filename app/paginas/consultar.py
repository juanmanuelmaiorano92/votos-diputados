"""Página 'Consultar': historial de votaciones de un diputado."""

import pandas as pd
import requests
import streamlit as st

from comun import API_BASE_URL, consultar_historial, headers_auth, listar_diputados


def render():
    st.title("Consultar diputado")
    st.write("Consultá el historial de votaciones de un diputado.")

    try:
        diputados = listar_diputados(headers_auth())
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
            historial = consultar_historial(diputado_sel, headers_auth())
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
