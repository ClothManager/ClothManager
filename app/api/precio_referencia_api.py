from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import PreciosReferenciaActualizar
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.usuario import Usuario
from app.repositories.precio_referencia_repository import (
    PrecioReferenciaRepository,
)
from app.services.precio_referencia_service import PrecioReferenciaService


router = APIRouter(
    prefix="/api/v1/referencias",
    tags=["Precios por referencia"],
)


def obtener_servicio(db: Session) -> PrecioReferenciaService:
    repositorio = PrecioReferenciaRepository(db)
    return PrecioReferenciaService(repositorio)


@router.get("/{referencia_id}/precios")
def consultar_precios_referencia(
    referencia_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.consultar(
        referencia_id=referencia_id,
        usuario_id=usuario.id,
    )


@router.put("/{referencia_id}/precios")
def actualizar_precios_referencia(
    referencia_id: int,
    datos: PreciosReferenciaActualizar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.actualizar(
        referencia_id=referencia_id,
        datos=datos.model_dump(),
        responsable_id=usuario.id,
    )