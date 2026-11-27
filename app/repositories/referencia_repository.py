
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.domain.coleccion import Coleccion
from app.domain.parametro import Color
from app.domain.referencia import Referencia
from app.domain.usuario import Rol, UsuarioRol


class ReferenciaRepository:
    def __init__(self, db: Session):
        self.db = db

    def es_administrador(self, usuario_id: int) -> bool:
        asignacion = (
            self.db.query(UsuarioRol)
            .join(
                Rol,
                Rol.id == UsuarioRol.rol_id,
            )
            .filter(
                UsuarioRol.usuario_id == usuario_id,
                Rol.codigo.in_(
                    ("SUPERADMINISTRADOR", "ADMINISTRADOR")
                ),
                Rol.activo.is_(True),
            )
            .first()
        )

        return asignacion is not None

    def obtener_coleccion(self, coleccion_id: int) -> Coleccion | None:
        return self.db.get(Coleccion, coleccion_id)

    def obtener_color_activo(self, color_id: int) -> Color | None:
        return (
            self.db.query(Color)
            .filter(
                Color.id == color_id,
                Color.activo.is_(True),
            )
            .first()
        )

    def obtener_tipo_prenda_activo(
        self,
        categoria_id: int,
    ) -> ValorParametro | None:
        return (
            self.db.query(ValorParametro)
            .join(
                CatalogoParametro,
                CatalogoParametro.id == ValorParametro.catalogo_id,
            )
            .filter(
                ValorParametro.id == categoria_id,
                ValorParametro.activo.is_(True),
                CatalogoParametro.codigo == "TIPO_PRENDA",
                CatalogoParametro.activo.is_(True),
            )
            .first()
        )

    def existe_codigo(self, codigo: str) -> bool:
        return (
            self.db.query(Referencia.id)
            .filter(
                func.lower(Referencia.codigo) == codigo.lower()
            )
            .first()
            is not None
        )

    def agregar(self, referencia: Referencia) -> Referencia:
        self.db.add(referencia)
        self.db.flush()
        return referencia

    def obtener_detalle(
        self,
        referencia_id: int,
    ) -> tuple[Referencia, Color, Coleccion, ValorParametro] | None:
        return (
            self.db.query(
                Referencia,
                Color,
                Coleccion,
                ValorParametro,
            )
            .join(Color, Color.id == Referencia.color_id)
            .join(Coleccion, Coleccion.id == Referencia.coleccion_id)
            .join(
                ValorParametro,
                ValorParametro.id == Referencia.categoria_id,
            )
            .filter(Referencia.id == referencia_id)
            .first()
        )

    def listar(
        self,
        buscar: str | None,
        coleccion_id: int | None,
        anio: int | None,
        color_id: int | None,
        categoria_id: int | None,
        page: int,
        page_size: int,
    ) -> tuple[
        list[tuple[Referencia, Color, Coleccion, ValorParametro]],
        int,
    ]:
        consulta = (
            self.db.query(
                Referencia,
                Color,
                Coleccion,
                ValorParametro,
            )
            .join(Color, Color.id == Referencia.color_id)
            .join(Coleccion, Coleccion.id == Referencia.coleccion_id)
            .join(
                ValorParametro,
                ValorParametro.id == Referencia.categoria_id,
            )
        )

        if buscar:
            termino = f"%{buscar.strip()}%"
            consulta = consulta.filter(
                or_(
                    Referencia.codigo.ilike(termino),
                    Referencia.nombre_referencia.ilike(termino),
                    Color.nombre.ilike(termino),
                    Coleccion.nombre.ilike(termino),
                    ValorParametro.nombre.ilike(termino),
                )
            )

        if coleccion_id is not None:
            consulta = consulta.filter(
                Referencia.coleccion_id == coleccion_id
            )

        if anio is not None:
            consulta = consulta.filter(
                Referencia.anio == anio
            )

        if color_id is not None:
            consulta = consulta.filter(
                Referencia.color_id == color_id
            )

        if categoria_id is not None:
            consulta = consulta.filter(
                Referencia.categoria_id == categoria_id
            )

        total = (
            consulta.with_entities(
                func.count(Referencia.id)
            ).scalar()
            or 0
        )

        resultados = (
            consulta
            .order_by(Referencia.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return resultados, total

    def registrar_auditoria(
        self,
        referencia_id: int,
        responsable_id: int,
        trace_id: str,
        despues: str,
    ) -> None:
        self.db.add(
            AuditoriaCatalogo(
                catalogo_codigo="REFERENCIA",
                registro_id=referencia_id,
                accion="CREAR",
                responsable_id=responsable_id,
                antes=None,
                despues=despues,
                motivo=None,
                trace_id=trace_id,
            )
        )
        self.db.flush()

    def guardar(self) -> None:
        self.db.commit()

    def deshacer(self) -> None:
        self.db.rollback()
