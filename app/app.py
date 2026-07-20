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


def _pantalla_login():
    """Sin sesion iniciada, la app no muestra nada mas que esto (login/registro)."""
    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        with st.form("form_login"):
            username = st.text_input("Usuario", key="login_username")
            password = st.text_input("Contraseña", type="password", key="login_password")
            enviar = st.form_submit_button("Ingresar")
        if enviar:
            try:
                r = requests.post(
                    f"{API_BASE_URL}/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )
            except requests.exceptions.RequestException:
                st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
                return
            if r.status_code == 401:
                st.error("Usuario o contraseña incorrectos.")
                return
            r.raise_for_status()
            st.session_state["token"] = r.json()["access_token"]
            st.session_state["username"] = username
            st.rerun()

    with tab_registro:
        with st.form("form_registro"):
            username_r = st.text_input("Elegí un usuario", key="registro_username")
            password_r = st.text_input(
                "Elegí una contraseña (mínimo 6 caracteres)",
                type="password",
                key="registro_password",
            )
            enviar_r = st.form_submit_button("Crear cuenta")
        if enviar_r:
            try:
                r = requests.post(
                    f"{API_BASE_URL}/registro",
                    json={"username": username_r, "password": password_r},
                    timeout=10,
                )
            except requests.exceptions.RequestException:
                st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
                return
            if r.status_code == 400:
                st.error("Ese nombre de usuario ya existe.")
                return
            if r.status_code == 422:
                st.error(f"Datos inválidos: {r.json().get('detail')}")
                return
            r.raise_for_status()
            st.success("Cuenta creada. Ahora podés iniciar sesión en la pestaña de al lado.")


if "token" not in st.session_state:
    _pantalla_login()
    st.stop()


def _headers_auth():
    return {"Authorization": f"Bearer {st.session_state['token']}"}


col_sesion, col_logout = st.columns([4, 1])
with col_sesion:
    st.write(f"Sesión iniciada como **{st.session_state['username']}**")
with col_logout:
    if st.button("Cerrar sesión"):
        del st.session_state["token"]
        del st.session_state["username"]
        st.rerun()


# ttl acotado (bien por debajo de las 12hs de vencimiento del token): el header no
# forma parte de la clave de cache (no es hasheable), asi que sin un ttl el dato queda
# cacheado para siempre y nunca se vuelve a validar el token contra la API.
@st.cache_data(ttl=1800)
def listar_diputados(_headers):
    """Nombre y bloque actual de los 257 diputados (ordenados por nombre)."""
    r = requests.get(f"{API_BASE_URL}/diputados", headers=_headers, timeout=10)
    r.raise_for_status()
    return sorted(r.json(), key=lambda d: d["diputado"])


@st.cache_data(ttl=1800)
def consultar_historial(nombre, _headers):
    r = requests.get(
        f"{API_BASE_URL}/diputados/{quote(nombre, safe='')}", headers=_headers, timeout=10
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def predecir_votos(titulo, autor):
    r = requests.post(
        f"{API_BASE_URL}/predecir",
        json={"titulo": titulo, "autor": autor},
        headers=_headers_auth(),
        timeout=30,
    )
    if r.status_code == 422:
        return None
    r.raise_for_status()
    return r.json()


try:
    diputados = listar_diputados(_headers_auth())
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
        historial = consultar_historial(diputado_sel, _headers_auth())
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

st.divider()
st.subheader("Mis predicciones")


def obtener_mis_predicciones():
    r = requests.get(f"{API_BASE_URL}/mis-predicciones", headers=_headers_auth(), timeout=10)
    r.raise_for_status()
    return r.json()


try:
    mis_predicciones = obtener_mis_predicciones()
except requests.exceptions.RequestException:
    st.error(f"No se pudo conectar con la API en {API_BASE_URL}.")
else:
    if not mis_predicciones:
        st.write("Todavía no hiciste ninguna predicción.")
    else:
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
