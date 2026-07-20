"""Página 'Predecir': predicción de voto para un título de ley + autor."""

import pandas as pd
import requests
import streamlit as st

from comun import (
    API_BASE_URL,
    AUTOR_PODER_EJECUTIVO,
    headers_auth,
    listar_diputados,
    predecir_votos,
)


def render():
    st.title("Predecir votación")
    st.write(
        "Ingresá el título de un proyecto de ley y quién lo firma para ver cómo votaría "
        "cada diputado."
    )

    try:
        diputados = listar_diputados(headers_auth())
    except requests.exceptions.RequestException:
        st.error(
            f"No se pudo conectar con la API en {API_BASE_URL}. "
            "Verificá que este corriendo (`uvicorn api.main:app`)."
        )
        st.stop()

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

        st.write(
            f"**Autor:** {resultado['autor']} — **Bloque asignado:** {resultado['bloque_autor']}"
        )
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
