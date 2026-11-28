from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.domain.compra_insumo import (
    CompraInsumo,
    CompraInsumoDetalle,
    ExistenciaInsumo,
    MovimientoBodega,
    Proveedor,
    RecepcionInsumo,
    RecepcionInsumoDetalle,
)
from app.domain.insumo import Insumo
from app.domain.referencia import Referencia
from app.domain.usuario import (
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)


class CompraInsumoRepository:
    def __init__(self, db: Session):
        self.db = db

    def es_administrador(self, usuario_id: int) -> bool:
        return (
            self.db.query(UsuarioRol)
            .join(Rol, Rol.id == UsuarioRol.rol_id)
            .filter(
                UsuarioRol.usuario_id == usuario_id,
                Rol.codigo == "ADMINISTRADOR",
                Rol.activo.is_(True),
            )
            .first()
            is not None
        )

    def tiene_permiso(
        self,
        usuario_id: int,
        modulo: str,
        recurso: str,
        accion: str,
    ) -> bool:
        return (
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
            is not None
        )

    def obtener_proveedor_activo(self, proveedor_id: int):
        return (
            self.db.query(Proveedor)
            .filter(
                Proveedor.id == proveedor_id,
                Proveedor.activo.is_(True),
            )
            .first()
        )

    def existe_identificacion_proveedor(self, identificacion: str) -> bool:
        return (
            self.db.query(Proveedor.id)
            .filter(
                func.lower(Proveedor.identificacion)
                == identificacion.lower()
            )
            .first()
            is not None
        )

    def agregar_proveedor(self, proveedor: Proveedor) -> Proveedor:
        self.db.add(proveedor)
        self.db.flush()
        return proveedor

    def listar_proveedores(self) -> list[Proveedor]:
        return (
            self.db.query(Proveedor)
            .filter(Proveedor.activo.is_(True))
            .order_by(Proveedor.nombre_razon_social)
            .all()
        )

    def obtener_insumo_activo(self, insumo_id: int):
        return (
            self.db.query(Insumo)
            .filter(
                Insumo.id == insumo_id,
                Insumo.activo.is_(True),
            )
            .first()
        )

    def obtener_unidad_activa(self, unidad_id: int):
        return (
            self.db.query(ValorParametro)
            .join(
                CatalogoParametro,
                CatalogoParametro.id == ValorParametro.catalogo_id,
            )
            .filter(
                ValorParametro.id == unidad_id,
                ValorParametro.activo.is_(True),
                CatalogoParametro.codigo == "UNIDAD_MEDIDA",
                CatalogoParametro.activo.is_(True),
            )
            .first()
        )

    def obtener_referencia(self, referencia_id: int):
        return self.db.get(Referencia, referencia_id)

    def agregar_compra(self, compra: CompraInsumo) -> CompraInsumo:
        self.db.add(compra)
        self.db.flush()
        return compra

    def agregar_detalle_compra(
        self,
        detalle: CompraInsumoDetalle,
    ) -> CompraInsumoDetalle:
        self.db.add(detalle)
        self.db.flush()
        return detalle

    def obtener_compra(self, compra_id: int) -> CompraInsumo | None:
        return self.db.get(CompraInsumo, compra_id)

    def listar_compras(self, estado: str | None = None):
        consulta = self.db.query(CompraInsumo)
        if estado:
            consulta = consulta.filter(
                CompraInsumo.estado == estado.upper()
            )
        return consulta.order_by(CompraInsumo.id.desc()).all()

    def obtener_detalle_compra(self, compra_id: int):
        compra = self.obtener_compra(compra_id)
        if compra is None:
            return None

        proveedor = self.db.get(Proveedor, compra.proveedor_id)
        unidad = aliased(ValorParametro)

        lineas = (
            self.db.query(CompraInsumoDetalle, Insumo, unidad)
            .join(
                Insumo,
                Insumo.id == CompraInsumoDetalle.insumo_id,
            )
            .join(
                unidad,
                unidad.id == CompraInsumoDetalle.unidad_medida_id,
            )
            .filter(CompraInsumoDetalle.compra_id == compra_id)
            .order_by(CompraInsumoDetalle.id)
            .all()
        )
        return compra, proveedor, lineas

    def obtener_linea_compra(self, compra_id: int, detalle_id: int):
        unidad = aliased(ValorParametro)
        return (
            self.db.query(CompraInsumoDetalle, Insumo, unidad)
            .join(Insumo, Insumo.id == CompraInsumoDetalle.insumo_id)
            .join(
                unidad,
                unidad.id == CompraInsumoDetalle.unidad_medida_id,
            )
            .filter(
                CompraInsumoDetalle.compra_id == compra_id,
                CompraInsumoDetalle.id == detalle_id,
            )
            .first()
        )

    def cantidad_recibida_acumulada(self, detalle_id: int) -> Decimal:
        resultado = (
            self.db.query(
                func.coalesce(
                    func.sum(RecepcionInsumoDetalle.cantidad_recibida),
                    0,
                )
            )
            .join(
                RecepcionInsumo,
                RecepcionInsumo.id
                == RecepcionInsumoDetalle.recepcion_id,
            )
            .filter(
                RecepcionInsumoDetalle.compra_detalle_id == detalle_id,
                RecepcionInsumo.estado == "CONFIRMADA",
            )
            .scalar()
        )
        return Decimal(str(resultado or 0))

    def obtener_recepcion_por_clave(self, clave: str):
        return (
            self.db.query(RecepcionInsumo)
            .filter(RecepcionInsumo.clave_idempotencia == clave)
            .first()
        )

    def agregar_recepcion(
        self,
        recepcion: RecepcionInsumo,
    ) -> RecepcionInsumo:
        self.db.add(recepcion)
        self.db.flush()
        return recepcion

    def agregar_detalle_recepcion(
        self,
        detalle: RecepcionInsumoDetalle,
    ) -> RecepcionInsumoDetalle:
        self.db.add(detalle)
        self.db.flush()
        return detalle

    def obtener_existencia(
        self,
        insumo_id: int,
        unidad_medida_id: int,
    ) -> ExistenciaInsumo | None:
        return (
            self.db.query(ExistenciaInsumo)
            .filter(
                ExistenciaInsumo.insumo_id == insumo_id,
                ExistenciaInsumo.unidad_medida_id == unidad_medida_id,
            )
            .with_for_update()
            .first()
        )

    def agregar_existencia(
        self,
        existencia: ExistenciaInsumo,
    ) -> ExistenciaInsumo:
        self.db.add(existencia)
        self.db.flush()
        return existencia

    def agregar_movimiento(
        self,
        movimiento: MovimientoBodega,
    ) -> MovimientoBodega:
        self.db.add(movimiento)
        self.db.flush()
        return movimiento

    def listar_recepciones(self, compra_id: int):
        return (
            self.db.query(RecepcionInsumo)
            .filter(RecepcionInsumo.compra_id == compra_id)
            .order_by(RecepcionInsumo.id)
            .all()
        )

    def obtener_detalles_recepcion(self, recepcion_id: int):
        movimiento = aliased(MovimientoBodega)
        unidad = aliased(ValorParametro)

        return (
            self.db.query(
                RecepcionInsumoDetalle,
                CompraInsumoDetalle,
                Insumo,
                unidad,
                movimiento,
            )
            .join(
                CompraInsumoDetalle,
                CompraInsumoDetalle.id
                == RecepcionInsumoDetalle.compra_detalle_id,
            )
            .join(Insumo, Insumo.id == CompraInsumoDetalle.insumo_id)
            .join(
                unidad,
                unidad.id == RecepcionInsumoDetalle.unidad_medida_id,
            )
            .outerjoin(
                movimiento,
                movimiento.recepcion_detalle_id
                == RecepcionInsumoDetalle.id,
            )
            .filter(RecepcionInsumoDetalle.recepcion_id == recepcion_id)
            .all()
        )

    def listar_existencias(self):
        unidad = aliased(ValorParametro)
        return (
            self.db.query(ExistenciaInsumo, Insumo, unidad)
            .join(Insumo, Insumo.id == ExistenciaInsumo.insumo_id)
            .join(
                unidad,
                unidad.id == ExistenciaInsumo.unidad_medida_id,
            )
            .order_by(Insumo.codigo)
            .all()
        )

    def registrar_auditoria(
        self,
        catalogo: str,
        registro_id: int,
        responsable_id: int,
        accion: str,
        antes: str | None,
        despues: str,
        trace_id: str,
    ) -> None:
        self.db.add(
            AuditoriaCatalogo(
                catalogo_codigo=catalogo,
                registro_id=registro_id,
                responsable_id=responsable_id,
                accion=accion,
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