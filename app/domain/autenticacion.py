from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class CredencialUsuario(Base):
    __tablename__ = "credenciales_usuarios"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        primary_key=True,
    )
    hash_contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    actualizada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    fallos_consecutivos: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    bloqueada_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    debe_cambiar_contrasena: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


class SesionUsuario(Base):
    __tablename__ = "sesiones_usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    token_renovacion_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    expira_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revocada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ultimo_uso_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    dispositivo: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )


class TokenCuenta(Base):
    __tablename__ = "tokens_cuenta"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ACTIVACION', 'RECUPERACION')",
            name="ck_token_cuenta_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    expira_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    usado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class EventoSeguridad(Base):
    __tablename__ = "eventos_seguridad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )
    evento: Mapped[str] = mapped_column(String(40), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_actual,
        nullable=False,
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    detalle_seguro: Mapped[str | None] = mapped_column(Text, nullable=True)