from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class Referencia(Base):
    __tablename__ = "referencias"
    __table_args__ = (
        CheckConstraint(
            "anio BETWEEN 2000 AND 2200",
            name="ck_referencia_anio",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    codigo: Mapped[str] = mapped_column(
        String(30, collation="NOCASE"),
        unique=True,
        index=True,
        nullable=False,
    )

    nombre_referencia: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    coleccion_id: Mapped[int] = mapped_column(
        ForeignKey("colecciones.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    color_id: Mapped[int] = mapped_column(
        ForeignKey("colores.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    anio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
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