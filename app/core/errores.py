from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


CODIGOS_HTTP = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


def _respuesta_error(
    status_code: int,
    codigo: str,
    message: str,
    detalles: list,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": codigo,
                "details": detalles,
            },
            "trace_id": str(uuid4()),
        },
    )


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def manejar_error_http(
        request: Request,
        exc: StarletteHTTPException,
    ):
        detail = exc.detail
        codigo = CODIGOS_HTTP.get(exc.status_code, "HTTP_ERROR")
        message = "No fue posible completar la solicitud"
        detalles = []

        if isinstance(detail, dict):
            codigo = detail.get("codigo", detail.get("code", codigo))
            message = detail.get(
                "message",
                detail.get("mensaje", message),
            )
            detalles = detail.get(
                "detalle",
                detail.get("details", []),
            )
        elif isinstance(detail, str):
            message = detail

        return _respuesta_error(
            exc.status_code,
            codigo,
            message,
            detalles,
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(
        request: Request,
        exc: RequestValidationError,
    ):
        detalles = [
            {
                "campo": ".".join(str(parte) for parte in error["loc"]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]

        return _respuesta_error(
            422,
            "VALIDATION_ERROR",
            "Los datos enviados no son válidos",
            detalles,
        )

    @app.exception_handler(Exception)
    async def manejar_error_interno(
        request: Request,
        exc: Exception,
    ):
        return _respuesta_error(
            500,
            "INTERNAL_ERROR",
            "Ocurrió un error interno en el servicio",
            [],
        )