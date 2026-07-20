import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.db import get_db
from api.tablas import Usuario

_contexto_claves = CryptContext(schemes=["bcrypt"], deprecated="auto")

_ALGORITMO_JWT = "HS256"
_MINUTOS_VENCIMIENTO_TOKEN = 60 * 12  # 12 horas


def hashear_clave(clave: str) -> str:
    return _contexto_claves.hash(clave)


def verificar_clave(clave: str, clave_hash: str) -> bool:
    return _contexto_claves.verify(clave, clave_hash)


def _clave_secreta_jwt() -> str:
    clave = os.environ.get("JWT_SECRET_KEY")
    if not clave:
        raise RuntimeError("Falta la variable de entorno JWT_SECRET_KEY")
    return clave


def crear_token(username: str) -> str:
    vencimiento = datetime.now(timezone.utc) + timedelta(minutes=_MINUTOS_VENCIMIENTO_TOKEN)
    payload = {"sub": username, "exp": vencimiento}
    return jwt.encode(payload, _clave_secreta_jwt(), algorithm=_ALGORITMO_JWT)


class TokenInvalidoError(Exception):
    pass


def validar_token(token: str) -> str:
    """Devuelve el username si el token es valido; lanza TokenInvalidoError si es
    invalido, esta manipulado o ya vencio."""
    try:
        payload = jwt.decode(token, _clave_secreta_jwt(), algorithms=[_ALGORITMO_JWT])
    except JWTError as e:
        raise TokenInvalidoError(str(e)) from e

    username = payload.get("sub")
    if not username:
        raise TokenInvalidoError("El token no tiene un usuario asociado")
    return username


_esquema_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia que protege un endpoint: exige un JWT valido en el encabezado
    Authorization y devuelve el Usuario real de la base. 401 si falta el token, es
    invalido, esta vencido, o el usuario del token ya no existe en la base."""
    error_no_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciales is None:
        raise error_no_autorizado

    try:
        username = validar_token(credenciales.credentials)
    except TokenInvalidoError:
        raise error_no_autorizado

    usuario = db.query(Usuario).filter(Usuario.username == username).one_or_none()
    if usuario is None:
        raise error_no_autorizado

    return usuario
