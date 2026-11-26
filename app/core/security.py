import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
ALGORITHM = "HS256"

if len(SECRET_KEY) < 32 or SECRET_KEY == "cambia-este-valor-en-produccion":
    raise RuntimeError(
        "Configura en .env un SECRET_KEY aleatorio de al menos 32 caracteres"
    )

password_hasher = PasswordHash.recommended()


def hash_contrasena(contrasena: str) -> str:
    return password_hasher.hash(contrasena)


def verificar_contrasena(
    contrasena: str,
    hash_guardado: str,
) -> bool:
    return password_hasher.verify(contrasena, hash_guardado)


def generar_token_secreto() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_token_acceso(usuario_id: int, sesion_id: int) -> str:
    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    contenido = {
        "sub": str(usuario_id),
        "sid": str(sesion_id),
        "tipo": "access",
        "iat": ahora,
        "exp": expiracion,
    }

    return jwt.encode(contenido, SECRET_KEY, algorithm=ALGORITHM)


def leer_token_acceso(token: str) -> dict:
    contenido = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    if contenido.get("tipo") != "access":
        raise InvalidTokenError("El token no es de acceso")

    if not contenido.get("sub") or not contenido.get("sid"):
        raise InvalidTokenError("Al token le faltan datos requeridos")

    return contenido