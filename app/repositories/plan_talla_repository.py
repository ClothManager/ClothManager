from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.catalogo import AuditoriaCatalogo
from app.domain.parametro import Color, Talla
from app.domain.plan_talla_referencia import PlanTallaReferencia
from app.domain.referencia import Referencia
from app.domain.usuario import Rol, UsuarioRol


class PlanTallaRepository:
    def __init__(self, db: Session):
        self.db = db

    def es_administrador(self, usuario_id: int) -> bool:
        asignacion = (
            self.db.query(UsuarioRol)
            .join(Rol, Rol.id == UsuarioRol.rol_id)
            .filter(
                UsuarioRol.usuario_id == usuario_id,
                Rol.codigo == "ADMINISTRADOR",
                Rol.activo.is_(True),
            )
            .first()
        )

        return asignacion is not None

    def obtener_referencia_y_color(
        self,
        referencia_id: int,
    ) -> tuple[Referencia, Color] | None:
        return (
            self.db.query(Referencia, Color)
            .join(Color, Color.id == Referencia.color_id)
            .filter(Referencia.id == referencia_id)
            .first()
        )

    def listar_tallas_activas(self) -> list[Talla]:
        return (
            self.db.query(Talla)
            .filter(Talla.activo.is_(True))
            .order_by(Talla.orden)
            .all()
        )

    def obtener_cantidades(
        self,
        referencia_id: int,
    ) -> dict[str, int]:
        resultados = (
            self.db.query(
                Talla.codigo,
                PlanTallaReferencia.cantidad_planeada,
            )
            .join(
                PlanTallaReferencia,
                PlanTallaReferencia.talla_id == Talla.id,
            )
            .filter(
                PlanTallaReferencia.referencia_id == referencia_id,
            )
            .all()
        )

        return {
            codigo: cantidad
            for codigo, cantidad in resultados
        }

    def guardar_matriz(
        self,
        referencia_id: int,
        tallas: list[Talla],
        cantidades: dict[str, int],
        responsable_id: int,
    ) -> None:
        registros_existentes = (
            self.db.query(PlanTallaReferencia)
            .filter(
                PlanTallaReferencia.referencia_id == referencia_id,
            )
            .all()
        )

        registros_por_talla = {
            registro.talla_id: registro
            for registro in registros_existentes
        }

        ahora = datetime.now(timezone.utc)

        for talla in tallas:
            cantidad = cantidades.get(talla.codigo, 0)
            registro = registros_por_talla.get(talla.id)

            if registro is None:
                registro = PlanTallaReferencia(
                    referencia_id=referencia_id,
                    talla_id=talla.id,
                    cantidad_planeada=cantidad,
                    creado_por=responsable_id,
                    actualizado_por=responsable_id,
                    actualizado_en=ahora,
                )
                self.db.add(registro)
            else:
                registro.cantidad_planeada = cantidad
                registro.actualizado_por = responsable_id
                registro.actualizado_en = ahora

        self.db.flush()

    def registrar_auditoria(
        self,
        referencia_id: int,
        responsable_id: int,
        trace_id: str,
        antes: str,
        despues: str,
    ) -> None:
        self.db.add(
            AuditoriaCatalogo(
                catalogo_codigo="PLAN_TALLAS_REFERENCIA",
                registro_id=referencia_id,
                accion="ACTUALIZAR_CANTIDADES_TALLA",
                responsable_id=responsable_id,
                antes=antes,
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