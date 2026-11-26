from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def ahora_utc():
    return datetime.now(timezone.utc)


usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column(
        "usuario_id",
        ForeignKey("usuarios.id"),
        primary_key=True,
    ),
    Column(
        "rol_id",
        ForeignKey("roles.id"),
        primary_key=True,
    ),
    Column("asignado_en", DateTime(timezone=True), default=ahora_utc),
)

rol_permisos = Table(
    "rol_permisos",
    Base.metadata,
    Column(
        "rol_id",
        ForeignKey("roles.id"),
        primary_key=True,
    ),
    Column(
        "permiso_id",
        ForeignKey("permisos.id"),
        primary_key=True,
    ),
    Column("asignado_en", DateTime(timezone=True), default=ahora_utc),
)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("correo", name="uq_usuarios_correo"),
        UniqueConstraint("nombre_usuario", name="uq_usuarios_nombre_usuario"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(80), nullable=False)
    apellidos = Column(String(80), nullable=False)
    correo = Column(String(254), nullable=False, index=True)
    nombre_usuario = Column(String(50), nullable=False, index=True)
    area = Column(String(30), nullable=False)
    estado = Column(String(12), nullable=False, default="ACTIVO")
    creado_en = Column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        onupdate=ahora_utc,
    )

    roles = relationship(
        "Rol",
        secondary=usuario_roles,
        back_populates="usuarios",
    )


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(40), nullable=False, unique=True, index=True)
    nombre = Column(String(80), nullable=False)
    descripcion = Column(String(250), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    usuarios = relationship(
        "Usuario",
        secondary=usuario_roles,
        back_populates="roles",
    )
    permisos = relationship(
        "Permiso",
        secondary=rol_permisos,
        back_populates="roles",
    )


class Permiso(Base):
    __tablename__ = "permisos"
    __table_args__ = (
        UniqueConstraint(
            "modulo",
            "recurso",
            "accion",
            name="uq_permisos_modulo_recurso_accion",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    modulo = Column(String(30), nullable=False)
    recurso = Column(String(50), nullable=False)
    accion = Column(String(30), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    roles = relationship(
        "Rol",
        secondary=rol_permisos,
        back_populates="permisos",
    )


class RegistroAuditoria(Base):
    __tablename__ = "registros_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(80), nullable=False)
    accion = Column(String(50), nullable=False)
    entidad = Column(String(50), nullable=False)
    entidad_id = Column(String(50), nullable=True)
    valores_anteriores = Column(JSON, nullable=True)
    valores_nuevos = Column(JSON, nullable=True)
    resultado = Column(String(20), nullable=False, default="EXITOSO")
    creado_en = Column(DateTime(timezone=True), nullable=False, default=ahora_utc)