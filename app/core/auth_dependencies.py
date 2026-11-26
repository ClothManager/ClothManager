from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import leer_token_acceso
from app.domain.usuario import Usuario
from app.repositories.autenticacion_repository import AutenticacionRepository


bearer = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    error_no_autenticado = HTTPException(
        status_code=401,
        detail="Autenticación requerida o sesión inválida",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciales is None:
        raise error_no_autenticado

    try:
        contenido = leer_token_acceso(credenciales.credentials)
        usuario_id = int(contenido["sub"])
        sesion_id = int(contenido["sid"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise error_no_autenticado

    repositorio = AutenticacionRepository(db)
    usuario = repositorio.obtener_usuario_por_id(usuario_id)
    sesion = repositorio.obtener_sesion(sesion_id)

    if usuario is None or usuario.estado != "ACTIVO":
        raise error_no_autenticado

    if sesion is None or sesion.usuario_id != usuario.id:
        raise error_no_autenticado

    if sesion.revocada_en is not None:
        raise error_no_autenticado

    expiracion = sesion.expira_en
    if expiracion.tzinfo is None:
        expiracion = expiracion.replace(tzinfo=timezone.utc)

    if expiracion <= datetime.now(timezone.utc):
        raise error_no_autenticado

    return usuario