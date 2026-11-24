import os

from dotenv import load_dotenv
from fastapi import FastAPI
from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ReferenciaValorParametro,
    ValorParametro,
)
from app.api.autenticacion_api import router as autenticacion_router
from app.api.catalogo_api import router as catalogo_router
from app.api.parametro_api import router as parametro_router
from app.api.rol_api import router as rol_router
from app.api.usuario_api import router as usuario_router
from app.core.database import Base, SessionLocal, engine
from app.core.errores import registrar_manejadores
from app.core.seed_catalogos import sembrar_catalogos_base
from app.domain.autenticacion import (
    CredencialUsuario,
    EventoSeguridad,
    SesionUsuario,
    TokenCuenta,
)
from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.domain.parametro import Color, Talla
from app.domain.usuario import (
    Auditoria,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
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

    tallas_iniciales = [
        ("S", "S", 1),
        ("M", "M", 2),
        ("L", "L", 3),
        ("XL", "XL", 4),
        ("XXL", "XXL", 5),
    ]

    db = SessionLocal()

    try:
        for codigo, nombre, orden in tallas_iniciales:
            talla_existente = (
                db.query(Talla)
                .filter_by(codigo=codigo)
                .first()
            )

            if talla_existente is None:
                db.add(
                    Talla(
                        codigo=codigo,
                        nombre=nombre,
                        orden=orden,
                        activo=True,
                    )
                )

        sembrar_catalogos_base(db)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


app.include_router(autenticacion_router)
app.include_router(usuario_router)
app.include_router(rol_router)
app.include_router(parametro_router)
app.include_router(catalogo_router)

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