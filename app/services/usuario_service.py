import json
from datetime import datetime, timezone
from fastapi import HTTPException

from app.domain.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository


AREAS_VALIDAS = {
    "ADMINISTRACION",
    "PRODUCCION",
    "BODEGA",
    "VENTAS",
    "CONTABILIDAD",
}

ESTADOS_VALIDOS = {"ACTIVO", "INACTIVO"}


class UsuarioService:
    def __init__(self, repositorio: UsuarioRepository):
        self.repositorio = repositorio

    def crear_usuario(self, datos: dict, responsable_id: int) -> Usuario:
        correo = datos["correo"].strip().lower()
        nombre_usuario = datos["nombre_usuario"].strip().lower()
        codigos_roles = datos.get("roles", [])

        if self.repositorio.obtener_por_correo(correo):
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario con ese correo",
            )

        if self.repositorio.obtener_por_nombre_usuario(nombre_usuario):
            raise HTTPException(
                status_code=409,
                detail="Ya existe ese nombre de usuario",
            )

        area = datos["area"].upper()
        estado = datos.get("estado", "ACTIVO").upper()

        if area not in AREAS_VALIDAS:
            raise HTTPException(status_code=422, detail="Área no válida")

        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=422, detail="Estado no válido")

        roles = self.repositorio.obtener_roles_activos(codigos_roles)
        if len(roles) != len(set(codigos_roles)):
            raise HTTPException(
                status_code=422,
                detail="Uno o más roles no existen o están inactivos",
            )

        usuario = Usuario(
            nombres=datos["nombres"].strip(),
            apellidos=datos["apellidos"].strip(),
            correo=correo,
            nombre_usuario=nombre_usuario,
            area=area,
            estado=estado,
            creado_por=responsable_id,
        )

        try:
            self.repositorio.agregar(usuario)
            self.repositorio.asignar_roles(
                usuario.id,
                roles,
                responsable_id,
            )
            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=usuario.id,
                responsable_id=responsable_id,
                accion="CREAR_USUARIO",
                despues=json.dumps(
                    {
                        "correo": correo,
                        "nombre_usuario": nombre_usuario,
                        "area": area,
                        "roles": codigos_roles,
                        "estado": estado,
                    },
                    ensure_ascii=False,
                ),
            )
            self.repositorio.guardar_cambios()
            return usuario
        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def listar_usuarios(
        self,
        buscar: str | None = None,
        area: str | None = None,
        estado: str | None = None,
        rol: str | None = None,
    ) -> list[Usuario]:
        return self.repositorio.listar(
            buscar=buscar,
            area=area,
            estado=estado,
            rol=rol,
        )
    def obtener_usuario(self, usuario_id: int) -> Usuario:
        usuario = self.repositorio.obtener_por_id(usuario_id)

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        return usuario
    def actualizar_usuario(
        self,
        usuario_id: int,
        datos: dict,
        responsable_id: int,
    ) -> Usuario:
        usuario = self.repositorio.obtener_por_id(usuario_id)

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        cambios = {
            campo: valor
            for campo, valor in datos.items()
            if valor is not None
        }

        if "correo" in cambios:
            cambios["correo"] = cambios["correo"].strip().lower()
            existente = self.repositorio.obtener_por_correo(cambios["correo"])

            if existente is not None and existente.id != usuario.id:
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe un usuario con ese correo",
                )

        if "nombre_usuario" in cambios:
            cambios["nombre_usuario"] = cambios["nombre_usuario"].strip().lower()
            existente = self.repositorio.obtener_por_nombre_usuario(
                cambios["nombre_usuario"]
            )

            if existente is not None and existente.id != usuario.id:
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe ese nombre de usuario",
                )

        if not cambios:
            return usuario

        antes = {
            campo: getattr(usuario, campo)
            for campo in cambios
        }

        for campo, valor in cambios.items():
            if campo in {"nombres", "apellidos"}:
                valor = valor.strip()
            if campo == "area":
                valor = valor.upper()
            if campo == "estado":
                valor = valor.upper()

            setattr(usuario, campo, valor)

        usuario.actualizado_en = datetime.now(timezone.utc)
        usuario.actualizado_por = responsable_id

        try:
            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=usuario.id,
                responsable_id=responsable_id,
                accion="ACTUALIZAR_USUARIO",
                antes=json.dumps(antes, ensure_ascii=False, default=str),
                despues=json.dumps(cambios, ensure_ascii=False, default=str),
            )
            self.repositorio.guardar_cambios()
            return usuario
        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def inactivar_usuario(
        self,
        usuario_id: int,
        responsable_id: int,
    ) -> Usuario:
        usuario = self.repositorio.obtener_por_id(usuario_id)

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        if usuario.estado == "INACTIVO":
            return usuario

        usuario.estado = "INACTIVO"
        usuario.actualizado_en = datetime.now(timezone.utc)
        usuario.actualizado_por = responsable_id

        try:
            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=usuario.id,
                responsable_id=responsable_id,
                accion="INACTIVAR_USUARIO",
                antes=json.dumps({"estado": "ACTIVO"}),
                despues=json.dumps({"estado": "INACTIVO"}),
            )
            self.repositorio.guardar_cambios()
            return usuario
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def actualizar_roles(
        self,
        usuario_id: int,
        codigos_roles: list[str],
        responsable_id: int,
    ) -> Usuario:
        usuario = self.repositorio.obtener_por_id(usuario_id)

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        roles = self.repositorio.obtener_roles_activos(codigos_roles)

        if len(roles) != len(set(codigos_roles)):
            raise HTTPException(
                status_code=422,
                detail="Uno o más roles no existen o están inactivos",
            )

        roles_anteriores = self.repositorio.listar_codigos_roles(usuario_id)

        try:
            self.repositorio.quitar_roles(usuario_id)
            self.repositorio.asignar_roles(
                usuario_id,
                roles,
                responsable_id,
            )
            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=usuario_id,
                responsable_id=responsable_id,
                accion="ACTUALIZAR_ROLES",
                antes=json.dumps(roles_anteriores, ensure_ascii=False),
                despues=json.dumps(codigos_roles, ensure_ascii=False),
            )
            self.repositorio.guardar_cambios()
            return usuario
        except Exception:
            self.repositorio.deshacer_cambios()
            raise