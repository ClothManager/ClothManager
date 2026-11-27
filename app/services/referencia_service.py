import json
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.permisos import validar_permiso
from app.domain.referencia import Referencia
from app.repositories.referencia_repository import ReferenciaRepository


class ReferenciaService:
    def __init__(self, repositorio: ReferenciaRepository):
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
            recurso="REFERENCIAS",
            accion=accion,
        )

    def _representar(self, detalle: tuple) -> dict:
        referencia, color, coleccion, categoria = detalle

        return {
            "id": referencia.id,
            "codigo": referencia.codigo,
            "nombre_referencia": referencia.nombre_referencia,
            "color": {
                "id": color.id,
                "codigo": color.codigo,
                "nombre": color.nombre,
            },
            "coleccion": {
                "id": coleccion.id,
                "codigo": coleccion.codigo,
                "nombre": coleccion.nombre,
                "anio": coleccion.anio,
            },
            "anio": referencia.anio,
            "categoria": {
                "id": categoria.id,
                "codigo": categoria.codigo,
                "nombre": categoria.nombre,
            },
            "activo": referencia.activo,
            "version": referencia.version,
        }

    def crear(
        self,
        datos: dict,
        responsable_id: int,
    ) -> dict:
        self._validar_permiso(responsable_id, "CREAR")

        codigo = datos["codigo"].strip().upper()
        nombre = datos["nombre_referencia"].strip()

        if not codigo:
            raise self._error(
                "VALIDATION_ERROR",
                "El código de referencia no puede estar vacío.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not nombre:
            raise self._error(
                "VALIDATION_ERROR",
                "El nombre de referencia no puede estar vacío.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        coleccion = self.repositorio.obtener_coleccion(
            datos["coleccion_id"]
        )

        if coleccion is None:
            raise self._error(
                "COLLECTION_NOT_FOUND",
                "La colección indicada no existe.",
                status.HTTP_404_NOT_FOUND,
            )

        if coleccion.estado != "EN_CURSO":
            raise self._error(
                "INVALID_COLLECTION",
                "La colección no está disponible para nuevas referencias.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # El año se obtiene de la colección; el cliente no lo envía.
        anio = coleccion.anio

        if not 2000 <= anio <= 2200:
            raise self._error(
                "INVALID_YEAR",
                "El año de la colección no es válido.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        color = self.repositorio.obtener_color_activo(datos["color_id"])

        if color is None:
            raise self._error(
                "INVALID_CATALOG_VALUE",
                "El color no existe o está inactivo.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        categoria = self.repositorio.obtener_tipo_prenda_activo(
            datos["categoria_id"]
        )

        if categoria is None:
            raise self._error(
                "INVALID_CATALOG_VALUE",
                (
                    "El tipo de prenda no existe, está inactivo "
                    "o no pertenece al catálogo TIPO_PRENDA."
                ),
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if self.repositorio.existe_codigo(codigo):
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe una referencia con ese código.",
                status.HTTP_409_CONFLICT,
            )

        referencia = Referencia(
            codigo=codigo,
            nombre_referencia=nombre,
            coleccion_id=coleccion.id,
            color_id=color.id,
            categoria_id=categoria.id,
            anio=anio,
            activo=True,
            version=1,
            creado_por=responsable_id,
        )

        trace_id = str(uuid4())

        try:
            self.repositorio.agregar(referencia)

            detalle = self.repositorio.obtener_detalle(referencia.id)

            if detalle is None:
                raise self._error(
                    "INTERNAL_ERROR",
                    "No fue posible consultar la referencia recién creada.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            data = self._representar(detalle)
            despues = json.dumps(data, ensure_ascii=False)

            self.repositorio.registrar_auditoria(
                referencia_id=referencia.id,
                responsable_id=responsable_id,
                trace_id=trace_id,
                despues=despues,
            )

            self.repositorio.guardar()

            return {
                "success": True,
                "message": "Referencia creada y asociada correctamente.",
                "data": data,
                "trace_id": trace_id,
            }

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe una referencia con ese código.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise

    def consultar(
        self,
        referencia_id: int,
        usuario_id: int,
    ) -> dict:
        self._validar_permiso(usuario_id, "CONSULTAR")

        detalle = self.repositorio.obtener_detalle(referencia_id)

        if detalle is None:
            raise self._error(
                "REFERENCE_NOT_FOUND",
                "No se encontró la referencia solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        return {
            "success": True,
            "message": "Referencia consultada correctamente.",
            "data": self._representar(detalle),
            "trace_id": str(uuid4()),
        }

    def listar(
        self,
        usuario_id: int,
        buscar: str | None = None,
        coleccion_id: int | None = None,
        anio: int | None = None,
        color_id: int | None = None,
        categoria_id: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        self._validar_permiso(usuario_id, "CONSULTAR")

        if page < 1 or page_size < 1 or page_size > 100:
            raise self._error(
                "BAD_REQUEST",
                (
                    "page debe ser mayor que cero y page_size "
                    "debe estar entre 1 y 100."
                ),
                status.HTTP_400_BAD_REQUEST,
            )

        if anio is not None and not 2000 <= anio <= 2200:
            raise self._error(
                "INVALID_YEAR",
                "El año debe estar entre 2000 y 2200.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if coleccion_id is not None:
            coleccion = self.repositorio.obtener_coleccion(coleccion_id)

            if coleccion is None:
                raise self._error(
                    "COLLECTION_NOT_FOUND",
                    "La colección indicada no existe.",
                    status.HTTP_404_NOT_FOUND,
                )

        referencias, total = self.repositorio.listar(
            buscar=buscar,
            coleccion_id=coleccion_id,
            anio=anio,
            color_id=color_id,
            categoria_id=categoria_id,
            page=page,
            page_size=page_size,
        )

        return {
            "success": True,
            "message": "Referencias consultadas correctamente.",
            "data": [
                self._representar(detalle)
                for detalle in referencias
            ],
            "meta": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
            "trace_id": str(uuid4()),
        }