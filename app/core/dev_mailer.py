import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()


def enviar_token_activacion(correo: str, token: str) -> None:
    if os.getenv("APP_ENV", "development") != "development":
        raise RuntimeError(
            "La bandeja local solo se puede usar en desarrollo"
        )

    bandeja = Path("dev_outbox")
    bandeja.mkdir(exist_ok=True)

    nombre_archivo = (
        f"activacion_{datetime.now(timezone.utc):%Y%m%d%H%M%S}_"
        f"{uuid4().hex[:8]}.txt"
    )

    mensaje = (
        f"Para: {correo}\n"
        "Asunto: Activación de cuenta ClothManager\n\n"
        "Usa el siguiente token en el endpoint de activación:\n"
        f"{token}\n"
    )

    (bandeja / nombre_archivo).write_text(mensaje, encoding="utf-8")


def enviar_token_recuperacion(correo: str, token: str) -> None:
    if os.getenv("APP_ENV", "development") != "development":
        raise RuntimeError(
            "La bandeja local solo se puede usar en desarrollo"
        )

    bandeja = Path("dev_outbox")
    bandeja.mkdir(exist_ok=True)

    nombre_archivo = (
        f"recuperacion_{datetime.now(timezone.utc):%Y%m%d%H%M%S}_"
        f"{uuid4().hex[:8]}.txt"
    )

    mensaje = (
        f"Para: {correo}\n"
        "Asunto: Recuperación de contraseña ClothManager\n\n"
        "Usa el siguiente token en el endpoint de confirmación:\n"
        f"{token}\n"
    )

    (bandeja / nombre_archivo).write_text(mensaje, encoding="utf-8")