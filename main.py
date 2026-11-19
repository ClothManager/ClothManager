from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.api.rol_api import router as rol_router
from app.core.database import Base, engine
from app.domain.usuario import (
    Auditoria,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)
from app.api.autenticacion_api import router as autenticacion_router
from app.core.errores import registrar_manejadores
from app.api.usuario_api import router as usuario_router
from app.domain.autenticacion import (
    CredencialUsuario,
    EventoSeguridad,
    SesionUsuario,
    TokenCuenta,
)


load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "ClothManager API"),
    description="API desarrollada con arquitectura de cuatro capas",
    version="1.0.0",
)


@app.on_event("startup")
def crear_tablas():
    Base.metadata.create_all(bind=engine)

app.include_router(autenticacion_router)
app.include_router(usuario_router)
app.include_router(rol_router)
registrar_manejadores(app)
@app.get("/")
def inicio():
    return {
        "mensaje": "ClothManager API funcionando correctamente",
        "estado": "OK",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
    }