from sqlalchemy.orm import Session
from app.domain.usuario import Auditoria, Permiso, Rol, RolPermiso
from app.domain.usuario import Permiso, Rol, RolPermiso
from sqlalchemy.orm import Session

from app.domain.usuario import (
    Auditoria,
    Permiso,
    Rol,
    RolPermiso,
)


class RolRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Rol]:
        return self.db.query(Rol).order_by(Rol.codigo).all()

    def listar_permisos(self, rol_id: int) -> list[Permiso]:
        return (
            self.db.query(Permiso)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .filter(
                RolPermiso.rol_id == rol_id,
                Permiso.activo.is_(True),
            )
            .all()
        )

    def obtener_por_codigo(self, codigo: str) -> Rol | None:
        return (
            self.db.query(Rol)
            .filter(Rol.codigo == codigo)
            .first()
        )

    def agregar(self, rol: Rol) -> Rol:
        self.db.add(rol)
        self.db.flush()
        return rol

    def registrar_auditoria(
        self,
        responsable_id: int,
        accion: str,
        despues: str,
    ) -> None:
        self.db.add(
            Auditoria(
                responsable_id=responsable_id,
                accion=accion,
                despues=despues,
            )
        )
        self.db.flush()

    def guardar_cambios(self) -> None:
        self.db.commit()

    def deshacer_cambios(self) -> None:
        self.db.rollback()
class RolRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Rol]:
        return self.db.query(Rol).order_by(Rol.codigo).all()

    def obtener_por_codigo(self, codigo: str) -> Rol | None:
        return (
            self.db.query(Rol)
            .filter(Rol.codigo == codigo)
            .first()
        )

    def listar_permisos(self, rol_id: int) -> list[Permiso]:
        return (
            self.db.query(Permiso)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .filter(
                RolPermiso.rol_id == rol_id,
                Permiso.activo.is_(True),
            )
            .all()
        )

    def obtener_permiso(
        self,
        modulo: str,
        recurso: str,
        accion: str,
    ) -> Permiso | None:
        return (
            self.db.query(Permiso)
            .filter(
                Permiso.modulo == modulo,
                Permiso.recurso == recurso,
                Permiso.accion == accion,
            )
            .first()
        )

    def agregar(self, rol: Rol) -> Rol:
        self.db.add(rol)
        self.db.flush()
        return rol

    def agregar_permiso(self, permiso: Permiso) -> Permiso:
        self.db.add(permiso)
        self.db.flush()
        return permiso

    def quitar_permisos(self, rol_id: int) -> None:
        (
            self.db.query(RolPermiso)
            .filter(RolPermiso.rol_id == rol_id)
            .delete()
        )
        self.db.flush()

    def asignar_permiso(
        self,
        rol_id: int,
        permiso_id: int,
        responsable_id: int,
    ) -> None:
        asignacion = RolPermiso(
            rol_id=rol_id,
            permiso_id=permiso_id,
            asignado_por=responsable_id,
        )
        self.db.add(asignacion)
        self.db.flush()

    def registrar_auditoria(
        self,
        responsable_id: int,
        accion: str,
        despues: str,
        antes: str | None = None,
    ) -> None:
        registro = Auditoria(
            responsable_id=responsable_id,
            accion=accion,
            antes=antes,
            despues=despues,
        )
        self.db.add(registro)
        self.db.flush()

    def guardar_cambios(self) -> None:
        self.db.commit()

    def deshacer_cambios(self) -> None:
        self.db.rollback()