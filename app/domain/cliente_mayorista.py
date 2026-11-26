
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def fecha_actual():
    return datetime.now(timezone.utc)


class ClienteMayorista(Base):
    __tablename__ = "clientes_mayoristas"

    __table_args__ = (
        UniqueConstraint(
            "tipo_documento_id",
            "identificacion",
            name="uq_cliente_mayorista_documento_identificacion",
        ),
        CheckConstraint(
            "estado IN ('ACTIVO', 'INACTIVO')",
            name="ck_cliente_mayorista_estado",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tipo_documento_id: Mapped[int] = mapped_column(
        ForeignKey(
            "valores_parametro.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    identificacion: Mapped[str] = mapped_column(
        String(30, collation="NOCASE"),
        nullable=False,
    )

    nombre_razon_social: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    correo: Mapped[str | None] = mapped_column(
        String(254),
        nullable=True,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    tipo_mayorista_id: Mapped[int] = mapped_column(
        ForeignKey(
            "valores_parametro.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    estado: Mapped[str] = mapped_column(
        String(12),
        default="ACTIVO",
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
