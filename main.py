from fastapi import FastAPI

# Creamos la instancia de la aplicación
app = FastAPI(
    title="Cloth Manager",
    version="1.0.0",
)

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a Cloth Manager!", "status": "activo"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "development"
    }