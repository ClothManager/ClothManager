
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.usuario import (
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)


def validar_permiso(
    db: Session,
    usuario_id: int,
    modulo: str,
    recurso: str,
    accion: str,
) -> None:
    # 1. Verificar que el usuario exista y esté activo.
    usuario = db.get(Usuario, usuario_id)

    if usuario is None or usuario.estado != "ACTIVO":
        raise HTTPException(
            status_code=401,
            detail="El usuario no existe o está inactivo",
        )

    # 2. Verificar si el usuario tiene el rol SUPERADMINISTRADOR.
    es_superadministrador = (
        db.query(UsuarioRol)
        .join(
            Rol,
            Rol.id == UsuarioRol.rol_id,
        )
        .filter(
            UsuarioRol.usuario_id == usuario_id,
            Rol.codigo == "SUPERADMINISTRADOR",
            Rol.activo.is_(True),
        )
        .first()
    )

    # El SUPERADMINISTRADOR activo tiene acceso global.
    if es_superadministrador is not None:
        return

    # 3. Verificar los permisos asignados a los demás roles.
    permiso_asignado = (
        db.query(Permiso.id)
        .select_from(Usuario)
        .join(
            UsuarioRol,
            UsuarioRol.usuario_id == Usuario.id,
        )
        .join(
            Rol,
            Rol.id == UsuarioRol.rol_id,
        )
        .join(
            RolPermiso,
            RolPermiso.rol_id == Rol.id,
        )
        .join(
            Permiso,
            Permiso.id == RolPermiso.permiso_id,
        )
        .filter(
            Usuario.id == usuario_id,
            Usuario.estado == "ACTIVO",
            Rol.activo.is_(True),
            Permiso.activo.is_(True),
            Permiso.modulo == modulo.strip().upper(),
            Permiso.recurso == recurso.strip().upper(),
            Permiso.accion == accion.strip().upper(),
        )
        .first()
    )

    # 4. Rechazar el acceso si no existe el permiso requerido.
    if permiso_asignado is None:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene permiso para realizar esta acción",
        )
