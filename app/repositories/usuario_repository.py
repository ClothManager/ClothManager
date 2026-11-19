from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.usuario import Auditoria, Rol, Usuario, UsuarioRol


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        return (
            self.db.query(Usuario)
            .filter(Usuario.correo == correo.lower())
            .first()
        )

    def obtener_por_nombre_usuario(
        self, nombre_usuario: str
    ) -> Usuario | None:
        return (
            self.db.query(Usuario)
            .filter(Usuario.nombre_usuario == nombre_usuario.lower())
            .first()
        )

    def listar(
        self,
        buscar: str | None = None,
        area: str | None = None,
        estado: str | None = None,
        rol: str | None = None,
    ) -> list[Usuario]:
        consulta = self.db.query(Usuario)

        if buscar:
            termino = f"%{buscar.strip()}%"
            consulta = consulta.filter(
                or_(
                    Usuario.nombres.ilike(termino),
                    Usuario.apellidos.ilike(termino),
                    Usuario.correo.ilike(termino),
                    Usuario.nombre_usuario.ilike(termino),
                )
            )

        if area:
            consulta = consulta.filter(Usuario.area == area)

        if estado:
            consulta = consulta.filter(Usuario.estado == estado)

        if rol:
            consulta = (
                consulta.join(UsuarioRol)
                .join(Rol)
                .filter(Rol.codigo == rol)
            )

        return consulta.order_by(Usuario.id).all()

    def agregar(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def obtener_roles_activos(self, codigos: list[str]) -> list[Rol]:
        if not codigos:
            return []

        return (
            self.db.query(Rol)
            .filter(
                Rol.codigo.in_(codigos),
                Rol.activo.is_(True),
            )
            .all()
        )

    def asignar_roles(
        self,
        usuario_id: int,
        roles: list[Rol],
        responsable_id: int,
    ) -> None:
        for rol in roles:
            asignacion = UsuarioRol(
                usuario_id=usuario_id,
                rol_id=rol.id,
                asignado_por=responsable_id,
            )
            self.db.add(asignacion)

        self.db.flush()

    def quitar_roles(self, usuario_id: int) -> None:
        (
            self.db.query(UsuarioRol)
            .filter(UsuarioRol.usuario_id == usuario_id)
            .delete()
        )
        self.db.flush()

    def registrar_auditoria(
        self,
        usuario_objetivo_id: int | None,
        responsable_id: int,
        accion: str,
        antes: str | None = None,
        despues: str | None = None,
    ) -> None:
        registro = Auditoria(
            usuario_objetivo_id=usuario_objetivo_id,
            responsable_id=responsable_id,
            accion=accion,
            antes=antes,
            despues=despues,
        )
        self.db.add(registro)
        self.db.flush()

    def guardar_cambios(self) -> None:
        self.db.commit()

    def deshacer_cambios(self) -> None:
        self.db.rollback()

    def listar_codigos_roles(self, usuario_id: int) -> list[str]:
        resultados = (
            self.db.query(Rol.codigo)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .filter(UsuarioRol.usuario_id == usuario_id)
            .all()
        )
        return [resultado[0] for resultado in resultados]