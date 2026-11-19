import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.security import (
    crear_token_acceso,
    generar_token_secreto,
    hash_contrasena,
    hash_token,
    verificar_contrasena,
)
from app.domain.autenticacion import (
    CredencialUsuario,
    EventoSeguridad,
    SesionUsuario,
    TokenCuenta,
)
from app.repositories.autenticacion_repository import AutenticacionRepository


class AutenticacionService:
    def __init__(self, repositorio: AutenticacionRepository):
        self.repositorio = repositorio

    def crear_token_activacion(self, usuario_id: int) -> str:
        usuario = self.repositorio.obtener_usuario_por_id(usuario_id)

        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if usuario.estado != "ACTIVO":
            raise HTTPException(status_code=422, detail="El usuario está inactivo")

        if self.repositorio.obtener_credencial(usuario_id):
            raise HTTPException(
                status_code=409,
                detail="El usuario ya tiene credenciales activas",
            )

        token = generar_token_secreto()
        ahora = datetime.now(timezone.utc)

        try:
            self.repositorio.invalidar_tokens_cuenta(usuario_id, "ACTIVACION")
            self.repositorio.agregar_token_cuenta(
                TokenCuenta(
                    usuario_id=usuario_id,
                    tipo="ACTIVACION",
                    token_hash=hash_token(token),
                    creado_en=ahora,
                    expira_en=ahora + timedelta(hours=24),
                )
            )
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario_id,
                    evento="SOLICITUD_ACTIVACION",
                    resultado="EXITOSO",
                )
            )
            self.repositorio.guardar_cambios()
            return token
        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def activar_credenciales(self, token: str, contrasena: str) -> None:
        registro = self.repositorio.buscar_token_cuenta(
            hash_token(token),
            "ACTIVACION",
        )

        if registro is None or registro.usado_en is not None:
            raise HTTPException(
                status_code=400,
                detail="El token de activación no es válido",
            )

        ahora = datetime.now(timezone.utc)
        expiracion = registro.expira_en

        if expiracion.tzinfo is None:
            expiracion = expiracion.replace(tzinfo=timezone.utc)

        if expiracion <= ahora:
            raise HTTPException(
                status_code=400,
                detail="El token de activación venció",
            )

        usuario = self.repositorio.obtener_usuario_por_id(registro.usuario_id)

        if usuario is None or usuario.estado != "ACTIVO":
            raise HTTPException(
                status_code=400,
                detail="El token de activación no es válido",
            )

        if self.repositorio.obtener_credencial(usuario.id):
            raise HTTPException(
                status_code=409,
                detail="El usuario ya tiene credenciales activas",
            )

        try:
            self.repositorio.agregar_credencial(
                CredencialUsuario(
                    usuario_id=usuario.id,
                    hash_contrasena=hash_contrasena(contrasena),
                    actualizada_en=ahora,
                )
            )
            registro.usado_en = ahora
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="ACTIVACION_CREDENCIALES",
                    resultado="EXITOSO",
                )
            )
            self.repositorio.guardar_cambios()
        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def iniciar_sesion(
        self,
        identificador: str,
        contrasena: str,
        dispositivo: str | None = None,
        ip: str | None = None,
    ) -> dict:
        usuario = self.repositorio.buscar_usuario(identificador)

        if usuario is None or usuario.estado != "ACTIVO":
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id if usuario else None,
                    evento="LOGIN",
                    resultado="FALLIDO",
                    ip=ip,
                )
            )
            self.repositorio.guardar_cambios()
            raise HTTPException(
                status_code=401,
                detail="No fue posible iniciar sesión con esos datos",
            )

        credencial = self.repositorio.obtener_credencial(usuario.id)

        if credencial is None:
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="LOGIN",
                    resultado="FALLIDO",
                    ip=ip,
                )
            )
            self.repositorio.guardar_cambios()
            raise HTTPException(
                status_code=401,
                detail="No fue posible iniciar sesión con esos datos",
            )

        ahora = datetime.now(timezone.utc)
        bloqueada_hasta = credencial.bloqueada_hasta

        if bloqueada_hasta is not None and bloqueada_hasta.tzinfo is None:
            bloqueada_hasta = bloqueada_hasta.replace(tzinfo=timezone.utc)

        if bloqueada_hasta is not None and bloqueada_hasta > ahora:
            raise HTTPException(
                status_code=401,
                detail="No fue posible iniciar sesión con esos datos",
            )

        if not verificar_contrasena(contrasena, credencial.hash_contrasena):
            credencial.fallos_consecutivos += 1

            if credencial.fallos_consecutivos >= 5:
                credencial.bloqueada_hasta = ahora + timedelta(minutes=15)

            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="LOGIN",
                    resultado="FALLIDO",
                    ip=ip,
                )
            )
            self.repositorio.guardar_cambios()
            raise HTTPException(
                status_code=401,
                detail="No fue posible iniciar sesión con esos datos",
            )

        credencial.fallos_consecutivos = 0
        credencial.bloqueada_hasta = None

        refresh_token = generar_token_secreto()
        dias_renovacion = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        sesion = SesionUsuario(
            usuario_id=usuario.id,
            token_renovacion_hash=hash_token(refresh_token),
            expira_en=ahora + timedelta(days=dias_renovacion),
            dispositivo=dispositivo,
        )

        try:
            self.repositorio.agregar_sesion(sesion)

            access_token = crear_token_acceso(
                usuario_id=usuario.id,
                sesion_id=sesion.id,
            )

            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="LOGIN",
                    resultado="EXITOSO",
                    ip=ip,
                )
            )
            self.repositorio.guardar_cambios()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(
                    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
                ) * 60,
                "usuario_id": usuario.id,
                "nombre_usuario": usuario.nombre_usuario,
            }
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def renovar_sesion(self, refresh_token: str) -> dict:
        sesion = self.repositorio.buscar_sesion_por_refresh_hash(
            hash_token(refresh_token)
        )

        if sesion is None or sesion.revocada_en is not None:
            raise HTTPException(
                status_code=401,
                detail="La sesión no es válida",
            )

        ahora = datetime.now(timezone.utc)
        expiracion = sesion.expira_en

        if expiracion.tzinfo is None:
            expiracion = expiracion.replace(tzinfo=timezone.utc)

        if expiracion <= ahora:
            self.repositorio.revocar_sesion(sesion)
            self.repositorio.guardar_cambios()
            raise HTTPException(
                status_code=401,
                detail="La sesión venció",
            )

        usuario = self.repositorio.obtener_usuario_por_id(sesion.usuario_id)

        if usuario is None or usuario.estado != "ACTIVO":
            self.repositorio.revocar_sesion(sesion)
            self.repositorio.guardar_cambios()
            raise HTTPException(
                status_code=401,
                detail="La sesión no es válida",
            )

        nuevo_refresh = generar_token_secreto()
        dias_renovacion = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        sesion.token_renovacion_hash = hash_token(nuevo_refresh)
        sesion.ultimo_uso_en = ahora
        sesion.expira_en = ahora + timedelta(days=dias_renovacion)

        try:
            access_token = crear_token_acceso(usuario.id, sesion.id)

            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="RENOVACION_SESION",
                    resultado="EXITOSO",
                )
            )
            self.repositorio.guardar_cambios()

            return {
                "access_token": access_token,
                "refresh_token": nuevo_refresh,
                "token_type": "Bearer",
                "expires_in": int(
                    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
                ) * 60,
                "usuario_id": usuario.id,
                "nombre_usuario": usuario.nombre_usuario,
            }
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def cerrar_sesion(
        self,
        usuario_id: int,
        refresh_token: str,
    ) -> None:
        sesion = self.repositorio.buscar_sesion_por_refresh_hash(
            hash_token(refresh_token)
        )

        if sesion is None or sesion.usuario_id != usuario_id:
            raise HTTPException(
                status_code=401,
                detail="La sesión no es válida",
            )

        if sesion.revocada_en is None:
            self.repositorio.revocar_sesion(sesion)
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario_id,
                    evento="LOGOUT",
                    resultado="EXITOSO",
                )
            )
            self.repositorio.guardar_cambios()
    def cambiar_contrasena(
        self,
        usuario_id: int,
        contrasena_actual: str,
        contrasena_nueva: str,
    ) -> None:
        credencial = self.repositorio.obtener_credencial(usuario_id)

        if credencial is None:
            raise HTTPException(
                status_code=401,
                detail="El usuario no tiene credenciales activas",
            )

        if not verificar_contrasena(
            contrasena_actual,
            credencial.hash_contrasena,
        ):
            raise HTTPException(
                status_code=400,
                detail="La contraseña actual no es correcta",
            )

        if verificar_contrasena(
            contrasena_nueva,
            credencial.hash_contrasena,
        ):
            raise HTTPException(
                status_code=422,
                detail="La nueva contraseña debe ser diferente",
            )

        ahora = datetime.now(timezone.utc)

        try:
            credencial.hash_contrasena = hash_contrasena(contrasena_nueva)
            credencial.actualizada_en = ahora
            credencial.fallos_consecutivos = 0
            credencial.bloqueada_hasta = None

            self.repositorio.revocar_todas_las_sesiones(usuario_id)
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario_id,
                    evento="CAMBIO_CONTRASENA",
                    resultado="EXITOSO",
                )
            )
            self.repositorio.guardar_cambios()
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def solicitar_recuperacion(self, correo: str) -> str | None:
        usuario = self.repositorio.buscar_usuario(correo)

        if usuario is None or usuario.estado != "ACTIVO":
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id if usuario else None,
                    evento="SOLICITUD_RECUPERACION",
                    resultado="RECIBIDA",
                )
            )
            self.repositorio.guardar_cambios()
            return None

        token = generar_token_secreto()
        ahora = datetime.now(timezone.utc)

        try:
            self.repositorio.invalidar_tokens_cuenta(
                usuario.id,
                "RECUPERACION",
            )
            self.repositorio.agregar_token_cuenta(
                TokenCuenta(
                    usuario_id=usuario.id,
                    tipo="RECUPERACION",
                    token_hash=hash_token(token),
                    creado_en=ahora,
                    expira_en=ahora + timedelta(minutes=30),
                )
            )
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="SOLICITUD_RECUPERACION",
                    resultado="RECIBIDA",
                )
            )
            self.repositorio.guardar_cambios()
            return token
        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def confirmar_recuperacion(
        self,
        token: str,
        contrasena_nueva: str,
    ) -> None:
        registro = self.repositorio.buscar_token_cuenta(
            hash_token(token),
            "RECUPERACION",
        )

        if registro is None or registro.usado_en is not None:
            raise HTTPException(
                status_code=400,
                detail="El token de recuperación no es válido",
            )

        ahora = datetime.now(timezone.utc)
        expiracion = registro.expira_en

        if expiracion.tzinfo is None:
            expiracion = expiracion.replace(tzinfo=timezone.utc)

        if expiracion <= ahora:
            raise HTTPException(
                status_code=400,
                detail="El token de recuperación venció",
            )

        usuario = self.repositorio.obtener_usuario_por_id(registro.usuario_id)
        credencial = self.repositorio.obtener_credencial(registro.usuario_id)

        if usuario is None or usuario.estado != "ACTIVO" or credencial is None:
            raise HTTPException(
                status_code=400,
                detail="El token de recuperación no es válido",
            )

        if verificar_contrasena(
            contrasena_nueva,
            credencial.hash_contrasena,
        ):
            raise HTTPException(
                status_code=422,
                detail="La nueva contraseña debe ser diferente",
            )

        try:
            credencial.hash_contrasena = hash_contrasena(contrasena_nueva)
            credencial.actualizada_en = ahora
            credencial.fallos_consecutivos = 0
            credencial.bloqueada_hasta = None

            registro.usado_en = ahora
            self.repositorio.invalidar_tokens_cuenta(
                usuario.id,
                "RECUPERACION",
            )
            self.repositorio.revocar_todas_las_sesiones(usuario.id)
            self.repositorio.registrar_evento(
                EventoSeguridad(
                    usuario_id=usuario.id,
                    evento="RECUPERACION_CONTRASENA",
                    resultado="EXITOSA",
                )
            )
            self.repositorio.guardar_cambios()
        except Exception:
            self.repositorio.deshacer_cambios()
            raise