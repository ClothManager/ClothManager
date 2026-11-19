from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.schemas import UsuarioActualizar, UsuarioCrear
from app.core.database import get_db
from app.domain.usuario import Rol, Usuario, UsuarioRol
from app.api.schemas import UsuarioCrear
from app.repositories.usuario_repository import UsuarioRepository
from app.services.usuario_service import UsuarioService
from app.api.schemas import RolesActualizar, UsuarioActualizar, UsuarioCrear
from app.core.auth_dependencies import obtener_usuario_actual
router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
)


def verificar_administrador(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
) -> int:
    tiene_rol_admin = (
        db.query(UsuarioRol)
        .join(Rol, UsuarioRol.rol_id == Rol.id)
        .filter(
            UsuarioRol.usuario_id == usuario.id,
            Rol.codigo == "ADMINISTRADOR",
            Rol.activo.is_(True),
        )
        .first()
    )

    if tiene_rol_admin is None:
        raise HTTPException(
            status_code=403,
            detail="Se requiere el rol ADMINISTRADOR",
        )

    return usuario.id


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_usuario(
    datos: UsuarioCrear,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    servicio = UsuarioService(UsuarioRepository(db))
    usuario = servicio.crear_usuario(
        datos.model_dump(),
        responsable_id,
    )

    return {
        "mensaje": "Usuario creado correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "area": usuario.area,
            "roles": datos.roles,
            "estado": usuario.estado,
            "creado_en": usuario.creado_en,
        },
        "success": True,
    }
@router.get("")
def listar_usuarios(
    buscar: str | None = None,
    area: str | None = None,
    estado: str | None = None,
    rol: str | None = None,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = UsuarioRepository(db)
    servicio = UsuarioService(repositorio)

    usuarios = servicio.listar_usuarios(
        buscar=buscar,
        area=area,
        estado=estado,
        rol=rol,
    )

    return {
        "mensaje": "Usuarios consultados correctamente",
        "data": [
            {
                "id": usuario.id,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "correo": usuario.correo,
                "nombre_usuario": usuario.nombre_usuario,
                "area": usuario.area,
                "roles": repositorio.listar_codigos_roles(usuario.id),
                "estado": usuario.estado,
                "creado_en": usuario.creado_en,
            }
            for usuario in usuarios
        ],
        "success": True,
    }
@router.get("/{usuario_id}")
def consultar_usuario(
    usuario_id: int,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = UsuarioRepository(db)
    servicio = UsuarioService(repositorio)
    usuario = servicio.obtener_usuario(usuario_id)

    return {
        "mensaje": "Usuario consultado correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "area": usuario.area,
            "roles": repositorio.listar_codigos_roles(usuario.id),
            "estado": usuario.estado,
            "creado_en": usuario.creado_en,
        },
        "success": True,
    }
@router.patch("/{usuario_id}")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = UsuarioRepository(db)
    servicio = UsuarioService(repositorio)

    usuario = servicio.actualizar_usuario(
        usuario_id=usuario_id,
        datos=datos.model_dump(exclude_unset=True, exclude_none=True),
        responsable_id=responsable_id,
    )

    return {
        "mensaje": "Usuario actualizado correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "area": usuario.area,
            "roles": repositorio.listar_codigos_roles(usuario.id),
            "estado": usuario.estado,
            "creado_en": usuario.creado_en,
        },
        "success": True,
    }
@router.post("/{usuario_id}/inactivacion")
def inactivar_usuario(
    usuario_id: int,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = UsuarioRepository(db)
    servicio = UsuarioService(repositorio)

    usuario = servicio.inactivar_usuario(
        usuario_id=usuario_id,
        responsable_id=responsable_id,
    )

    return {
        "mensaje": "Usuario inactivado correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "area": usuario.area,
            "roles": repositorio.listar_codigos_roles(usuario.id),
            "estado": usuario.estado,
        },
        "success": True,
    }
@router.put("/{usuario_id}/roles")
def actualizar_roles(
    usuario_id: int,
    datos: RolesActualizar,
    responsable_id: int = Depends(verificar_administrador),
    db: Session = Depends(get_db),
):
    repositorio = UsuarioRepository(db)
    servicio = UsuarioService(repositorio)

    usuario = servicio.actualizar_roles(
        usuario_id=usuario_id,
        codigos_roles=datos.roles,
        responsable_id=responsable_id,
    )

    return {
        "mensaje": "Roles actualizados correctamente",
        "data": {
            "id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "roles": repositorio.listar_codigos_roles(usuario.id),
        },
        "success": True,
    }