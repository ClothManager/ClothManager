from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    CatalogoActualizar,
    CatalogoCrear,
    CatalogoEstadoActualizar,
    ValorParametroActualizar,
    ValorParametroCrear,
    ValorParametroEstadoActualizar,
)
from app.api.usuario_api import verificar_administrador
from app.core.auth_dependencies import obtener_usuario_actual
from app.core.database import get_db
from app.core.permisos import validar_permiso
from app.domain.usuario import Rol, Usuario, UsuarioRol
from app.repositories.catalogo_repository import CatalogoRepository
from app.services.catalogo_service import CatalogoService


router = APIRouter(
    prefix="/api/v1/catalogos",
    tags=["Catálogos"],
)


def verificar_lectura_catalogos(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
) -> int:
    es_administrador = (
        db.query(UsuarioRol)
        .join(Rol, Rol.id == UsuarioRol.rol_id)
        .filter(
            UsuarioRol.usuario_id == usuario.id,
            Rol.codigo == "ADMINISTRADOR",
            Rol.activo.is_(True),
        )
        .first()
    )

    if es_administrador is None:
        validar_permiso(
            db=db,
            usuario_id=usuario.id,
            modulo="MOD-10",
            recurso="CATALOGOS",
            accion="CONSULTAR",
        )

    return usuario.id


def _catalogo_json(catalogo):
    return {
        "id": catalogo.id,
        "codigo": catalogo.codigo,
        "nombre": catalogo.nombre,
        "descripcion": catalogo.descripcion,
        "activo": catalogo.activo,
        "version": catalogo.version,
    }


def _valor_json(valor):
    return {
        "id": valor.id,
        "codigo": valor.codigo,
        "nombre": valor.nombre,
        "orden": valor.orden,
        "activo": valor.activo,
        "version": valor.version,
    }


@router.get("")
def listar_catalogos(
    usuario_id: int = Depends(verificar_lectura_catalogos),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))

    return {
        "success": True,
        "message": "Catálogos consultados correctamente",
        "data": [
            _catalogo_json(item)
            for item in servicio.listar_catalogos()
        ],
        "trace_id": str(uuid4()),
    }


@router.post("", status_code=201)
def crear_catalogo(
    datos: CatalogoCrear,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    catalogo, trace_id = servicio.crear_catalogo(
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": "Catálogo creado correctamente",
        "data": _catalogo_json(catalogo),
        "trace_id": trace_id,
    }


@router.patch("/{codigo}")
def actualizar_catalogo(
    codigo: str,
    datos: CatalogoActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    catalogo, trace_id = servicio.actualizar_catalogo(
        codigo,
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": "Catálogo actualizado correctamente",
        "data": _catalogo_json(catalogo),
        "trace_id": trace_id,
    }


@router.patch("/{codigo}/estado")
def cambiar_estado_catalogo(
    codigo: str,
    datos: CatalogoEstadoActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    catalogo, trace_id = servicio.cambiar_estado_catalogo(
        codigo,
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": (
            "Catálogo activado correctamente"
            if datos.activo
            else "Catálogo inactivado correctamente"
        ),
        "data": _catalogo_json(catalogo),
        "trace_id": trace_id,
    }


@router.get("/{codigo}/valores")
def listar_valores(
    codigo: str,
    buscar: str | None = None,
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    usuario_id: int = Depends(verificar_lectura_catalogos),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    catalogo, valores, total = servicio.listar_valores(
        codigo,
        buscar,
        activo,
        page,
        page_size,
    )

    return {
        "success": True,
        "message": "Opciones consultadas correctamente",
        "data": {
            "catalogo": _catalogo_json(catalogo),
            "valores": [
                _valor_json(item)
                for item in valores
            ],
        },
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        "trace_id": str(uuid4()),
    }


@router.post("/{codigo}/valores", status_code=201)
def crear_valor(
    codigo: str,
    datos: ValorParametroCrear,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    valor, trace_id = servicio.crear_valor(
        codigo,
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": "Opción creada correctamente",
        "data": _valor_json(valor),
        "trace_id": trace_id,
    }


@router.patch("/{codigo}/valores/{valor_id}")
def actualizar_valor(
    codigo: str,
    valor_id: int,
    datos: ValorParametroActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    valor, trace_id = servicio.actualizar_valor(
        codigo,
        valor_id,
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": "Opción actualizada correctamente",
        "data": _valor_json(valor),
        "trace_id": trace_id,
    }


@router.patch("/{codigo}/valores/{valor_id}/estado")
def cambiar_estado_valor(
    codigo: str,
    valor_id: int,
    datos: ValorParametroEstadoActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = CatalogoService(CatalogoRepository(db))
    valor, trace_id = servicio.cambiar_estado_valor(
        codigo,
        valor_id,
        datos.model_dump(),
        responsable_id,
    )

    return {
        "success": True,
        "message": (
            "Opción activada correctamente"
            if datos.activo
            else "Opción inactivada correctamente"
        ),
        "data": _valor_json(valor),
        "trace_id": trace_id,
    }