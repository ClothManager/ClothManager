from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import CantidadesTallaActualizar
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.usuario import Usuario
from app.repositories.plan_talla_repository import PlanTallaRepository
from app.services.plan_talla_service import PlanTallaService


router = APIRouter(
    prefix="/api/v1/referencias",
    tags=["Planificación por talla"],
)


def obtener_servicio(db: Session) -> PlanTallaService:
    repositorio = PlanTallaRepository(db)
    return PlanTallaService(repositorio)


@router.get("/{referencia_id}/variantes")
def consultar_cantidades_por_talla(
    referencia_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.consultar(
        referencia_id=referencia_id,
        usuario_id=usuario.id,
    )


@router.put("/{referencia_id}/variantes")
def actualizar_cantidades_por_talla(
    referencia_id: int,
    datos: CantidadesTallaActualizar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.actualizar(
        referencia_id=referencia_id,
        cantidades_planeadas=datos.cantidades_planeadas,
        responsable_id=usuario.id,
    )