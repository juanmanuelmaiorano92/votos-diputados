"""Piezas compartidas entre las páginas de la app: conexión con la API, sesión y login."""

import base64
from pathlib import Path
from urllib.parse import quote
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("LEGISTRACK_API_URL", "http://127.0.0.1:8000")

AUTOR_PODER_EJECUTIVO = "Poder Ejecutivo Nacional"


class SesionVencida(Exception):
    """La API respondió 401: el token ya no es válido (venció o la cuenta no existe)."""


def inyectar_fondo():
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


def pantalla_login():
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


def headers_auth():
    return {"Authorization": f"Bearer {st.session_state['token']}"}


def barra_sesion():
    """Dibuja en el sidebar quién está logueado y el botón para cerrar sesión."""
    with st.sidebar:
        st.write(f"Sesión iniciada como **{st.session_state['username']}**")
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
    if r.status_code == 401:
        raise SesionVencida()
    r.raise_for_status()
    return sorted(r.json(), key=lambda d: d["diputado"])


@st.cache_data(ttl=1800)
def consultar_historial(nombre, _headers):
    r = requests.get(
        f"{API_BASE_URL}/diputados/{quote(nombre, safe='')}", headers=_headers, timeout=10
    )
    if r.status_code == 401:
        raise SesionVencida()
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def predecir_votos(titulo, autor):
    r = requests.post(
        f"{API_BASE_URL}/predecir",
        json={"titulo": titulo, "autor": autor},
        headers=headers_auth(),
        timeout=30,
    )
    if r.status_code == 401:
        raise SesionVencida()
    if r.status_code == 422:
        return None
    r.raise_for_status()
    return r.json()


def obtener_mis_predicciones():
    r = requests.get(f"{API_BASE_URL}/mis-predicciones", headers=headers_auth(), timeout=10)
    if r.status_code == 401:
        raise SesionVencida()
    r.raise_for_status()
    return r.json()
