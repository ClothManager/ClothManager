from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "area IN ('ADMINISTRACION', 'PRODUCCION', 'BODEGA', 'VENTAS', 'CONTABILIDAD')",
            name="ck_usuario_area",
        ),
        CheckConstraint(
            "estado IN ('ACTIVO', 'INACTIVO')",
            name="ck_usuario_estado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombres: Mapped[str] = mapped_column(String(80), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(80), nullable=False)
    correo: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    nombre_usuario: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    area: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(12), default="ACTIVO", nullable=False
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=fecha_actual, nullable=False
    )
    creado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actualizado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(250), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class Permiso(Base):
    __tablename__ = "permisos"
    __table_args__ = (
        UniqueConstraint(
            "modulo",
            "recurso",
            "accion",
            name="uq_permiso_modulo_recurso_accion",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modulo: Mapped[str] = mapped_column(String(30), nullable=False)
    recurso: Mapped[str] = mapped_column(String(50), nullable=False)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), primary_key=True
    )
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), primary_key=True
    )
    asignado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=fecha_actual, nullable=False
    )
    asignado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )


class RolPermiso(Base):
    __tablename__ = "roles_permisos"

    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), primary_key=True
    )
    permiso_id: Mapped[int] = mapped_column(
        ForeignKey("permisos.id"), primary_key=True
    )
    asignado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=fecha_actual, nullable=False
    )
    asignado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_objetivo_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    responsable_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    accion: Mapped[str] = mapped_column(String(40), nullable=False)
    antes: Mapped[str | None] = mapped_column(Text, nullable=True)
    despues: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str] = mapped_column(
        String(20), default="EXITOSO", nullable=False
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=fecha_actual, nullable=False
    )