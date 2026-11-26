import json
from fastapi import HTTPException
from app.domain.usuario import Rol
from app.domain.usuario import Rol
from app.repositories.rol_repository import RolRepository
from app.domain.usuario import Permiso, Rol

class RolService:
    def __init__(self, repositorio: RolRepository):
        self.repositorio = repositorio

    def listar_roles(self) -> list[Rol]:
        return self.repositorio.listar()
    def crear_rol(
        self,
        datos: dict,
        responsable_id: int,
    ) -> Rol:
        codigo = datos["codigo"].strip().upper()

        if self.repositorio.obtener_por_codigo(codigo):
            raise HTTPException(
                status_code=409,
                detail="Ya existe un rol con ese código",
            )

        rol = Rol(
            codigo=codigo,
            nombre=datos["nombre"].strip(),
            descripcion=datos.get("descripcion"),
            activo=True,
        )

        try:
            self.repositorio.agregar(rol)
            self.repositorio.registrar_auditoria(
                responsable_id=responsable_id,
                accion="CREAR_ROL",
                despues=json.dumps(
                    {
                        "codigo": rol.codigo,
                        "nombre": rol.nombre,
                        "descripcion": rol.descripcion,
                    },
                    ensure_ascii=False,
                ),
            )
            self.repositorio.guardar_cambios()
            return rol
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def actualizar_rol(
        self,
        codigo: str,
        datos: dict,
        responsable_id: int,
    ) -> Rol:
        rol = self.repositorio.obtener_por_codigo(codigo.strip().upper())

        if rol is None:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        cambios = {
            campo: valor
            for campo, valor in datos.items()
            if valor is not None
        }

        if not cambios:
            return rol

        antes = {
            campo: getattr(rol, campo)
            for campo in cambios
        }

        for campo, valor in cambios.items():
            setattr(rol, campo, valor)

        try:
            self.repositorio.registrar_auditoria(
                responsable_id=responsable_id,
                accion="ACTUALIZAR_ROL",
                despues=json.dumps(
                    {"antes": antes, "despues": cambios},
                    ensure_ascii=False,
                ),
            )
            self.repositorio.guardar_cambios()
            return rol
        except Exception:
            self.repositorio.deshacer_cambios()
            raise
    def actualizar_permisos(
        self,
        codigo: str,
        permisos_datos: list[dict],
        responsable_id: int,
    ) -> Rol:
        rol = self.repositorio.obtener_por_codigo(codigo.strip().upper())

        if rol is None:
            raise HTTPException(
                status_code=404,
                detail="Rol no encontrado",
            )

        claves = [
            (p["modulo"], p["recurso"], p["accion"])
            for p in permisos_datos
        ]

        if len(claves) != len(set(claves)):
            raise HTTPException(
                status_code=422,
                detail="La lista contiene permisos duplicados",
            )

        try:
            permisos = []

            for datos in permisos_datos:
                permiso = self.repositorio.obtener_permiso(
                    modulo=datos["modulo"],
                    recurso=datos["recurso"],
                    accion=datos["accion"],
                )

                if permiso is None:
                    permiso = Permiso(
                        modulo=datos["modulo"],
                        recurso=datos["recurso"],
                        accion=datos["accion"],
                        activo=True,
                    )
                    permiso = self.repositorio.agregar_permiso(permiso)

                if not permiso.activo:
                    raise HTTPException(
                        status_code=422,
                        detail="No se puede asignar un permiso inactivo",
                    )

                permisos.append(permiso)

            anteriores = [
                {
                    "modulo": p.modulo,
                    "recurso": p.recurso,
                    "accion": p.accion,
                }
                for p in self.repositorio.listar_permisos(rol.id)
            ]

            self.repositorio.quitar_permisos(rol.id)

            for permiso in permisos:
                self.repositorio.asignar_permiso(
                    rol_id=rol.id,
                    permiso_id=permiso.id,
                    responsable_id=responsable_id,
                )

            self.repositorio.registrar_auditoria(
                responsable_id=responsable_id,
                accion="ACTUALIZAR_PERMISOS_ROL",
                antes=json.dumps(anteriores, ensure_ascii=False),
                despues=json.dumps(permisos_datos, ensure_ascii=False),
            )

            self.repositorio.guardar_cambios()
            return rol

        except Exception:
            self.repositorio.deshacer_cambios()
            raise