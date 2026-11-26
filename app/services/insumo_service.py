import json
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.domain.insumo import Insumo
from app.repositories.insumo_repository import InsumoRepository


BASES_VALIDAS = {"POR_UNIDAD", "POR_LOTE"}


class InsumoService:
    MODULO = "MOD-09"
    RECURSO_INSUMOS = "INSUMOS"
    RECURSO_REQUERIMIENTOS = "REQUERIMIENTOS_INSUMOS"

    def __init__(self, repositorio: InsumoRepository):
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

    def _obtener_referencia_disponible(self, referencia_id: int):
        referencia = self.repositorio.obtener_referencia(referencia_id)

        if referencia is None or not referencia.activo:
            raise self._error(
                "REFERENCE_NOT_FOUND",
                "La referencia no existe o está inactiva.",
                status.HTTP_404_NOT_FOUND,
            )

        return referencia

    def _representar_insumo(self, insumo, tipo, unidad) -> dict:
        return {
            "id": insumo.id,
            "codigo": insumo.codigo,
            "nombre": insumo.nombre,
            "tipoInsumo": {
                "id": tipo.id,
                "codigo": tipo.codigo,
                "nombre": tipo.nombre,
            },
            "unidadMedida": {
                "id": unidad.id,
                "codigo": unidad.codigo,
                "nombre": unidad.nombre,
            },
            "costoReferencia": (
                float(insumo.costo_referencia)
                if insumo.costo_referencia is not None
                else None
            ),
            "activo": insumo.activo,
        }

    def crear_insumo(self, datos: dict, responsable_id: int) -> dict:
        self._validar_permiso(
            responsable_id,
            self.RECURSO_INSUMOS,
            "CREAR",
        )

        codigo = datos["codigo"].strip().upper()
        nombre = datos["nombre"].strip()

        if self.repositorio.existe_codigo_insumo(codigo):
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe un insumo con ese código.",
                status.HTTP_409_CONFLICT,
            )

        tipo = self.repositorio.obtener_tipo_insumo_activo(
            datos["tipo_insumo_id"]
        )
        if tipo is None:
            raise self._error(
                "INVALID_SUPPLY_TYPE",
                "El tipo de insumo no existe o está inactivo.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        unidad = self.repositorio.obtener_unidad_activa(
            datos["unidad_medida_id"]
        )
        if unidad is None:
            raise self._error(
                "INVALID_UNIT",
                "La unidad de medida no existe o está inactiva.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        insumo = Insumo(
            codigo=codigo,
            nombre=nombre,
            tipo_insumo_id=tipo.id,
            unidad_medida_id=unidad.id,
            costo_referencia=datos.get("costo_referencia"),
            activo=True,
            creado_por=responsable_id,
        )

        trace_id = str(uuid4())

        try:
            self.repositorio.agregar_insumo(insumo)
            respuesta = self._representar_insumo(insumo, tipo, unidad)

            self.repositorio.registrar_auditoria(
                registro_id=insumo.id,
                responsable_id=responsable_id,
                accion="CREAR_INSUMO",
                antes=None,
                despues=json.dumps(respuesta, ensure_ascii=False),
                trace_id=trace_id,
            )
            self.repositorio.guardar()

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe un insumo con ese código.",
                status.HTTP_409_CONFLICT,
            ) from error
        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Insumo creado correctamente.",
            "data": respuesta,
            "trace_id": trace_id,
        }

    def listar_insumos(self, usuario_id: int) -> dict:
        self._validar_permiso(
            usuario_id,
            self.RECURSO_INSUMOS,
            "CONSULTAR",
        )

        resultados = self.repositorio.listar_insumos_activos()

        return {
            "success": True,
            "message": "Insumos consultados correctamente.",
            "data": [
                self._representar_insumo(insumo, tipo, unidad)
                for insumo, tipo, unidad in resultados
            ],
            "trace_id": str(uuid4()),
        }

    def _representar_requerimiento(self, linea, insumo, unidad) -> dict:
        return {
            "insumoId": insumo.id,
            "codigo": insumo.codigo,
            "nombre": insumo.nombre,
            "cantidad": float(linea.cantidad),
            "unidadMedida": {
                "id": unidad.id,
                "codigo": unidad.codigo,
                "nombre": unidad.nombre,
            },
            "baseCalculo": linea.base_calculo,
        }

    def consultar_requerimientos(
        self,
        referencia_id: int,
        usuario_id: int,
        base_calculo: str | None = None,
    ) -> dict:
        self._validar_permiso(
            usuario_id,
            self.RECURSO_REQUERIMIENTOS,
            "CONSULTAR",
        )

        referencia = self._obtener_referencia_disponible(referencia_id)

        if base_calculo is not None:
            base_calculo = base_calculo.upper()
            if base_calculo not in BASES_VALIDAS:
                raise self._error(
                    "INVALID_CALCULATION_BASE",
                    "La base debe ser POR_UNIDAD o POR_LOTE.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

        resultados = self.repositorio.obtener_requerimientos(
            referencia_id,
            base_calculo,
        )

        data = {
            "referenciaId": referencia.id,
            "referencia": referencia.nombre_referencia,
            "insumos": [
                self._representar_requerimiento(linea, insumo, unidad)
                for linea, insumo, unidad in resultados
            ],
            "totalLineas": len(resultados),
        }

        if base_calculo is not None:
            data["baseCalculo"] = base_calculo

        return {
            "success": True,
            "message": "Requerimientos consultados correctamente.",
            "data": data,
            "trace_id": str(uuid4()),
        }

    def actualizar_requerimientos(
        self,
        referencia_id: int,
        base_calculo: str,
        lineas_datos: list[dict],
        responsable_id: int,
    ) -> dict:
        self._validar_permiso(
            responsable_id,
            self.RECURSO_REQUERIMIENTOS,
            "MODIFICAR",
        )

        referencia = self._obtener_referencia_disponible(referencia_id)
        base_calculo = base_calculo.strip().upper()

        if base_calculo not in BASES_VALIDAS:
            raise self._error(
                "INVALID_CALCULATION_BASE",
                "La base debe ser POR_UNIDAD o POR_LOTE.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        lineas_validadas = []
        insumos_vistos = set()

        for datos in lineas_datos:
            insumo_id = datos["insumo_id"]
            unidad_id = datos["unidad_medida_id"]
            cantidad = datos["cantidad"]

            if insumo_id in insumos_vistos:
                raise self._error(
                    "DUPLICATE_REQUIREMENT",
                    "No se puede repetir un insumo para la misma base.",
                    status.HTTP_409_CONFLICT,
                )
            insumos_vistos.add(insumo_id)

            if not isinstance(cantidad, Decimal):
                cantidad = Decimal(str(cantidad))

            if cantidad <= 0:
                raise self._error(
                    "INVALID_QUANTITY",
                    "La cantidad debe ser mayor que cero.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            insumo = self.repositorio.obtener_insumo_activo(insumo_id)
            if insumo is None:
                raise self._error(
                    "SUPPLY_NOT_FOUND",
                    f"El insumo {insumo_id} no existe o está inactivo.",
                    status.HTTP_404_NOT_FOUND,
                )

            unidad = self.repositorio.obtener_unidad_activa(unidad_id)
            if unidad is None:
                raise self._error(
                    "INVALID_UNIT",
                    "La unidad no existe o está inactiva.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            if unidad.id != insumo.unidad_medida_id:
                raise self._error(
                    "INVALID_UNIT",
                    (
                        f"La unidad {unidad.codigo} no coincide con la unidad "
                        f"del insumo {insumo.codigo}."
                    ),
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            lineas_validadas.append(
                {
                    "insumo_id": insumo.id,
                    "cantidad": cantidad,
                    "unidad_medida_id": unidad.id,
                }
            )

        anteriores = self.repositorio.obtener_requerimientos(
            referencia_id,
            base_calculo,
        )

        antes = json.dumps(
            [
                self._representar_requerimiento(linea, insumo, unidad)
                for linea, insumo, unidad in anteriores
            ],
            ensure_ascii=False,
        )

        despues_datos = [
            {
                "insumoId": linea["insumo_id"],
                "cantidad": str(linea["cantidad"]),
                "unidadMedidaId": linea["unidad_medida_id"],
                "baseCalculo": base_calculo,
            }
            for linea in lineas_validadas
        ]

        trace_id = str(uuid4())

        try:
            self.repositorio.reemplazar_requerimientos(
                referencia_id=referencia_id,
                base_calculo=base_calculo,
                lineas=lineas_validadas,
                responsable_id=responsable_id,
            )

            self.repositorio.registrar_auditoria(
                registro_id=referencia_id,
                responsable_id=responsable_id,
                accion="ACTUALIZAR_REQUERIMIENTOS",
                antes=antes,
                despues=json.dumps(despues_datos, ensure_ascii=False),
                trace_id=trace_id,
            )

            self.repositorio.guardar()

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "INVALID_REQUIREMENT",
                "No se pudo guardar la lista de requerimientos.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from error
        except Exception:
            self.repositorio.deshacer()
            raise

        guardados = self.repositorio.obtener_requerimientos(
            referencia_id,
            base_calculo,
        )

        return {
            "success": True,
            "message": "Requerimientos registrados correctamente.",
            "data": {
                "referenciaId": referencia.id,
                "referencia": referencia.nombre_referencia,
                "baseCalculo": base_calculo,
                "insumos": [
                    self._representar_requerimiento(linea, insumo, unidad)
                    for linea, insumo, unidad in guardados
                ],
                "totalLineas": len(guardados),
            },
            "trace_id": trace_id,
        }