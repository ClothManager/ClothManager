from sqlalchemy.orm import Session

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.domain.precio_referencia import PrecioReferencia
from app.domain.referencia import Referencia
from app.domain.usuario import (
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)


class PrecioReferenciaRepository:
    def __init__(self, db: Session):
        self.db = db

    def es_administrador(self, usuario_id: int) -> bool:
        asignacion = (
            self.db.query(UsuarioRol)
            .join(Rol, Rol.id == UsuarioRol.rol_id)
            .filter(
                UsuarioRol.usuario_id == usuario_id,
                Rol.codigo == "ADMINISTRADOR",
                Rol.activo.is_(True),
            )
            .first()
        )

        return asignacion is not None

    def tiene_permiso(
        self,
        usuario_id: int,
        modulo: str,
        recurso: str,
        accion: str,
    ) -> bool:
        permiso = (
            self.db.query(Permiso.id)
            .select_from(Usuario)
            .join(
                UsuarioRol,
                UsuarioRol.usuario_id == Usuario.id,
            )
            .join(
                Rol,
                Rol.id == UsuarioRol.rol_id,
            )
            .join(
                RolPermiso,
                RolPermiso.rol_id == Rol.id,
            )
            .join(
                Permiso,
                Permiso.id == RolPermiso.permiso_id,
            )
            .filter(
                Usuario.id == usuario_id,
                Usuario.estado == "ACTIVO",
                Rol.activo.is_(True),
                Permiso.activo.is_(True),
                Permiso.modulo == modulo.upper(),
                Permiso.recurso == recurso.upper(),
                Permiso.accion == accion.upper(),
            )
            .first()
        )

        return permiso is not None

    def obtener_referencia(
        self,
        referencia_id: int,
    ) -> Referencia | None:
        return self.db.get(Referencia, referencia_id)

    def obtener_moneda_activa(
        self,
        codigo_moneda: str,
    ) -> ValorParametro | None:
        return (
            self.db.query(ValorParametro)
            .join(
                CatalogoParametro,
                CatalogoParametro.id == ValorParametro.catalogo_id,
            )
            .filter(
                CatalogoParametro.codigo == "MONEDA",
                CatalogoParametro.activo.is_(True),
                ValorParametro.codigo == codigo_moneda.upper(),
                ValorParametro.activo.is_(True),
            )
            .first()
        )

    def obtener_por_referencia(
        self,
        referencia_id: int,
    ) -> PrecioReferencia | None:
        return (
            self.db.query(PrecioReferencia)
            .filter(
                PrecioReferencia.referencia_id == referencia_id,
            )
            .first()
        )

    def agregar(
        self,
        precios: PrecioReferencia,
    ) -> PrecioReferencia:
        self.db.add(precios)
        self.db.flush()
        return precios

    def registrar_auditoria(
        self,
        registro_id: int,
        responsable_id: int,
        accion: str,
        antes: str | None,
        despues: str,
        trace_id: str,
    ) -> None:
        self.db.add(
            AuditoriaCatalogo(
                catalogo_codigo="PRECIOS_REFERENCIA",
                registro_id=registro_id,
                accion=accion,
                responsable_id=responsable_id,
                antes=antes,
                despues=despues,
                motivo=None,
                trace_id=trace_id,
            )
        )
        self.db.flush()

    def guardar(self) -> None:
        self.db.commit()

    def deshacer(self) -> None:
        self.db.rollback()