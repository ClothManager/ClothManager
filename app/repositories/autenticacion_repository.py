from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.autenticacion import (
    CredencialUsuario,
    EventoSeguridad,
    SesionUsuario,
    TokenCuenta,
)
from app.domain.usuario import Usuario


class AutenticacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_usuario(self, identificador: str) -> Usuario | None:
        identificador = identificador.strip().lower()

        return (
            self.db.query(Usuario)
            .filter(
                or_(
                    func.lower(Usuario.nombre_usuario) == identificador,
                    func.lower(Usuario.correo) == identificador,
                )
            )
            .first()
        )

    def obtener_credencial(
        self,
        usuario_id: int,
    ) -> CredencialUsuario | None:
        return self.db.get(CredencialUsuario, usuario_id)

    def agregar_credencial(
        self,
        credencial: CredencialUsuario,
    ) -> CredencialUsuario:
        self.db.add(credencial)
        self.db.flush()
        return credencial

    def obtener_sesion(
        self,
        sesion_id: int,
    ) -> SesionUsuario | None:
        return self.db.get(SesionUsuario, sesion_id)

    def buscar_sesion_por_refresh_hash(
        self,
        token_hash: str,
    ) -> SesionUsuario | None:
        return (
            self.db.query(SesionUsuario)
            .filter(SesionUsuario.token_renovacion_hash == token_hash)
            .first()
        )

    def listar_sesiones(
        self,
        usuario_id: int,
    ) -> list[SesionUsuario]:
        return (
            self.db.query(SesionUsuario)
            .filter(SesionUsuario.usuario_id == usuario_id)
            .order_by(SesionUsuario.creada_en.desc())
            .all()
        )

    def agregar_sesion(
        self,
        sesion: SesionUsuario,
    ) -> SesionUsuario:
        self.db.add(sesion)
        self.db.flush()
        return sesion

    def revocar_sesion(self, sesion: SesionUsuario) -> None:
        if sesion.revocada_en is None:
            sesion.revocada_en = datetime.now(timezone.utc)
            self.db.flush()

    def revocar_todas_las_sesiones(self, usuario_id: int) -> None:
        ahora = datetime.now(timezone.utc)

        (
            self.db.query(SesionUsuario)
            .filter(
                SesionUsuario.usuario_id == usuario_id,
                SesionUsuario.revocada_en.is_(None),
            )
            .update(
                {"revocada_en": ahora},
                synchronize_session=False,
            )
        )
        self.db.flush()

    def buscar_token_cuenta(
        self,
        token_hash: str,
        tipo: str,
    ) -> TokenCuenta | None:
        return (
            self.db.query(TokenCuenta)
            .filter(
                TokenCuenta.token_hash == token_hash,
                TokenCuenta.tipo == tipo,
            )
            .first()
        )

    def agregar_token_cuenta(
        self,
        token: TokenCuenta,
    ) -> TokenCuenta:
        self.db.add(token)
        self.db.flush()
        return token

    def invalidar_tokens_cuenta(
        self,
        usuario_id: int,
        tipo: str,
    ) -> None:
        (
            self.db.query(TokenCuenta)
            .filter(
                TokenCuenta.usuario_id == usuario_id,
                TokenCuenta.tipo == tipo,
                TokenCuenta.usado_en.is_(None),
            )
            .update(
                {"usado_en": datetime.now(timezone.utc)},
                synchronize_session=False,
            )
        )
        self.db.flush()

    def registrar_evento(
        self,
        evento: EventoSeguridad,
    ) -> EventoSeguridad:
        self.db.add(evento)
        self.db.flush()
        return evento

    def guardar_cambios(self) -> None:
        self.db.commit()

    def deshacer_cambios(self) -> None:
        self.db.rollback()
    def obtener_usuario_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)