from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.parametro import AuditoriaParametro, Color, Talla


class ParametroRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_tallas(self) -> list[Talla]:
        return (
            self.db.query(Talla)
            .filter(Talla.activo.is_(True))
            .order_by(Talla.orden)
            .all()
        )

    def obtener_talla_por_id(self, talla_id: int) -> Talla | None:
        return self.db.get(Talla, talla_id)

    def listar_colores(
        self,
        buscar: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Color], int]:
        consulta = self.db.query(Color)

        if buscar:
            termino = f"%{buscar.strip()}%"
            consulta = consulta.filter(
                or_(
                    Color.codigo.ilike(termino),
                    Color.nombre.ilike(termino),
                )
            )

        if activo is not None:
            consulta = consulta.filter(Color.activo.is_(activo))

        total = consulta.count()

        colores = (
            consulta.order_by(Color.codigo)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return colores, total

    def obtener_color_por_id(self, color_id: int) -> Color | None:
        return self.db.get(Color, color_id)

    def obtener_color_por_codigo(self, codigo: str) -> Color | None:
        codigo_normalizado = codigo.strip().lower()

        return (
            self.db.query(Color)
            .filter(func.lower(Color.codigo) == codigo_normalizado)
            .first()
        )

    def agregar_color(self, color: Color) -> Color:
        self.db.add(color)
        self.db.flush()
        return color

    def actualizar_color_si_version_coincide(
        self,
        color_id: int,
        version: int,
        cambios: dict,
    ) -> bool:
        resultado = (
            self.db.query(Color)
            .filter(
                Color.id == color_id,
                Color.version == version,
            )
            .update(cambios, synchronize_session=False)
        )

        return resultado == 1

    def agregar_auditoria_parametro(
        self,
        auditoria: AuditoriaParametro,
    ) -> None:
        self.db.add(auditoria)
        self.db.flush()

    def guardar_cambios(self) -> None:
        self.db.commit()

    def deshacer_cambios(self) -> None:
        self.db.rollback()
