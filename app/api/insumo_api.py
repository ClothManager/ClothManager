from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.schemas import InsumoCrear, RequerimientosInsumoActualizar
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.usuario import Usuario
from app.repositories.insumo_repository import InsumoRepository
from app.services.insumo_service import InsumoService


router = APIRouter(
    tags=["Insumos y requerimientos"],
)

insumos_router = APIRouter(
    prefix="/api/v1/insumos",
    tags=["Insumos y requerimientos"],
)

referencias_router = APIRouter(
    prefix="/api/v1/referencias",
    tags=["Insumos y requerimientos"],
)


def obtener_servicio(db: Session) -> InsumoService:
    return InsumoService(InsumoRepository(db))


@insumos_router.get("")
def listar_insumos(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).listar_insumos(usuario.id)


@insumos_router.post("", status_code=status.HTTP_201_CREATED)
def crear_insumo(
    datos: InsumoCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).crear_insumo(
        datos=datos.model_dump(),
        responsable_id=usuario.id,
    )


@referencias_router.get("/{referencia_id}/insumos")
def consultar_requerimientos(
    referencia_id: int,
    base_calculo: Literal["POR_UNIDAD", "POR_LOTE"] | None = Query(
        default=None,
        alias="baseCalculo",
    ),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).consultar_requerimientos(
        referencia_id=referencia_id,
        usuario_id=usuario.id,
        base_calculo=base_calculo,
    )


@referencias_router.put("/{referencia_id}/insumos")
def actualizar_requerimientos(
    referencia_id: int,
    datos: "RequerimientosInsumoActualizar",
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).actualizar_requerimientos(
        referencia_id=referencia_id,
        base_calculo=datos.base_calculo,
        lineas_datos=[
            linea.model_dump()
            for linea in datos.insumos
        ],
        responsable_id=usuario.id,
    )