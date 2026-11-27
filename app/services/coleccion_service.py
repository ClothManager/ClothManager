import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.domain.coleccion import Coleccion
from app.repositories.coleccion_repository import ColeccionRepository


class ColeccionService:
    def __init__(self, repositorio: ColeccionRepository):
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

    def _validar_permiso(self, usuario_id: int, accion: str) -> None:
        if self.repositorio.es_administrador(usuario_id):
            return

        validar_permiso(
            db=self.repositorio.db,
            usuario_id=usuario_id,
            modulo="MOD-03",
            recurso="COLECCIONES",
            accion=accion,
        )

    def _foto(self, coleccion: Coleccion) -> dict:
        return {
            "id": coleccion.id,
            "codigo": coleccion.codigo,
            "nombre": coleccion.nombre,
            "anio": coleccion.anio,
            "fecha_inicio": coleccion.fecha_inicio.isoformat(),
            "fecha_inicio_preventa": (
                coleccion.fecha_inicio_preventa.isoformat()
            ),
            "fecha_cierre_preventa": (
                coleccion.fecha_cierre_preventa.isoformat()
            ),
            "fecha_entrega": coleccion.fecha_entrega.isoformat(),
            "estado": coleccion.estado,
            "version": coleccion.version,
        }

    def _validar_fechas(self, datos: dict) -> None:
        inicio = datos["fecha_inicio"]
        inicio_preventa = datos["fecha_inicio_preventa"]
        cierre_preventa = datos["fecha_cierre_preventa"]
        entrega = datos["fecha_entrega"]

        if not (
            inicio <= inicio_preventa
            and inicio_preventa < cierre_preventa
            and cierre_preventa <= entrega
        ):
            raise self._error(
                "INVALID_DATE_ORDER",
                (
                    "Las fechas deben cumplir: inicio <= apertura de "
                    "preventa < cierre de preventa <= entrega."
                ),
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    def crear(
        self,
        datos: dict,
        responsable_id: int,
    ) -> tuple[Coleccion, str]:
        self._validar_permiso(responsable_id, "CREAR")

        if not 2000 <= datos["anio"] <= 2200:
            raise self._error(
                "INVALID_YEAR",
                "El año debe estar entre 2000 y 2200.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        self._validar_fechas(datos)
        codigo = self.repositorio.generar_codigo_coleccion(datos["anio"])

        coleccion = Coleccion(
            codigo=codigo,
            nombre=datos["nombre"].strip(),
            anio=datos["anio"],
            fecha_inicio=datos["fecha_inicio"],
            fecha_inicio_preventa=datos["fecha_inicio_preventa"],
            fecha_cierre_preventa=datos["fecha_cierre_preventa"],
            fecha_entrega=datos["fecha_entrega"],
            estado="EN_CURSO",
            version=1,
            creado_por=responsable_id,
        )
        trace_id = str(uuid4())

        try:
            self.repositorio.agregar(coleccion)
            despues = json.dumps(self._foto(coleccion), ensure_ascii=False)
            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=coleccion.id,
                responsable_id=responsable_id,
                accion="CREAR_COLECCION",
                antes=None,
                despues=despues,
            )
            self.repositorio.guardar()
            return coleccion, trace_id

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe una colección con ese código.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise

    def listar(
        self,
        buscar: str | None,
        anio: int | None,
        estado: str | None,
        page: int,
        page_size: int,
        usuario_id: int,
    ):
        self._validar_permiso(usuario_id, "CONSULTAR")

        if page < 1 or page_size < 1 or page_size > 100:
            raise self._error(
                "BAD_REQUEST",
                (
                    "La página debe ser mayor que cero y page_size "
                    "debe estar entre 1 y 100."
                ),
                status.HTTP_400_BAD_REQUEST,
            )

        colecciones, total = self.repositorio.listar(
            buscar,
            anio,
            estado,
            page,
            page_size,
        )
        return colecciones, total

    def consultar(
        self,
        coleccion_id: int,
        usuario_id: int,
    ) -> Coleccion:
        self._validar_permiso(usuario_id, "CONSULTAR")
        coleccion = self.repositorio.obtener_por_id(coleccion_id)

        if coleccion is None:
            raise self._error(
                "COLLECTION_NOT_FOUND",
                "No se encontró la colección solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        return coleccion

    def actualizar(
        self,
        coleccion_id: int,
        datos: dict,
        responsable_id: int,
    ) -> tuple[Coleccion, str]:
        self._validar_permiso(responsable_id, "MODIFICAR")
        coleccion = self.repositorio.obtener_por_id(coleccion_id)

        if coleccion is None:
            raise self._error(
                "COLLECTION_NOT_FOUND",
                "No se encontró la colección solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        version = datos["version"]

        if coleccion.version != version:
            raise self._error(
                "STALE_VERSION",
                (
                    "La colección cambió. Consulta su versión actual "
                    "antes de editarla."
                ),
                status.HTTP_409_CONFLICT,
            )

        cambios_recibidos = {
            clave: valor
            for clave, valor in datos.items()
            if clave != "version"
        }

        if not cambios_recibidos:
            raise self._error(
                "VALIDATION_ERROR",
                "Debes enviar al menos un campo para actualizar.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        datos_finales = {
            "fecha_inicio": coleccion.fecha_inicio,
            "fecha_inicio_preventa": coleccion.fecha_inicio_preventa,
            "fecha_cierre_preventa": coleccion.fecha_cierre_preventa,
            "fecha_entrega": coleccion.fecha_entrega,
        }

        for campo in datos_finales:
            if campo in cambios_recibidos:
                datos_finales[campo] = cambios_recibidos[campo]

        if any(valor is None for valor in datos_finales.values()):
            raise self._error(
                "VALIDATION_ERROR",
                "Las cuatro fechas de la colección son obligatorias.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        self._validar_fechas(datos_finales)

        if (
            coleccion.estado == "COMPLETADA"
            and cambios_recibidos.get("estado") == "EN_CURSO"
        ):
            raise self._error(
                "INVALID_STATE",
                "Una colección completada no se puede regresar a EN_CURSO.",
                status.HTTP_409_CONFLICT,
            )

        cambios = {
            clave: valor
            for clave, valor in cambios_recibidos.items()
            if valor is not None
        }

        if "nombre" in cambios:
            cambios["nombre"] = cambios["nombre"].strip()

        anio_destino = cambios.get("anio", coleccion.anio)

        if not 2000 <= anio_destino <= 2200:
            raise self._error(
                "INVALID_YEAR",
                "El año debe estar entre 2000 y 2200.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        codigo_corresponde_al_anio = coleccion.codigo.endswith(
            f"-{anio_destino}"
        )

        if (
            anio_destino != coleccion.anio
            or not codigo_corresponde_al_anio
        ):
            cambios["codigo"] = (
                self.repositorio.generar_codigo_coleccion(anio_destino)
            )

        antes = json.dumps(self._foto(coleccion), ensure_ascii=False)
        trace_id = str(uuid4())

        cambios["version"] = version + 1
        cambios["actualizado_en"] = datetime.now(timezone.utc)
        cambios["actualizado_por"] = responsable_id

        try:
            actualizado = self.repositorio.actualizar_si_version_coincide(
                coleccion_id,
                version,
                cambios,
            )

            if not actualizado:
                self.repositorio.deshacer()
                raise self._error(
                    "STALE_VERSION",
                    (
                        "La colección cambió. Consulta su versión actual "
                        "antes de editarla."
                    ),
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            coleccion_actualizada = self.repositorio.obtener_por_id(
                coleccion_id
            )

            despues = json.dumps(
                self._foto(coleccion_actualizada),
                ensure_ascii=False,
            )

            self.repositorio.registrar_auditoria(
                usuario_objetivo_id=coleccion_id,
                responsable_id=responsable_id,
                accion="ACTUALIZAR_COLECCION",
                antes=antes,
                despues=despues,
            )

            self.repositorio.guardar()
            return coleccion_actualizada, trace_id

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe una colección con ese código.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise