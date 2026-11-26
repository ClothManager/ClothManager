from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class Insumo(Base):
    __tablename__ = "insumos"
    __table_args__ = (
        CheckConstraint(
            "costo_referencia IS NULL OR costo_referencia >= 0",
            name="ck_insumo_costo_no_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    codigo: Mapped[str] = mapped_column(
        String(30, collation="NOCASE"),
        unique=True,
        index=True,
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    tipo_insumo_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    costo_referencia: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    actualizado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
    )


class RequerimientoInsumoReferencia(Base):
    __tablename__ = "requerimientos_insumo_referencia"
    __table_args__ = (
        UniqueConstraint(
            "referencia_id",
            "insumo_id",
            "base_calculo",
            name="uq_requerimiento_referencia_insumo_base",
        ),
        CheckConstraint(
            "cantidad > 0",
            name="ck_requerimiento_cantidad_positiva",
        ),
        CheckConstraint(
            "base_calculo IN ('POR_UNIDAD', 'POR_LOTE')",
            name="ck_requerimiento_base_calculo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    referencia_id: Mapped[int] = mapped_column(
        ForeignKey("referencias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("insumos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    cantidad: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    unidad_medida_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
    )

    base_calculo: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
    )

    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        onupdate=fecha_actual,
        nullable=False,
    )

    actualizado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
    )