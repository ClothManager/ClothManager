
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Crear aplicación FastAPI
app = FastAPI(
    title=os.getenv("APP_NAME", "ClothManager API"),
    description="API desarrollada con arquitectura de cuatro capas",
    version="1.0.0"
)

# Ruta principal
@app.get("/")
def inicio():
    return {
        "mensaje": "ClothManager API funcionando correctamente",
        "estado": "OK"
    }

# Ruta de verificación
@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development")
    }
