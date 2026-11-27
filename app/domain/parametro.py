from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

def fecha_actual():
    return datetime.now(timezone.utc)


class Talla(Base):
    __tablename__ = "tallas"
    __table_args__ = (
        CheckConstraint(
            "codigo IN ('S', 'M', 'L', 'XL', 'XXL')",
            name="ck_talla_codigo_permitido",
        ),
        CheckConstraint(
            "orden BETWEEN 1 AND 5",
            name="ck_talla_orden",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(10), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Color(Base):
    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    creado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
    )
    actualizado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
class AuditoriaParametro(Base):
    __tablename__ = "auditoria_parametros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(30), nullable=False)
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False)
    accion: Mapped[str] = mapped_column(String(20), nullable=False)
    responsable_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )
    antes: Mapped[str | None] = mapped_column(Text, nullable=True)
    despues: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    trace_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)