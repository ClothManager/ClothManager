import os
from app.domain.coleccion import Coleccion, SecuenciaColeccion
from app.api.coleccion_api import router as coleccion_router
from app.domain.coleccion import Coleccion
from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.precio_referencia_api import router as precio_referencia_router
from app.domain.precio_referencia import PrecioReferencia
from app.domain.referencia import Referencia
from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ReferenciaValorParametro,
    ValorParametro,
)
from app.api.autenticacion_api import router as autenticacion_router
from app.api.referencia_api import (
    coleccion_router as coleccion_referencias_router,
)
from app.api.referencia_api import router as referencia_router
from app.domain.referencia import Referencia
from app.api.catalogo_api import router as catalogo_router
from app.api.parametro_api import router as parametro_router
from app.api.rol_api import router as rol_router
from app.api.usuario_api import router as usuario_router
from app.core.database import Base, SessionLocal, engine
from app.core.errores import registrar_manejadores
from app.domain.plan_talla_referencia import PlanTallaReferencia
from app.api.plan_talla_api import router as plan_talla_router
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

Base.metadata.create_all(bind=engine)
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
app.include_router(coleccion_router)
app.include_router(referencia_router)
app.include_router(coleccion_referencias_router)
app.include_router(plan_talla_router)
app.include_router(precio_referencia_router)
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