from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ActivarCredenciales,
    CambiarContrasenaRequest,
    ConfirmarRecuperacionRequest,
    LoginRequest,
    RenovarSesionRequest,
    SolicitarRecuperacionRequest,
)
from app.api.usuario_api import verificar_administrador
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.core.dev_mailer import (
    enviar_token_activacion,
    enviar_token_recuperacion,
)
from app.domain.usuario import Usuario
from app.repositories.autenticacion_repository import AutenticacionRepository
from app.services.autenticacion_service import AutenticacionService

router = APIRouter(
    prefix="/api/v1/autenticacion",
    tags=["Autenticación"],
)


@router.post(
    "/usuarios/{usuario_id}/activacion",
    status_code=status.HTTP_202_ACCEPTED,
)
def solicitar_activacion(
    usuario_id: int,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = AutenticacionRepository(db)
    servicio = AutenticacionService(repositorio)

    usuario = repositorio.obtener_usuario_por_id(usuario_id)
    if usuario is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = servicio.crear_token_activacion(usuario_id)
    enviar_token_activacion(usuario.correo, token)

    return {
        "mensaje": "Si el usuario puede activarse, se envió la instrucción",
        "success": True,
    }


@router.post("/activar")
def activar_credenciales(
    datos: ActivarCredenciales,
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(AutenticacionRepository(db))
    servicio.activar_credenciales(datos.token, datos.contrasena)

    return {
        "mensaje": "Credenciales activadas correctamente",
        "success": True,
    }


@router.post("/login")
def iniciar_sesion(
    datos: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    repositorio = AutenticacionRepository(db)
    servicio = AutenticacionService(repositorio)

    resultado = servicio.iniciar_sesion(
        identificador=datos.identificador,
        contrasena=datos.contrasena,
        dispositivo=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )

    return {
        "mensaje": "Autenticación exitosa",
        "data": resultado,
        "success": True,
    }
@router.get("/me")
def obtener_mi_usuario(
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return {
        "mensaje": "Usuario autenticado correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "estado": usuario.estado,
        },
        "success": True,
    }
@router.post("/renovacion")
def renovar_sesion(
    datos: RenovarSesionRequest,
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(
        AutenticacionRepository(db)
    )

    resultado = servicio.renovar_sesion(datos.refresh_token)

    return {
        "mensaje": "Sesión renovada correctamente",
        "data": resultado,
        "success": True,
    }
@router.post("/logout")
def cerrar_sesion(
    datos: RenovarSesionRequest,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(
        AutenticacionRepository(db)
    )
    servicio.cerrar_sesion(
        usuario_id=usuario.id,
        refresh_token=datos.refresh_token,
    )

    return {
        "mensaje": "Sesión cerrada correctamente",
        "success": True,
    }
@router.put("/contrasena")
def cambiar_contrasena(
    datos: CambiarContrasenaRequest,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(
        AutenticacionRepository(db)
    )
    servicio.cambiar_contrasena(
        usuario_id=usuario.id,
        contrasena_actual=datos.contrasena_actual,
        contrasena_nueva=datos.contrasena_nueva,
    )

    return {
        "mensaje": "Contraseña actualizada; inicia sesión nuevamente",
        "success": True,
    }
@router.post("/recuperacion", status_code=status.HTTP_202_ACCEPTED)
def solicitar_recuperacion(
    datos: SolicitarRecuperacionRequest,
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(
        AutenticacionRepository(db)
    )
    token = servicio.solicitar_recuperacion(datos.correo)

    if token is not None:
        enviar_token_recuperacion(datos.correo, token)

    return {
        "mensaje": (
            "Si la cuenta existe y está activa, "
            "se enviaron instrucciones de recuperación"
        ),
        "success": True,
    }


@router.post("/recuperacion/confirmacion")
def confirmar_recuperacion(
    datos: ConfirmarRecuperacionRequest,
    db: Session = Depends(get_db),
):
    servicio = AutenticacionService(
        AutenticacionRepository(db)
    )
    servicio.confirmar_recuperacion(
        token=datos.token,
        contrasena_nueva=datos.contrasena_nueva,
    )

    return {
        "mensaje": "Contraseña recuperada correctamente",
        "success": True,
    }