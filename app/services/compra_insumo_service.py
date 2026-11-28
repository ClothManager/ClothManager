import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.domain.compra_insumo import (
    CompraInsumo,
    CompraInsumoDetalle,
    ExistenciaInsumo,
    MovimientoBodega,
    Proveedor,
    RecepcionInsumo,
    RecepcionInsumoDetalle,
)
from app.repositories.compra_insumo_repository import (
    CompraInsumoRepository,
)


class CompraInsumoService:
    MODULO = "MOD-09"
    RECURSO_COMPRAS = "COMPRAS_INSUMOS"
    RECURSO_BODEGA = "BODEGA_RECEPCIONES"
    RECURSO_PROVEEDORES = "PROVEEDORES"

    def __init__(self, repositorio: CompraInsumoRepository):
        self.repositorio = repositorio

    def _error(self, codigo: str, message: str, http: int):
        return HTTPException(
            status_code=http,
            detail={
                "codigo": codigo,
                "message": message,
                "detalle": [],
            },
        )

    def _permiso(
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

    def _proveedor_json(self, proveedor: Proveedor) -> dict:
        return {
            "id": proveedor.id,
            "identificacion": proveedor.identificacion,
            "nombre": proveedor.nombre_razon_social,
            "telefono": proveedor.telefono,
            "correo": proveedor.correo,
            "activo": proveedor.activo,
        }

    def crear_proveedor(self, datos: dict, responsable_id: int) -> dict:
        self._permiso(
            responsable_id,
            self.RECURSO_PROVEEDORES,
            "CREAR",
        )
        identificacion = datos["identificacion"].strip()
        if self.repositorio.existe_identificacion_proveedor(identificacion):
            raise self._error(
                "DUPLICATE_SUPPLIER",
                "Ya existe un proveedor con esa identificación.",
                status.HTTP_409_CONFLICT,
            )

        proveedor = Proveedor(
            identificacion=identificacion,
            nombre_razon_social=datos["nombre_razon_social"].strip(),
            telefono=datos.get("telefono"),
            correo=datos.get("correo"),
            activo=True,
            creado_por=responsable_id,
        )
        trace_id = str(uuid4())

        try:
            self.repositorio.agregar_proveedor(proveedor)
            data = self._proveedor_json(proveedor)
            self.repositorio.registrar_auditoria(
                "PROVEEDORES",
                proveedor.id,
                responsable_id,
                "CREAR",
                None,
                json.dumps(data, ensure_ascii=False),
                trace_id,
            )
            self.repositorio.guardar()
        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_SUPPLIER",
                "Ya existe un proveedor con esa identificación.",
                status.HTTP_409_CONFLICT,
            ) from error
        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Proveedor creado correctamente.",
            "data": data,
            "trace_id": trace_id,
        }

    def listar_proveedores(self, usuario_id: int) -> dict:
        self._permiso(
            usuario_id,
            self.RECURSO_PROVEEDORES,
            "CONSULTAR",
        )
        return {
            "success": True,
            "message": "Proveedores consultados correctamente.",
            "data": [
                self._proveedor_json(p)
                for p in self.repositorio.listar_proveedores()
            ],
            "trace_id": str(uuid4()),
        }

    def _compra_json(self, detalle) -> dict:
        compra, proveedor, lineas = detalle
        return {
            "id": compra.id,
            "numeroCompra": compra.numero_compra,
            "proveedor": self._proveedor_json(proveedor),
            "fechaCompra": compra.fecha_compra.isoformat(),
            "estado": compra.estado,
            "lineas": [
                {
                    "id": linea.id,
                    "insumoId": insumo.id,
                    "codigo": insumo.codigo,
                    "nombre": insumo.nombre,
                    "cantidadSolicitada": float(
                        linea.cantidad_solicitada
                    ),
                    "unidadMedida": {
                        "id": unidad.id,
                        "codigo": unidad.codigo,
                        "nombre": unidad.nombre,
                    },
                    "costoUnitario": float(linea.costo_unitario),
                    "cantidadRecibidaAcumulada": float(
                        self.repositorio.cantidad_recibida_acumulada(
                            linea.id
                        )
                    ),
                }
                for linea, insumo, unidad in lineas
            ],
        }

    def crear_compra(self, datos: dict, responsable_id: int) -> dict:
        self._permiso(
            responsable_id,
            self.RECURSO_COMPRAS,
            "CREAR",
        )

        proveedor = self.repositorio.obtener_proveedor_activo(
            datos["proveedor_id"]
        )
        if proveedor is None:
            raise self._error(
                "SUPPLIER_NOT_FOUND",
                "El proveedor no existe o está inactivo.",
                status.HTTP_404_NOT_FOUND,
            )

        for linea in datos["lineas"]:
            insumo = self.repositorio.obtener_insumo_activo(
                linea["insumo_id"]
            )
            if insumo is None:
                raise self._error(
                    "SUPPLY_NOT_FOUND",
                    f"El insumo {linea['insumo_id']} no existe o está inactivo.",
                    status.HTTP_404_NOT_FOUND,
                )

            unidad = self.repositorio.obtener_unidad_activa(
                linea["unidad_medida_id"]
            )
            if unidad is None or unidad.id != insumo.unidad_medida_id:
                raise self._error(
                    "INVALID_UNIT",
                    "La unidad no existe, está inactiva o no corresponde al insumo.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

        compra = CompraInsumo(
            numero_compra=f"COM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
            proveedor_id=proveedor.id,
            fecha_compra=datos["fecha_compra"],
            estado="REGISTRADA",
            creado_por=responsable_id,
        )
        trace_id = str(uuid4())

        try:
            self.repositorio.agregar_compra(compra)
            for linea in datos["lineas"]:
                self.repositorio.agregar_detalle_compra(
                    CompraInsumoDetalle(
                        compra_id=compra.id,
                        insumo_id=linea["insumo_id"],
                        cantidad_solicitada=linea["cantidad_solicitada"],
                        unidad_medida_id=linea["unidad_medida_id"],
                        costo_unitario=linea["costo_unitario"],
                    )
                )

            detalle = self.repositorio.obtener_detalle_compra(compra.id)
            data = self._compra_json(detalle)
            self.repositorio.registrar_auditoria(
                "COMPRAS_INSUMOS",
                compra.id,
                responsable_id,
                "CREAR",
                None,
                json.dumps(data, ensure_ascii=False),
                trace_id,
            )
            self.repositorio.guardar()
        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "PURCHASE_CONFLICT",
                "No fue posible registrar la compra.",
                status.HTTP_409_CONFLICT,
            ) from error
        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Compra de insumos registrada correctamente.",
            "data": data,
            "trace_id": trace_id,
        }

    def consultar_compra(self, compra_id: int, usuario_id: int) -> dict:
        self._permiso(
            usuario_id,
            self.RECURSO_COMPRAS,
            "CONSULTAR",
        )
        detalle = self.repositorio.obtener_detalle_compra(compra_id)
        if detalle is None:
            raise self._error(
                "PURCHASE_NOT_FOUND",
                "La compra indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )
        return {
            "success": True,
            "message": "Compra consultada correctamente.",
            "data": self._compra_json(detalle),
            "trace_id": str(uuid4()),
        }

    def listar_compras(self, usuario_id: int, estado: str | None = None) -> dict:
        self._permiso(
            usuario_id,
            self.RECURSO_COMPRAS,
            "CONSULTAR",
        )
        compras = self.repositorio.listar_compras(estado)
        return {
            "success": True,
            "message": "Compras consultadas correctamente.",
            "data": [
                self._compra_json(
                    self.repositorio.obtener_detalle_compra(compra.id)
                )
                for compra in compras
            ],
            "trace_id": str(uuid4()),
        }

    def _recepcion_json(self, recepcion: RecepcionInsumo) -> dict:
        detalles = self.repositorio.obtener_detalles_recepcion(recepcion.id)
        return {
            "id": recepcion.id,
            "compraId": recepcion.compra_id,
            "fechaRecepcion": recepcion.fecha_recepcion.isoformat(),
            "estado": recepcion.estado,
            "lineas": [
                {
                    "compraDetalleId": compra_detalle.id,
                    "insumoId": insumo.id,
                    "insumo": insumo.nombre,
                    "cantidadRecibida": float(linea.cantidad_recibida),
                    "unidadMedida": unidad.codigo,
                    "novedad": linea.novedad,
                    "movimientoBodegaId": (
                        movimiento.id if movimiento else None
                    ),
                }
                for linea, compra_detalle, insumo, unidad, movimiento
                in detalles
            ],
        }

    def registrar_recepcion(
        self,
        compra_id: int,
        lineas: list[dict],
        responsable_id: int,
        clave_idempotencia: str,
    ) -> dict:
        self._permiso(
            responsable_id,
            self.RECURSO_BODEGA,
            "CREAR",
        )

        compra = self.repositorio.obtener_compra(compra_id)
        if compra is None:
            raise self._error(
                "PURCHASE_NOT_FOUND",
                "La compra indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )
        if compra.estado == "CANCELADA":
            raise self._error(
                "PURCHASE_CLOSED",
                "No se puede recibir una compra cancelada.",
                status.HTTP_409_CONFLICT,
            )
        if compra.estado == "RECIBIDA":
            raise self._error(
                "PURCHASE_CLOSED",
                "La compra ya fue recibida completamente.",
                status.HTTP_409_CONFLICT,
            )

        solicitud_hash = hashlib.sha256(
            json.dumps(lineas, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        anterior = self.repositorio.obtener_recepcion_por_clave(
            clave_idempotencia
        )
        if anterior is not None:
            if anterior.solicitud_hash != solicitud_hash:
                raise self._error(
                    "IDEMPOTENCY_KEY_REUSED",
                    "La clave de recepción ya se utilizó con otros datos.",
                    status.HTTP_409_CONFLICT,
                )
            return {
                "success": True,
                "message": "La recepción ya había sido confirmada.",
                "data": self._recepcion_json(anterior),
                "trace_id": str(uuid4()),
            }

        lineas_validadas = []
        for entrada in lineas:
            resultado = self.repositorio.obtener_linea_compra(
                compra_id,
                entrada["compra_detalle_id"],
            )
            if resultado is None:
                raise self._error(
                    "PURCHASE_LINE_NOT_FOUND",
                    "La línea no pertenece a esta compra.",
                    status.HTTP_404_NOT_FOUND,
                )

            linea_compra, insumo, unidad_compra = resultado
            unidad_recibida = self.repositorio.obtener_unidad_activa(
                entrada["unidad_medida_id"]
            )

            if (
                unidad_recibida is None
                or unidad_recibida.id != linea_compra.unidad_medida_id
            ):
                raise self._error(
                    "INVALID_UNIT",
                    "La unidad recibida no coincide con la unidad comprada.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            pendiente = (
                linea_compra.cantidad_solicitada
                - self.repositorio.cantidad_recibida_acumulada(
                    linea_compra.id
                )
            )
            cantidad = entrada["cantidad_recibida"]

            if cantidad > pendiente:
                raise self._error(
                    "RECEIPT_EXCEEDS_PENDING",
                    "La cantidad recibida supera lo pendiente.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            novedad = entrada.get("novedad")
            if cantidad != pendiente and not novedad:
                raise self._error(
                    "RECEIPT_DISCREPANCY",
                    "La diferencia requiere una novedad descriptiva.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            lineas_validadas.append(
                (linea_compra, insumo, unidad_compra, cantidad, novedad)
            )

        trace_id = str(uuid4())
        try:
            recepcion = self.repositorio.agregar_recepcion(
                RecepcionInsumo(
                    compra_id=compra.id,
                    estado="CONFIRMADA",
                    recibido_por=responsable_id,
                    clave_idempotencia=clave_idempotencia,
                    solicitud_hash=solicitud_hash,
                )
            )

            for linea_compra, insumo, unidad, cantidad, novedad in lineas_validadas:
                detalle = self.repositorio.agregar_detalle_recepcion(
                    RecepcionInsumoDetalle(
                        recepcion_id=recepcion.id,
                        compra_detalle_id=linea_compra.id,
                        cantidad_recibida=cantidad,
                        unidad_medida_id=unidad.id,
                        novedad=novedad,
                    )
                )

                if cantidad > 0:
                    existencia = self.repositorio.obtener_existencia(
                        insumo.id,
                        unidad.id,
                    )
                    if existencia is None:
                        existencia = self.repositorio.agregar_existencia(
                            ExistenciaInsumo(
                                insumo_id=insumo.id,
                                unidad_medida_id=unidad.id,
                                cantidad_disponible=Decimal("0"),
                            )
                        )

                    existencia.cantidad_disponible += cantidad

                    self.repositorio.agregar_movimiento(
                        MovimientoBodega(
                            tipo_movimiento="ENTRADA",
                            compra_id=compra.id,
                            recepcion_id=recepcion.id,
                            recepcion_detalle_id=detalle.id,
                            insumo_id=insumo.id,
                            cantidad=cantidad,
                            unidad_medida_id=unidad.id,
                            usuario_id=responsable_id,
                        )
                    )

            self.repositorio.db.flush()
            detalle_compra = self.repositorio.obtener_detalle_compra(compra.id)
            lineas_compra = detalle_compra[2]
            cantidades_totales = [
                (
                    linea.cantidad_solicitada,
                    self.repositorio.cantidad_recibida_acumulada(linea.id),
                )
                for linea, _, _ in lineas_compra
            ]

            if all(recibida >= solicitada for solicitada, recibida in cantidades_totales):
                compra.estado = "RECIBIDA"
            elif any(recibida > 0 for _, recibida in cantidades_totales):
                compra.estado = "PARCIAL"
            else:
                compra.estado = "REGISTRADA"

            compra.actualizado_en = datetime.now(timezone.utc)

            self.repositorio.registrar_auditoria(
                "RECEPCIONES_INSUMOS",
                recepcion.id,
                responsable_id,
                "CONFIRMAR",
                None,
                json.dumps(
                    self._recepcion_json(recepcion),
                    ensure_ascii=False,
                ),
                trace_id,
            )
            self.repositorio.guardar()

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "RECEIPT_CONFLICT",
                "La recepción ya fue procesada o no pudo guardarse.",
                status.HTTP_409_CONFLICT,
            ) from error
        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Recepción confirmada por Bodega.",
            "data": {
                **self._recepcion_json(recepcion),
                "estadoCompra": compra.estado,
            },
            "trace_id": trace_id,
        }

    def consultar_recepciones(
        self,
        compra_id: int,
        usuario_id: int,
    ) -> dict:
        self._permiso(
            usuario_id,
            self.RECURSO_BODEGA,
            "CONSULTAR",
        )
        if self.repositorio.obtener_compra(compra_id) is None:
            raise self._error(
                "PURCHASE_NOT_FOUND",
                "La compra indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )
        recepciones = self.repositorio.listar_recepciones(compra_id)
        return {
            "success": True,
            "message": "Recepciones consultadas correctamente.",
            "data": [
                self._recepcion_json(recepcion)
                for recepcion in recepciones
            ],
            "trace_id": str(uuid4()),
        }

    def cancelar_compra(
        self,
        compra_id: int,
        motivo: str,
        responsable_id: int,
    ) -> dict:
        self._permiso(
            responsable_id,
            self.RECURSO_COMPRAS,
            "MODIFICAR",
        )
        compra = self.repositorio.obtener_compra(compra_id)
        if compra is None:
            raise self._error(
                "PURCHASE_NOT_FOUND",
                "La compra indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )
        if compra.estado != "REGISTRADA":
            raise self._error(
                "PURCHASE_CLOSED",
                "Solo se puede cancelar una compra sin recepciones.",
                status.HTTP_409_CONFLICT,
            )

        compra.estado = "CANCELADA"
        compra.actualizado_en = datetime.now(timezone.utc)
        trace_id = str(uuid4())
        try:
            self.repositorio.registrar_auditoria(
                "COMPRAS_INSUMOS",
                compra.id,
                responsable_id,
                "CANCELAR",
                json.dumps({"estado": "REGISTRADA"}),
                json.dumps(
                    {"estado": "CANCELADA", "motivo": motivo},
                    ensure_ascii=False,
                ),
                trace_id,
            )
            self.repositorio.guardar()
        except Exception:
            self.repositorio.deshacer()
            raise

        return {
            "success": True,
            "message": "Compra cancelada correctamente.",
            "data": {"id": compra.id, "estado": compra.estado},
            "trace_id": trace_id,
        }

    def listar_existencias(self, usuario_id: int) -> dict:
        self._permiso(
            usuario_id,
            self.RECURSO_BODEGA,
            "CONSULTAR",
        )
        filas = self.repositorio.listar_existencias()
        return {
            "success": True,
            "message": "Existencias consultadas correctamente.",
            "data": [
                {
                    "insumoId": insumo.id,
                    "codigo": insumo.codigo,
                    "nombre": insumo.nombre,
                    "unidadMedida": unidad.codigo,
                    "cantidadDisponible": float(
                        existencia.cantidad_disponible
                    ),
                }
                for existencia, insumo, unidad in filas
            ],
            "trace_id": str(uuid4()),
        }