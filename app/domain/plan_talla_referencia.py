from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class PlanTallaReferencia(Base):
    __tablename__ = "planes_tallas_referencia"
    __table_args__ = (
        UniqueConstraint(
            "referencia_id",
            "talla_id",
            name="uq_plan_talla_referencia",
        ),
        CheckConstraint(
            "cantidad_planeada BETWEEN 0 AND 1000000",
            name="ck_plan_talla_cantidad",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    referencia_id: Mapped[int] = mapped_column(
        ForeignKey("referencias.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    talla_id: Mapped[int] = mapped_column(
        ForeignKey("tallas.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    cantidad_planeada: Mapped[int] = mapped_column(
        Integer,
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