from getpass import getpass

from app.core.database import SessionLocal
from app.core.security import hash_contrasena
from app.domain.autenticacion import CredencialUsuario
from app.domain.usuario import Rol, Usuario, UsuarioRol


db = SessionLocal()

try:
    rol = db.query(Rol).filter_by(codigo="ADMINISTRADOR").first()

    if rol is None:
        rol = Rol(
            codigo="ADMINISTRADOR",
            nombre="Administrador",
            activo=True,
        )
        db.add(rol)
        db.flush()

    usuario = (
        db.query(Usuario)
        .filter_by(nombre_usuario="admin")
        .first()
    )

    if usuario is None:
        usuario = Usuario(
            nombres="Administrador",
            apellidos="Local",
            correo="admin@clothmanager.local",
            nombre_usuario="admin",
            area="ADMINISTRACION",
            estado="ACTIVO",
        )
        db.add(usuario)
        db.flush()

    asignacion = (
        db.query(UsuarioRol)
        .filter_by(usuario_id=usuario.id, rol_id=rol.id)
        .first()
    )

    if asignacion is None:
        db.add(
            UsuarioRol(
                usuario_id=usuario.id,
                rol_id=rol.id,
            )
        )

    credencial = (
        db.query(CredencialUsuario)
        .filter_by(usuario_id=usuario.id)
        .first()
    )

    if credencial is None:
        contrasena = getpass("Contraseña inicial para admin: ")
        confirmacion = getpass("Confirma la contraseña: ")

        if not contrasena or contrasena != confirmacion:
            raise ValueError("La contraseña está vacía o no coincide.")

        db.add(
            CredencialUsuario(
                usuario_id=usuario.id,
                hash_contrasena=hash_contrasena(contrasena),
                debe_cambiar_contrasena=True,
            )
        )

    db.commit()
    print(f"Administrador local creado o ya existente. ID: {usuario.id}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()