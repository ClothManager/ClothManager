from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
    ReferenciaValorParametro,
)


class CatalogoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_catalogos(self) -> list[CatalogoParametro]:
        return (
            self.db.query(CatalogoParametro)
            .order_by(CatalogoParametro.codigo)
            .all()
        )

    def obtener_catalogo(self, codigo: str) -> CatalogoParametro | None:
        return (
            self.db.query(CatalogoParametro)
            .filter(
                func.lower(CatalogoParametro.codigo) == codigo.lower()
            )
            .first()
        )

    def obtener_catalogo_por_id(
        self,
        catalogo_id: int,
    ) -> CatalogoParametro | None:
        return self.db.get(CatalogoParametro, catalogo_id)

    def agregar_catalogo(
        self,
        catalogo: CatalogoParametro,
    ) -> CatalogoParametro:
        self.db.add(catalogo)
        self.db.flush()
        return catalogo

    def actualizar_catalogo_si_version_coincide(
        self,
        catalogo_id: int,
        version: int,
        cambios: dict,
    ) -> bool:
        filas_actualizadas = (
            self.db.query(CatalogoParametro)
            .filter(
                CatalogoParametro.id == catalogo_id,
                CatalogoParametro.version == version,
            )
            .update(cambios, synchronize_session=False)
        )
        return filas_actualizadas == 1

    def listar_valores(
        self,
        catalogo_id: int,
        buscar: str | None,
        activo: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[ValorParametro], int]:
        consulta = self.db.query(ValorParametro).filter(
            ValorParametro.catalogo_id == catalogo_id
        )

        if buscar:
            termino = f"%{buscar.strip()}%"
            consulta = consulta.filter(
                or_(
                    ValorParametro.codigo.ilike(termino),
                    ValorParametro.nombre.ilike(termino),
                )
            )

        if activo is not None:
            consulta = consulta.filter(
                ValorParametro.activo.is_(activo)
            )

        total = consulta.count()
        valores = (
            consulta
            .order_by(ValorParametro.orden, ValorParametro.codigo)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return valores, total

    def obtener_valor(
        self,
        catalogo_id: int,
        valor_id: int,
    ) -> ValorParametro | None:
        return (
            self.db.query(ValorParametro)
            .filter(
                ValorParametro.catalogo_id == catalogo_id,
                ValorParametro.id == valor_id,
            )
            .first()
        )

    def existe_codigo_valor(
        self,
        catalogo_id: int,
        codigo: str,
    ) -> bool:
        return (
            self.db.query(ValorParametro.id)
            .filter(
                ValorParametro.catalogo_id == catalogo_id,
                func.lower(ValorParametro.codigo) == codigo.lower(),
            )
            .first()
            is not None
        )

    def agregar_valor(
        self,
        valor: ValorParametro,
    ) -> ValorParametro:
        self.db.add(valor)
        self.db.flush()
        return valor

    def agregar_auditoria(
        self,
        auditoria: AuditoriaCatalogo,
    ) -> None:
        self.db.add(auditoria)
        self.db.flush()

    def guardar(self) -> None:
        self.db.commit()

    def deshacer(self) -> None:
        self.db.rollback()
    def actualizar_valor_si_version_coincide(
        self,
        valor_id: int,
        version: int,
        cambios: dict,
    ) -> bool:
        filas_actualizadas = (
            self.db.query(ValorParametro)
            .filter(
                ValorParametro.id == valor_id,
                ValorParametro.version == version,
            )
            .update(cambios, synchronize_session=False)
        )
        return filas_actualizadas == 1
    def tiene_dependencias_activas(self, valor_id: int) -> bool:
        return (
            self.db.query(ReferenciaValorParametro.id)
            .filter(
                ReferenciaValorParametro.valor_id == valor_id,
                ReferenciaValorParametro.activo.is_(True),
            )
            .first()
            is not None
        )