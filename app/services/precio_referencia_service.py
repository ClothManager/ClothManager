import json
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.domain.precio_referencia import PrecioReferencia
from app.repositories.precio_referencia_repository import (
    PrecioReferenciaRepository,
)


class PrecioReferenciaService:
    MODULO = "MOD-03"
    RECURSO_PRECIOS = "PRECIOS_REFERENCIA"
    RECURSO_COSTOS = "COSTOS_REFERENCIA"

    def __init__(self, repositorio: PrecioReferenciaRepository):
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

    def _requerir_permiso(
        self,
        usuario_id: int,
        recurso: str,
        accion: str,
    ) -> None:
        if self.repositorio.es_administrador(usuario_id):
            return

        validar_permiso(
            db=self.repositorio.db,
            usuario_id=usuario_id,
            modulo=self.MODULO,
            recurso=recurso,
            accion=accion,
        )

    def _puede_consultar_costo(self, usuario_id: int) -> bool:
        if self.repositorio.es_administrador(usuario_id):
            return True

        return self.repositorio.tiene_permiso(
            usuario_id=usuario_id,
            modulo=self.MODULO,
            recurso=self.RECURSO_COSTOS,
            accion="CONSULTAR",
        )

    def _obtener_referencia_disponible(
        self,
        referencia_id: int,
    ):
        referencia = self.repositorio.obtener_referencia(referencia_id)

        if referencia is None:
            raise self._error(
                "REFERENCE_NOT_FOUND",
                "La referencia indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )

        if not referencia.activo:
            raise self._error(
                "INVALID_REFERENCE",
                "La referencia está inactiva.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return referencia

    def _datos_auditoria(
        self,
        precios: PrecioReferencia,
    ) -> dict:
        return {
            "costoProduccion": str(precios.costo_produccion),
            "precioDetal": str(precios.precio_detal),
            "precioMayoristaNacional": str(
                precios.precio_mayorista_nacional
            ),
            "precioMayoristaExportacion": str(
                precios.precio_mayorista_exportacion
            ),
            "moneda": precios.moneda,
        }

    def _respuesta(
        self,
        referencia,
        precios: PrecioReferencia | None,
        usuario_id: int,
        message: str,
        trace_id: str,
    ) -> dict:
        if precios is None:
            data = None
        else:
            data = {
                "referenciaId": referencia.id,
                "referencia": referencia.nombre_referencia,
                "precioDetal": float(precios.precio_detal),
                "precioMayoristaNacional": float(
                    precios.precio_mayorista_nacional
                ),
                "precioMayoristaExportacion": float(
                    precios.precio_mayorista_exportacion
                ),
                "moneda": precios.moneda,
                "actualizadoEn": precios.actualizado_en,
            }

            if self._puede_consultar_costo(usuario_id):
                data["costoProduccion"] = float(
                    precios.costo_produccion
                )

        if precios is None:
            message = "La referencia aún no tiene precios configurados."

        return {
            "success": True,
            "message": message,
            "data": data,
            "trace_id": trace_id,
        }

    def consultar(
        self,
        referencia_id: int,
        usuario_id: int,
    ) -> dict:
        self._requerir_permiso(
            usuario_id,
            self.RECURSO_PRECIOS,
            "CONSULTAR",
        )

        referencia = self._obtener_referencia_disponible(referencia_id)
        precios = self.repositorio.obtener_por_referencia(referencia_id)

        return self._respuesta(
            referencia=referencia,
            precios=precios,
            usuario_id=usuario_id,
            message="Precios de referencia consultados correctamente.",
            trace_id=str(uuid4()),
        )

    def actualizar(
        self,
        referencia_id: int,
        datos: dict,
        responsable_id: int,
    ) -> dict:
        referencia = self._obtener_referencia_disponible(referencia_id)
        precios_existentes = self.repositorio.obtener_por_referencia(
            referencia_id
        )

        accion = "MODIFICAR" if precios_existentes else "CREAR"

        self._requerir_permiso(
            responsable_id,
            self.RECURSO_PRECIOS,
            accion,
        )
        self._requerir_permiso(
            responsable_id,
            self.RECURSO_COSTOS,
            accion,
        )

        moneda = self.repositorio.obtener_moneda_activa(datos["moneda"])

        if moneda is None:
            raise self._error(
                "INVALID_CURRENCY",
                "La moneda no existe o está inactiva en el catálogo MONEDA.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if precios_existentes is None:
            precios = PrecioReferencia(
                referencia_id=referencia.id,
                costo_produccion=datos["costo_produccion"],
                precio_detal=datos["precio_detal"],
                precio_mayorista_nacional=datos[
                    "precio_mayorista_nacional"
                ],
                precio_mayorista_exportacion=datos[
                    "precio_mayorista_exportacion"
                ],
                moneda=moneda.codigo,
                actualizado_por=responsable_id,
            )
            antes = None
        else:
            precios = precios_existentes
            antes = json.dumps(
                self._datos_auditoria(precios),
                ensure_ascii=False,
            )

            precios.costo_produccion = datos["costo_produccion"]
            precios.precio_detal = datos["precio_detal"]
            precios.precio_mayorista_nacional = datos[
                "precio_mayorista_nacional"
            ]
            precios.precio_mayorista_exportacion = datos[
                "precio_mayorista_exportacion"
            ]
            precios.moneda = moneda.codigo
            precios.actualizado_por = responsable_id

        trace_id = str(uuid4())

        try:
            if precios_existentes is None:
                self.repositorio.agregar(precios)
            else:
                self.repositorio.db.flush()

            despues = json.dumps(
                self._datos_auditoria(precios),
                ensure_ascii=False,
            )

            self.repositorio.registrar_auditoria(
                registro_id=precios.id,
                responsable_id=responsable_id,
                accion=accion,
                antes=antes,
                despues=despues,
                trace_id=trace_id,
            )

            self.repositorio.guardar()

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "PRICE_CONFLICT",
                "No fue posible guardar los precios de la referencia.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise

        return self._respuesta(
            referencia=referencia,
            precios=precios,
            usuario_id=responsable_id,
            message="Precios de referencia actualizados correctamente.",
            trace_id=trace_id,
        )