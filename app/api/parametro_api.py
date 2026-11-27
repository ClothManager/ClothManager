from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ColorActualizar,
    ColorCrear,
    ColorEstadoActualizar,
)
from app.api.usuario_api import verificar_administrador
from app.core.database import get_db
from app.repositories.parametro_repository import ParametroRepository
from app.services.parametro_service import ParametroService


router = APIRouter(
    prefix="/api/v1/parametros",
    tags=["Parámetros"],
)


def _error_parametro(
    codigo: str,
    message: str,
    codigo_http: int,
) -> HTTPException:
    return HTTPException(
        status_code=codigo_http,
        detail={
            "codigo": codigo,
            "message": message,
            "detalle": [],
        },
    )


def _representar_talla(talla) -> dict:
    return {
        "id": talla.id,
        "codigo": talla.codigo,
        "nombre": talla.nombre,
        "orden": talla.orden,
        "activo": talla.activo,
    }


def _representar_color(color) -> dict:
    return {
        "id": color.id,
        "codigo": color.codigo,
        "nombre": color.nombre,
        "activo": color.activo,
        "version": color.version,
    }


@router.get("/{tipo}")
def listar_parametros(
    tipo: str,
    buscar: str | None = None,
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = ParametroService(ParametroRepository(db))
    tipo_normalizado = tipo.strip().upper()

    if tipo_normalizado == "TALLA":
        registros, total = servicio.listar_tallas(
            buscar=buscar,
            activo=activo,
            page=page,
            page_size=page_size,
        )
        data = [_representar_talla(talla) for talla in registros]

    elif tipo_normalizado == "COLOR":
        registros, total = servicio.listar_colores(
            buscar=buscar,
            activo=activo,
            page=page,
            page_size=page_size,
        )
        data = [_representar_color(color) for color in registros]

    else:
        raise _error_parametro(
            "PARAMETER_NOT_FOUND",
            f"El catálogo '{tipo}' no está disponible.",
            status.HTTP_404_NOT_FOUND,
        )

    return {
        "success": True,
        "message": "Consulta de parámetros exitosa",
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        "trace_id": str(uuid4()),
    }


@router.get("/{tipo}/{registro_id}")
def consultar_parametro(
    tipo: str,
    registro_id: int,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = ParametroService(ParametroRepository(db))
    tipo_normalizado = tipo.strip().upper()

    if tipo_normalizado == "TALLA":
        registro = servicio.consultar_talla(registro_id)
        data = _representar_talla(registro)

    elif tipo_normalizado == "COLOR":
        registro = servicio.consultar_color(registro_id)
        data = _representar_color(registro)

    else:
        raise _error_parametro(
            "PARAMETER_NOT_FOUND",
            f"El catálogo '{tipo}' no está disponible.",
            status.HTTP_404_NOT_FOUND,
        )

    return {
        "success": True,
        "message": "Parámetro consultado correctamente",
        "data": data,
        "trace_id": str(uuid4()),
    }


@router.post(
    "/{tipo}",
    status_code=status.HTTP_201_CREATED,
)
def crear_parametro(
    tipo: str,
    datos: ColorCrear,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    tipo_normalizado = tipo.strip().upper()

    if tipo_normalizado == "TALLA":
        raise _error_parametro(
            "FIXED_CATALOG",
            "Las tallas son fijas y no se pueden crear ni modificar.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if tipo_normalizado != "COLOR":
        raise _error_parametro(
            "PARAMETER_NOT_FOUND",
            f"El catálogo '{tipo}' no está disponible.",
            status.HTTP_404_NOT_FOUND,
        )

    servicio = ParametroService(ParametroRepository(db))
    color, trace_id = servicio.crear_color(
        datos=datos.model_dump(),
        responsable_id=responsable_id,
    )

    return {
        "success": True,
        "message": "Color creado correctamente",
        "data": _representar_color(color),
        "trace_id": trace_id,
    }


@router.patch("/{tipo}/{registro_id}")
def actualizar_parametro(
    tipo: str,
    registro_id: int,
    datos: ColorActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    tipo_normalizado = tipo.strip().upper()

    if tipo_normalizado == "TALLA":
        raise _error_parametro(
            "FIXED_CATALOG",
            "Las tallas son fijas y no se pueden modificar.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if tipo_normalizado != "COLOR":
        raise _error_parametro(
            "PARAMETER_NOT_FOUND",
            f"El catálogo '{tipo}' no está disponible.",
            status.HTTP_404_NOT_FOUND,
        )

    servicio = ParametroService(ParametroRepository(db))
    color, trace_id = servicio.actualizar_color(
        color_id=registro_id,
        datos=datos.model_dump(),
        responsable_id=responsable_id,
    )

    return {
        "success": True,
        "message": "Color actualizado correctamente",
        "data": _representar_color(color),
        "trace_id": trace_id,
    }


@router.patch("/{tipo}/{registro_id}/estado")
def cambiar_estado_parametro(
    tipo: str,
    registro_id: int,
    datos: ColorEstadoActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    tipo_normalizado = tipo.strip().upper()

    if tipo_normalizado == "TALLA":
        raise _error_parametro(
            "FIXED_CATALOG",
            "Las tallas son fijas y no se pueden activar, inactivar ni eliminar.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if tipo_normalizado != "COLOR":
        raise _error_parametro(
            "PARAMETER_NOT_FOUND",
            f"El catálogo '{tipo}' no está disponible.",
            status.HTTP_404_NOT_FOUND,
        )

    servicio = ParametroService(ParametroRepository(db))
    color, trace_id = servicio.cambiar_estado_color(
        color_id=registro_id,
        datos=datos.model_dump(),
        responsable_id=responsable_id,
    )

    accion = "activado" if datos.activo else "inactivado"

    return {
        "success": True,
        "message": f"Color {accion} correctamente",
        "data": _representar_color(color),
        "trace_id": trace_id,
    }