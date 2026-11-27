from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status
from app.api.schemas import RolCrear
from app.api.usuario_api import verificar_administrador
from app.core.database import get_db
from app.repositories.rol_repository import RolRepository
from app.services.rol_service import RolService
from app.api.schemas import RolActualizar, RolCrear
from app.api.schemas import (
    PermisosRolActualizar,
    RolActualizar,
    RolCrear,
)


router = APIRouter(
    prefix="/api/v1/roles",
    tags=["Roles"],
)


@router.get("")
def listar_roles(
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = RolRepository(db)
    servicio = RolService(repositorio)
    roles = servicio.listar_roles()

    return {
        "mensaje": "Roles consultados correctamente",
        "data": [
            {
                "codigo": rol.codigo,
                "nombre": rol.nombre,
                "descripcion": rol.descripcion,
                "activo": rol.activo,
                "permisos": [
                    {
                        "modulo": permiso.modulo,
                        "recurso": permiso.recurso,
                        "accion": permiso.accion,
                    }
                    for permiso in repositorio.listar_permisos(rol.id)
                ],
            }
            for rol in roles
        ],
        "success": True,
    }
@router.post("", status_code=status.HTTP_201_CREATED)
def crear_rol(
    datos: RolCrear,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = RolRepository(db)
    servicio = RolService(repositorio)
    rol = servicio.crear_rol(datos.model_dump(), responsable_id)

    return {
        "mensaje": "Rol creado correctamente",
        "data": {
            "codigo": rol.codigo,
            "nombre": rol.nombre,
            "descripcion": rol.descripcion,
            "activo": rol.activo,
        },
        "success": True,
    }
@router.patch("/{codigo}")
def actualizar_rol(
    codigo: str,
    datos: RolActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = RolRepository(db)
    servicio = RolService(repositorio)

    rol = servicio.actualizar_rol(
        codigo=codigo,
        datos=datos.model_dump(exclude_unset=True, exclude_none=True),
        responsable_id=responsable_id,
    )

    return {
        "mensaje": "Rol actualizado correctamente",
        "data": {
            "codigo": rol.codigo,
            "nombre": rol.nombre,
            "descripcion": rol.descripcion,
            "activo": rol.activo,
        },
        "success": True,
    }
@router.put("/{codigo}/permisos")
def actualizar_permisos_rol(
    codigo: str,
    datos: PermisosRolActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = RolRepository(db)
    servicio = RolService(repositorio)

    rol = servicio.actualizar_permisos(
        codigo=codigo,
        permisos_datos=[
            permiso.model_dump()
            for permiso in datos.permisos
        ],
        responsable_id=responsable_id,
    )

    permisos = repositorio.listar_permisos(rol.id)

    return {
        "mensaje": "Permisos del rol actualizados correctamente",
        "data": {
            "codigo": rol.codigo,
            "permisos": [
                {
                    "modulo": permiso.modulo,
                    "recurso": permiso.recurso,
                    "accion": permiso.accion,
                }
                for permiso in permisos
            ],
        },
        "success": True,
    }
