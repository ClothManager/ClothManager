from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    CompraInsumoCrear,
    CompraInsumoEstadoActualizar,
    ProveedorCrear,
    RecepcionInsumoCrear,
)
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.usuario import Usuario
from app.repositories.compra_insumo_repository import (
    CompraInsumoRepository,
)
from app.services.compra_insumo_service import CompraInsumoService


router = APIRouter(tags=["Compras y recepción de insumos"])


def obtener_servicio(db: Session) -> CompraInsumoService:
    return CompraInsumoService(CompraInsumoRepository(db))


@router.get("/api/v1/proveedores")
def listar_proveedores(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).listar_proveedores(usuario.id)


@router.post(
    "/api/v1/proveedores",
    status_code=status.HTTP_201_CREATED,
)
def crear_proveedor(
    datos: ProveedorCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).crear_proveedor(
        datos=datos.model_dump(),
        responsable_id=usuario.id,
    )


@router.get("/api/v1/compras-insumos")
def listar_compras(
    estado: str | None = Query(default=None),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).listar_compras(
        usuario_id=usuario.id,
        estado=estado,
    )


@router.post(
    "/api/v1/compras-insumos",
    status_code=status.HTTP_201_CREATED,
)
def crear_compra(
    datos: CompraInsumoCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).crear_compra(
        datos=datos.model_dump(),
        responsable_id=usuario.id,
    )


@router.get("/api/v1/compras-insumos/{compra_id}")
def consultar_compra(
    compra_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).consultar_compra(
        compra_id,
        usuario.id,
    )


@router.post(
    "/api/v1/compras-insumos/{compra_id}/recepciones",
    status_code=status.HTTP_201_CREATED,
)
def confirmar_recepcion(
    compra_id: int,
    datos: RecepcionInsumoCrear,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=100,
    ),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).registrar_recepcion(
        compra_id=compra_id,
        lineas=[
            linea.model_dump()
            for linea in datos.lineas
        ],
        responsable_id=usuario.id,
        clave_idempotencia=idempotency_key.strip(),
    )


@router.get("/api/v1/compras-insumos/{compra_id}/recepciones")
def consultar_recepciones(
    compra_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).consultar_recepciones(
        compra_id,
        usuario.id,
    )


@router.patch("/api/v1/compras-insumos/{compra_id}/estado")
def cancelar_compra(
    compra_id: int,
    datos: CompraInsumoEstadoActualizar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).cancelar_compra(
        compra_id=compra_id,
        motivo=datos.motivo,
        responsable_id=usuario.id,
    )


@router.get("/api/v1/existencias-insumos")
def listar_existencias(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    return obtener_servicio(db).listar_existencias(usuario.id)