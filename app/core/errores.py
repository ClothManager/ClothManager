from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


CODIGOS_HTTP = {
    400: "SOLICITUD_INVALIDA",
    401: "NO_AUTENTICADO",
    403: "SIN_PERMISO",
    404: "NO_ENCONTRADO",
    409: "DUPLICADO",
    422: "REGLA_NO_CUMPLIDA",
    500: "ERROR_INTERNO",
}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def manejar_error_http(
        request: Request,
        exc: StarletteHTTPException,
    ):
        detail = exc.detail
        codigo = CODIGOS_HTTP.get(exc.status_code, "ERROR")
        detalle = []

        if isinstance(detail, dict):
            codigo = detail.get("codigo", codigo)
            mensaje = detail.get("mensaje", "No fue posible completar la solicitud")
            detalle = detail.get("detalle", [])
        else:
            mensaje = str(detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "codigo": codigo,
                "mensaje": mensaje,
                "detalle": detalle,
                "success": False,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(
        request: Request,
        exc: RequestValidationError,
    ):
        detalle = [
            {
                "campo": ".".join(str(parte) for parte in error["loc"]),
                "error": error["msg"],
            }
            for error in exc.errors()
        ]

        return JSONResponse(
            status_code=400,
            content={
                "codigo": "SOLICITUD_INVALIDA",
                "mensaje": "Los datos enviados no tienen un formato válido",
                "detalle": detalle,
                "success": False,
            },
        )
    @app.exception_handler(Exception)
    async def manejar_error_interno(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=500,
            content={
                "codigo": "ERROR_INTERNO",
                "mensaje": "Ocurrió un error interno en el servicio",
                "detalle": [],
                "success": False,
            },
        )