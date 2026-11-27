from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.schemas import ReferenciaCrear
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.usuario import Usuario
from app.repositories.referencia_repository import ReferenciaRepository
from app.services.referencia_service import ReferenciaService


router = APIRouter(
    prefix="/api/v1/referencias",
    tags=["Referencias"],
)

coleccion_router = APIRouter(
    prefix="/api/v1/colecciones",
    tags=["Colecciones"],
)


def obtener_servicio(db: Session) -> ReferenciaService:
    return ReferenciaService(ReferenciaRepository(db))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def crear_referencia(
    datos: ReferenciaCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.crear(
        datos=datos.model_dump(),
        responsable_id=usuario.id,
    )


@router.get("")
def listar_referencias(
    buscar: str | None = Query(default=None, max_length=100),
    coleccion_id: int | None = Query(default=None, gt=0),
    anio: int | None = Query(default=None, ge=2000, le=2200),
    color_id: int | None = Query(default=None, gt=0),
    categoria_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.listar(
        usuario_id=usuario.id,
        buscar=buscar,
        coleccion_id=coleccion_id,
        anio=anio,
        color_id=color_id,
        categoria_id=categoria_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{referencia_id}")
def consultar_referencia(
    referencia_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.consultar(
        referencia_id=referencia_id,
        usuario_id=usuario.id,
    )


@coleccion_router.get("/{coleccion_id}/referencias")
def listar_referencias_de_coleccion(
    coleccion_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = obtener_servicio(db)

    return servicio.listar(
        usuario_id=usuario.id,
        coleccion_id=coleccion_id,
        page=page,
        page_size=page_size,
    )