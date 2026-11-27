from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.schemas import ColeccionActualizar, ColeccionCrear
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.domain.coleccion import Coleccion
from app.domain.usuario import Usuario
from app.repositories.coleccion_repository import ColeccionRepository
from app.services.coleccion_service import ColeccionService


router = APIRouter(
    prefix="/api/v1/colecciones",
    tags=["Colecciones"],
)


def _coleccion_json(coleccion: Coleccion) -> dict:
    return {
        "id": coleccion.id,
        "codigo": coleccion.codigo,
        "nombre": coleccion.nombre,
        "anio": coleccion.anio,
        "fecha_inicio": coleccion.fecha_inicio.isoformat(),
        "fecha_inicio_preventa": (
            coleccion.fecha_inicio_preventa.isoformat()
        ),
        "fecha_cierre_preventa": (
            coleccion.fecha_cierre_preventa.isoformat()
        ),
        "fecha_entrega": coleccion.fecha_entrega.isoformat(),
        "estado": coleccion.estado,
        "version": coleccion.version,
        "creado_en": coleccion.creado_en.isoformat(),
        "creado_por": coleccion.creado_por,
        "actualizado_en": (
            coleccion.actualizado_en.isoformat()
            if coleccion.actualizado_en
            else None
        ),
        "actualizado_por": coleccion.actualizado_por,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_coleccion(
    datos: ColeccionCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = ColeccionService(ColeccionRepository(db))
    coleccion, trace_id = servicio.crear(
        datos.model_dump(),
        usuario.id,
    )

    return {
        "success": True,
        "message": "Colección creada correctamente",
        "data": _coleccion_json(coleccion),
        "trace_id": trace_id,
    }


@router.get("")
def listar_colecciones(
    buscar: str | None = None,
    anio: int | None = Query(default=None, ge=2000, le=2200),
    estado: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = ColeccionService(ColeccionRepository(db))
    colecciones, total = servicio.listar(
        buscar=buscar,
        anio=anio,
        estado=estado,
        page=page,
        page_size=page_size,
        usuario_id=usuario.id,
    )

    return {
        "success": True,
        "message": "Colecciones consultadas correctamente",
        "data": [_coleccion_json(item) for item in colecciones],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        "trace_id": str(uuid4()),
    }


@router.get("/{coleccion_id}")
def consultar_coleccion(
    coleccion_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = ColeccionService(ColeccionRepository(db))
    coleccion = servicio.consultar(coleccion_id, usuario.id)

    return {
        "success": True,
        "message": "Colección consultada correctamente",
        "data": _coleccion_json(coleccion),
        "trace_id": str(uuid4()),
    }


@router.patch("/{coleccion_id}")
def actualizar_coleccion(
    coleccion_id: int,
    datos: ColeccionActualizar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    servicio = ColeccionService(ColeccionRepository(db))
    coleccion, trace_id = servicio.actualizar(
        coleccion_id=coleccion_id,
        datos=datos.model_dump(exclude_unset=True),
        responsable_id=usuario.id,
    )

    return {
        "success": True,
        "message": "Colección actualizada correctamente",
        "data": _coleccion_json(coleccion),
        "trace_id": trace_id,
    }