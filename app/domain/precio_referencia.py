from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
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


class PrecioReferencia(Base):
    __tablename__ = "precios_referencia"
    __table_args__ = (
        UniqueConstraint(
            "referencia_id",
            name="uq_precio_referencia",
        ),
        CheckConstraint(
            "costo_produccion >= 0",
            name="ck_precio_costo_no_negativo",
        ),
        CheckConstraint(
            "precio_detal >= 0",
            name="ck_precio_detal_no_negativo",
        ),
        CheckConstraint(
            "precio_mayorista_nacional >= 0",
            name="ck_precio_nacional_no_negativo",
        ),
        CheckConstraint(
            "precio_mayorista_exportacion >= 0",
            name="ck_precio_exportacion_no_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    referencia_id: Mapped[int] = mapped_column(
        ForeignKey("referencias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    costo_produccion: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    precio_detal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    precio_mayorista_nacional: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    precio_mayorista_exportacion: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    moneda: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        onupdate=fecha_actual,
        nullable=False,
    )

    actualizado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )