from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identificacion: Mapped[str] = mapped_column(
        String(30, collation="NOCASE"),
        unique=True,
        index=True,
        nullable=False,
    )
    nombre_razon_social: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(254), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    creado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )


class CompraInsumo(Base):
    __tablename__ = "compras_insumos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('REGISTRADA', 'PARCIAL', 'RECIBIDA', 'CANCELADA')",
            name="ck_compra_insumo_estado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_compra: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )
    proveedor_id: Mapped[int] = mapped_column(
        ForeignKey("proveedores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_compra: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        default="REGISTRADA",
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    creado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class CompraInsumoDetalle(Base):
    __tablename__ = "compras_insumos_detalle"
    __table_args__ = (
        CheckConstraint(
            "cantidad_solicitada > 0",
            name="ck_compra_cantidad_positiva",
        ),
        CheckConstraint(
            "costo_unitario >= 0",
            name="ck_compra_costo_no_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compra_id: Mapped[int] = mapped_column(
        ForeignKey("compras_insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cantidad_solicitada: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )
    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
    )
    costo_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )


class RecepcionInsumo(Base):
    __tablename__ = "recepciones_insumos"
    __table_args__ = (
        UniqueConstraint(
            "clave_idempotencia",
            name="uq_recepcion_clave_idempotencia",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compra_id: Mapped[int] = mapped_column(
        ForeignKey("compras_insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_recepcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(15),
        default="CONFIRMADA",
        nullable=False,
    )
    recibido_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )
    clave_idempotencia: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    solicitud_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )


class RecepcionInsumoDetalle(Base):
    __tablename__ = "recepciones_insumos_detalle"
    __table_args__ = (
        CheckConstraint(
            "cantidad_recibida >= 0",
            name="ck_recepcion_cantidad_no_negativa",
        ),
        UniqueConstraint(
            "recepcion_id",
            "compra_detalle_id",
            name="uq_recepcion_compra_detalle",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recepcion_id: Mapped[int] = mapped_column(
        ForeignKey("recepciones_insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    compra_detalle_id: Mapped[int] = mapped_column(
        ForeignKey("compras_insumos_detalle.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cantidad_recibida: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )
    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
    )
    novedad: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExistenciaInsumo(Base):
    __tablename__ = "existencias_insumos"
    __table_args__ = (
        UniqueConstraint(
            "insumo_id",
            "unidad_medida_id",
            name="uq_existencia_insumo_unidad",
        ),
        CheckConstraint(
            "cantidad_disponible >= 0",
            name="ck_existencia_no_negativa",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("insumos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cantidad_disponible: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        default=Decimal("0"),
        nullable=False,
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        onupdate=fecha_actual,
        nullable=False,
    )


class MovimientoBodega(Base):
    __tablename__ = "movimientos_bodega"
    __table_args__ = (
        UniqueConstraint(
            "recepcion_detalle_id",
            name="uq_movimiento_recepcion_detalle",
        ),
        CheckConstraint(
            "tipo_movimiento = 'ENTRADA'",
            name="ck_movimiento_tipo_entrada",
        ),
        CheckConstraint(
            "cantidad > 0",
            name="ck_movimiento_cantidad_positiva",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_movimiento: Mapped[str] = mapped_column(
        String(12),
        default="ENTRADA",
        nullable=False,
    )
    compra_id: Mapped[int] = mapped_column(
        ForeignKey("compras_insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    recepcion_id: Mapped[int] = mapped_column(
        ForeignKey("recepciones_insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    recepcion_detalle_id: Mapped[int] = mapped_column(
        ForeignKey("recepciones_insumos_detalle.id", ondelete="RESTRICT"),
        nullable=False,
    )
    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )