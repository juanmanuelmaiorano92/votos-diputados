"""Página 'Mis predicciones': historial de predicciones del usuario logueado."""

import pandas as pd
import requests
import streamlit as st

from comun import API_BASE_URL, obtener_mis_predicciones


def render():
    st.title("Mis predicciones")

    try:
        mis_predicciones = obtener_mis_predicciones()
    except requests.exceptions.RequestException:
        st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
        return

    if not mis_predicciones:
        st.write("Todavía no hiciste ninguna predicción.")
        return

    tabla_historial = pd.DataFrame(mis_predicciones)
    tabla_historial["fecha"] = pd.to_datetime(tabla_historial["fecha"]).dt.strftime(
        "%d/%m/%Y %H:%M"
    )
    tabla_historial["titulo"] = tabla_historial["titulo"].str[:80]
    tabla_historial = tabla_historial[
        ["fecha", "titulo", "autor", "tema", "n_afirmativo", "n_negativo", "n_abstencion"]
    ]
    tabla_historial.columns = [
        "Fecha", "Proyecto", "Autor", "Tema", "AFIRMATIVO", "NEGATIVO", "ABSTENCIÓN",
    ]
    st.dataframe(tabla_historial, hide_index=True)
