from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.domain.insumo import Insumo, RequerimientoInsumoReferencia
from app.domain.referencia import Referencia
from app.domain.usuario import (
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)


class InsumoRepository:
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
            .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
            .join(Rol, Rol.id == UsuarioRol.rol_id)
            .join(RolPermiso, RolPermiso.rol_id == Rol.id)
            .join(Permiso, Permiso.id == RolPermiso.permiso_id)
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

    def obtener_referencia(self, referencia_id: int) -> Referencia | None:
        return self.db.get(Referencia, referencia_id)

    def obtener_valor_catalogo_activo(
        self,
        valor_id: int,
        codigo_catalogo: str,
    ) -> ValorParametro | None:
        return (
            self.db.query(ValorParametro)
            .join(
                CatalogoParametro,
                CatalogoParametro.id == ValorParametro.catalogo_id,
            )
            .filter(
                ValorParametro.id == valor_id,
                ValorParametro.activo.is_(True),
                CatalogoParametro.codigo == codigo_catalogo.upper(),
                CatalogoParametro.activo.is_(True),
            )
            .first()
        )

    def obtener_unidad_activa(
        self,
        unidad_id: int,
    ) -> ValorParametro | None:
        return self.obtener_valor_catalogo_activo(
            unidad_id,
            "UNIDAD_MEDIDA",
        )

    def obtener_tipo_insumo_activo(
        self,
        tipo_id: int,
    ) -> ValorParametro | None:
        return self.obtener_valor_catalogo_activo(
            tipo_id,
            "TIPO_INSUMO",
        )

    def existe_codigo_insumo(self, codigo: str) -> bool:
        return (
            self.db.query(Insumo.id)
            .filter(func.lower(Insumo.codigo) == codigo.lower())
            .first()
            is not None
        )

    def agregar_insumo(self, insumo: Insumo) -> Insumo:
        self.db.add(insumo)
        self.db.flush()
        return insumo

    def obtener_insumo_activo(self, insumo_id: int) -> Insumo | None:
        return (
            self.db.query(Insumo)
            .filter(
                Insumo.id == insumo_id,
                Insumo.activo.is_(True),
            )
            .first()
        )

    def listar_insumos_activos(self) -> list[tuple]:
        tipo = aliased(ValorParametro)
        unidad = aliased(ValorParametro)

        return (
            self.db.query(Insumo, tipo, unidad)
            .join(tipo, tipo.id == Insumo.tipo_insumo_id)
            .join(unidad, unidad.id == Insumo.unidad_medida_id)
            .filter(Insumo.activo.is_(True))
            .order_by(Insumo.codigo)
            .all()
        )

    def obtener_requerimientos(
        self,
        referencia_id: int,
        base_calculo: str | None = None,
    ) -> list[tuple]:
        unidad = aliased(ValorParametro)

        consulta = (
            self.db.query(
                RequerimientoInsumoReferencia,
                Insumo,
                unidad,
            )
            .join(
                Insumo,
                Insumo.id == RequerimientoInsumoReferencia.insumo_id,
            )
            .join(
                unidad,
                unidad.id
                == RequerimientoInsumoReferencia.unidad_medida_id,
            )
            .filter(
                RequerimientoInsumoReferencia.referencia_id
                == referencia_id
            )
        )

        if base_calculo is not None:
            consulta = consulta.filter(
                RequerimientoInsumoReferencia.base_calculo
                == base_calculo.upper()
            )

        return (
            consulta
            .order_by(
                RequerimientoInsumoReferencia.base_calculo,
                Insumo.codigo,
            )
            .all()
        )

    def reemplazar_requerimientos(
        self,
        referencia_id: int,
        base_calculo: str,
        lineas: list[dict],
        responsable_id: int,
    ) -> None:
        (
            self.db.query(RequerimientoInsumoReferencia)
            .filter(
                RequerimientoInsumoReferencia.referencia_id
                == referencia_id,
                RequerimientoInsumoReferencia.base_calculo
                == base_calculo,
            )
            .delete(synchronize_session=False)
        )

        for linea in lineas:
            self.db.add(
                RequerimientoInsumoReferencia(
                    referencia_id=referencia_id,
                    insumo_id=linea["insumo_id"],
                    cantidad=linea["cantidad"],
                    unidad_medida_id=linea["unidad_medida_id"],
                    base_calculo=base_calculo,
                    actualizado_por=responsable_id,
                )
            )

        self.db.flush()

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
                catalogo_codigo="REQUERIMIENTOS_INSUMOS",
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