import json
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.repositories.plan_talla_repository import PlanTallaRepository


TALLAS_ESPERADAS = ("S", "M", "L", "XL", "XXL")


class PlanTallaService:
    def __init__(self, repositorio: PlanTallaRepository):
        self.repositorio = repositorio

    def _error(
        self,
        codigo: str,
        message: str,
        codigo_http: int,
    ) -> HTTPException:
        return HTTPException(
            status_code=codigo_http,
            detail={
                "codigo": codigo,
                "message": message,
                "detalle": [],
            },
        )

    def _validar_permiso(
        self,
        usuario_id: int,
        accion: str,
    ) -> None:
        if self.repositorio.es_administrador(usuario_id):
            return

        validar_permiso(
            db=self.repositorio.db,
            usuario_id=usuario_id,
            modulo="MOD-03",
            recurso="PLAN_TALLAS",
            accion=accion,
        )

    def _obtener_referencia_disponible(
        self,
        referencia_id: int,
    ):
        resultado = self.repositorio.obtener_referencia_y_color(
            referencia_id
        )

        if resultado is None:
            raise self._error(
                "REFERENCE_NOT_FOUND",
                "No se encontró la referencia solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        referencia, color = resultado

        if not referencia.activo:
            raise self._error(
                "INVALID_REFERENCE",
                "La referencia está inactiva y no admite planificación.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return referencia, color

    def _obtener_tallas(self):
        tallas = self.repositorio.listar_tallas_activas()
        tallas_por_codigo = {
            talla.codigo.upper(): talla
            for talla in tallas
        }

        faltantes = [
            codigo
            for codigo in TALLAS_ESPERADAS
            if codigo not in tallas_por_codigo
        ]

        if faltantes:
            raise self._error(
                "SIZE_CONFIGURATION_ERROR",
                "No están disponibles todas las tallas requeridas.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return [
            tallas_por_codigo[codigo]
            for codigo in TALLAS_ESPERADAS
        ]

    def _crear_respuesta(
        self,
        referencia,
        color,
        cantidades: dict[str, int],
        trace_id: str,
    ) -> dict:
        matriz = {
            codigo: cantidades.get(codigo, 0)
            for codigo in TALLAS_ESPERADAS
        }

        return {
            "success": True,
            "message": "Cantidades por talla consultadas correctamente.",
            "data": {
                "referenciaId": referencia.id,
                "referencia": referencia.nombre_referencia,
                "color": {
                    "id": color.id,
                    "codigo": color.codigo,
                    "nombre": color.nombre,
                },
                "cantidadesPlaneadas": matriz,
                "totalPlaneado": sum(matriz.values()),
            },
            "trace_id": trace_id,
        }

    def consultar(
        self,
        referencia_id: int,
        usuario_id: int,
    ) -> dict:
        self._validar_permiso(usuario_id, "CONSULTAR")

        referencia, color = self._obtener_referencia_disponible(
            referencia_id
        )
        self._obtener_tallas()

        cantidades_guardadas = self.repositorio.obtener_cantidades(
            referencia_id
        )

        return self._crear_respuesta(
            referencia=referencia,
            color=color,
            cantidades=cantidades_guardadas,
            trace_id=str(uuid4()),
        )

    def actualizar(
        self,
        referencia_id: int,
        cantidades_planeadas: dict[str, int],
        responsable_id: int,
    ) -> dict:
        self._validar_permiso(responsable_id, "MODIFICAR")

        referencia, color = self._obtener_referencia_disponible(
            referencia_id
        )
        tallas = self._obtener_tallas()

        cantidades_normalizadas = {
            talla.strip().upper(): cantidad
            for talla, cantidad in cantidades_planeadas.items()
        }

        tallas_no_permitidas = (
            set(cantidades_normalizadas) - set(TALLAS_ESPERADAS)
        )

        if tallas_no_permitidas:
            raise self._error(
                "INVALID_SIZE",
                "Solo se permiten las tallas S, M, L, XL y XXL.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        for cantidad in cantidades_normalizadas.values():
            if not isinstance(cantidad, int) or isinstance(cantidad, bool):
                raise self._error(
                    "INVALID_QUANTITY",
                    "Las cantidades deben ser números enteros.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if cantidad < 0 or cantidad > 1_000_000:
                raise self._error(
                    "INVALID_QUANTITY",
                    "La cantidad debe estar entre 0 y 1.000.000.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

        cantidades_anteriores = self.repositorio.obtener_cantidades(
            referencia_id
        )

        matriz_anterior = {
            codigo: cantidades_anteriores.get(codigo, 0)
            for codigo in TALLAS_ESPERADAS
        }

        matriz_nueva = {
            codigo: cantidades_normalizadas.get(codigo, 0)
            for codigo in TALLAS_ESPERADAS
        }

        trace_id = str(uuid4())

        try:
            self.repositorio.guardar_matriz(
                referencia_id=referencia_id,
                tallas=tallas,
                cantidades=cantidades_normalizadas,
                responsable_id=responsable_id,
            )

            self.repositorio.registrar_auditoria(
                referencia_id=referencia_id,
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=json.dumps(matriz_anterior, ensure_ascii=False),
                despues=json.dumps(matriz_nueva, ensure_ascii=False),
            )

            self.repositorio.guardar()

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "INVALID_PLAN",
                "No fue posible guardar la distribución por talla.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Cantidades por talla actualizadas correctamente.",
            "data": {
                "referenciaId": referencia.id,
                "referencia": referencia.nombre_referencia,
                "color": {
                    "id": color.id,
                    "codigo": color.codigo,
                    "nombre": color.nombre,
                },
                "cantidadesPlaneadas": matriz_nueva,
                "totalPlaneado": sum(matriz_nueva.values()),
            },
            "trace_id": trace_id,
        }