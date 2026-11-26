from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class Coleccion(Base):
    __tablename__ = "colecciones"
    __table_args__ = (
        CheckConstraint(
            "anio BETWEEN 2000 AND 2200",
            name="ck_coleccion_anio",
        ),
        CheckConstraint(
            "estado IN ('EN_CURSO', 'COMPLETADA')",
            name="ck_coleccion_estado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_inicio_preventa: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cierre_preventa: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_entrega: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        default="EN_CURSO",
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
class SecuenciaColeccion(Base):
    __tablename__ = "secuencias_colecciones"

    anio: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo_numero: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )