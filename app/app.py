import streamlit as st

from comun import SesionVencida, barra_sesion, inyectar_fondo, pantalla_login
from paginas import consultar, mis_predicciones, predecir

inyectar_fondo()

st.title("LegisTrack — Predictor de Votaciones")
st.write("Consultá el historial de votaciones de un diputado y próximamente su predicción de voto.")

if "token" not in st.session_state:
    # Sin sesion, la unica pagina que existe es la de login: no se registra ninguna de
    # las 3 paginas reales, asi que no hay forma de entrar a ellas ni por URL.
    pagina_login = st.Page(pantalla_login, title="Ingresar")
    st.navigation([pagina_login], position="hidden").run()
    st.stop()

barra_sesion()

pagina_consultar = st.Page(consultar.render, title="Consultar", icon="🔎", url_path="consultar")
pagina_predecir = st.Page(predecir.render, title="Predecir", icon="🗳️", url_path="predecir")
pagina_mis_predicciones = st.Page(
    mis_predicciones.render, title="Mis predicciones", icon="📋", url_path="mis_predicciones"
)

try:
    st.navigation([pagina_consultar, pagina_predecir, pagina_mis_predicciones]).run()
except SesionVencida:
    # Un solo lugar para las 3 paginas: cualquier llamada a la API que devuelva 401
    # (token vencido o cuenta borrada) termina acá, en vez de mostrar el mensaje
    # generico de "no se pudo conectar" de cada pagina.
    st.session_state.pop("token", None)
    st.session_state.pop("username", None)
    st.warning("Tu sesión venció. Volvé a iniciar sesión.")
    st.rerun()
