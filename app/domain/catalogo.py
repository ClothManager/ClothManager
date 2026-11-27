from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class CatalogoParametro(Base):
    __tablename__ = "catalogos_parametro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
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


class ValorParametro(Base):
    __tablename__ = "valores_parametro"
    __table_args__ = (
        UniqueConstraint(
            "catalogo_id",
            "codigo",
            name="uq_valor_catalogo_codigo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalogo_id: Mapped[int] = mapped_column(
        ForeignKey("catalogos_parametro.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    orden: Mapped[int] = mapped_column(
        Integer,
        default=1,
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


class AuditoriaCatalogo(Base):
    __tablename__ = "auditoria_catalogos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalogo_codigo: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False)
    accion: Mapped[str] = mapped_column(String(20), nullable=False)
    responsable_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )
    antes: Mapped[str | None] = mapped_column(Text, nullable=True)
    despues: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )
    trace_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )


class ReferenciaValorParametro(Base):
    __tablename__ = "referencias_valores_parametro"
    __table_args__ = (
        UniqueConstraint(
            "valor_id",
            "entidad",
            "entidad_id",
            "campo",
            name="uq_referencia_valor_entidad_campo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    valor_id: Mapped[int] = mapped_column(
        ForeignKey("valores_parametro.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entidad: Mapped[str] = mapped_column(String(40), nullable=False)
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False)
    campo: Mapped[str] = mapped_column(String(40), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )