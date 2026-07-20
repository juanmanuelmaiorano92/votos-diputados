from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import LoginRequest, RegistroRequest, TokenResponse
from api.seguridad import crear_token, hashear_clave, verificar_clave
from api.tablas import Usuario

router = APIRouter(tags=["auth"])


@router.post("/registro", status_code=201)
def registro(request: RegistroRequest, db: Session = Depends(get_db)):
    ya_existe = db.query(Usuario).filter(Usuario.username == request.username).one_or_none()
    if ya_existe is not None:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    usuario = Usuario(username=request.username, password_hash=hashear_clave(request.password))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        # Dos registros con el mismo usuario llegaron casi al mismo tiempo: el chequeo
        # de arriba no alcanzo a verlo, pero la restriccion unique de la tabla si.
        db.rollback()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    return {"username": usuario.username}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.username == request.username).one_or_none()

    # Mismo error generico si el usuario no existe o si la clave es incorrecta,
    # para no revelar a un atacante cual de las dos cosas fallo.
    error_credenciales = HTTPException(status_code=401, detail="Usuario o clave incorrectos")

    if usuario is None:
        raise error_credenciales
    if not verificar_clave(request.password, usuario.password_hash):
        raise error_credenciales

    token = crear_token(usuario.username)
    return TokenResponse(access_token=token)
