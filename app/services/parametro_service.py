import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.domain.parametro import AuditoriaParametro, Color, Talla
from app.repositories.parametro_repository import ParametroRepository


class ParametroService:
    def __init__(self, repositorio: ParametroRepository):
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

    def _validar_paginacion(self, page: int, page_size: int) -> None:
        if page < 1:
            raise self._error(
                "BAD_REQUEST",
                "La página debe ser mayor que cero",
                status.HTTP_400_BAD_REQUEST,
            )

        if page_size < 1 or page_size > 100:
            raise self._error(
                "BAD_REQUEST",
                "page_size debe estar entre 1 y 100",
                status.HTTP_400_BAD_REQUEST,
            )

    def _foto_color(self, color: Color) -> dict:
        return {
            "id": color.id,
            "codigo": color.codigo,
            "nombre": color.nombre,
            "activo": color.activo,
            "version": color.version,
        }

    def _auditar(
        self,
        color: Color,
        responsable_id: int,
        accion: str,
        antes: dict | None,
        despues: dict,
        trace_id: str,
    ) -> None:
        auditoria = AuditoriaParametro(
            catalogo="COLOR",
            registro_id=color.id,
            accion=accion,
            responsable_id=responsable_id,
            antes=(
                json.dumps(antes, ensure_ascii=False)
                if antes is not None
                else None
            ),
            despues=json.dumps(despues, ensure_ascii=False),
            trace_id=trace_id,
        )

        self.repositorio.agregar_auditoria_parametro(auditoria)

    def listar_tallas(
        self,
        buscar: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Talla], int]:
        self._validar_paginacion(page, page_size)

        tallas = self.repositorio.listar_tallas()

        if buscar:
            termino = buscar.strip().casefold()
            tallas = [
                talla
                for talla in tallas
                if termino in talla.codigo.casefold()
                or termino in talla.nombre.casefold()
            ]

        if activo is False:
            tallas = []

        total = len(tallas)
        inicio = (page - 1) * page_size

        return tallas[inicio:inicio + page_size], total

    def listar_colores(
        self,
        buscar: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Color], int]:
        self._validar_paginacion(page, page_size)

        return self.repositorio.listar_colores(
            buscar=buscar,
            activo=activo,
            page=page,
            page_size=page_size,
        )

    def consultar_talla(self, talla_id: int) -> Talla:
        talla = self.repositorio.obtener_talla_por_id(talla_id)

        if talla is None:
            raise self._error(
                "PARAMETER_NOT_FOUND",
                "No se encontró la talla solicitada",
                status.HTTP_404_NOT_FOUND,
            )

        return talla

    def consultar_color(self, color_id: int) -> Color:
        color = self.repositorio.obtener_color_por_id(color_id)

        if color is None:
            raise self._error(
                "PARAMETER_NOT_FOUND",
                "No se encontró el color solicitado",
                status.HTTP_404_NOT_FOUND,
            )

        return color

    def crear_color(
        self,
        datos: dict[str, str],
        responsable_id: int,
    ) -> tuple[Color, str]:
        trace_id = str(uuid4())
        codigo_temporal = f"TMP-{uuid4().hex[:20]}"

        color = Color(
            codigo=codigo_temporal,
            nombre=datos["nombre"].strip(),
            activo=True,
            creado_por=responsable_id,
            version=1,
        )

        try:
            self.repositorio.agregar_color(color)
            color.codigo = f"COL-{color.id:04d}"

            self._auditar(
                color=color,
                responsable_id=responsable_id,
                accion="CREAR",
                antes=None,
                despues=self._foto_color(color),
                trace_id=trace_id,
            )

            self.repositorio.guardar_cambios()
            return color, trace_id

        except IntegrityError as error:
            self.repositorio.deshacer_cambios()
            raise self._error(
                "DUPLICATE_CODE",
                "No se pudo generar un código único para el color",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def actualizar_color(
        self,
        color_id: int,
        datos: dict,
        responsable_id: int,
    ) -> tuple[Color, str]:
        color = self.consultar_color(color_id)
        version_esperada = datos["version"]

        if color.version != version_esperada:
            raise self._error(
                "STALE_VERSION",
                "El color cambió. Consulta su versión actual antes de editarlo.",
                status.HTTP_409_CONFLICT,
            )

        antes = self._foto_color(color)
        trace_id = str(uuid4())
        cambios = {
            "nombre": datos["nombre"].strip(),
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
            "version": version_esperada + 1,
        }

        try:
            actualizado = self.repositorio.actualizar_color_si_version_coincide(
                color_id=color_id,
                version=version_esperada,
                cambios=cambios,
            )

            if not actualizado:
                self.repositorio.deshacer_cambios()
                raise self._error(
                    "STALE_VERSION",
                    "El color cambió. Consulta su versión actual antes de editarlo.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            color_actualizado = self.consultar_color(color_id)

            self._auditar(
                color=color_actualizado,
                responsable_id=responsable_id,
                accion="MODIFICAR",
                antes=antes,
                despues=self._foto_color(color_actualizado),
                trace_id=trace_id,
            )

            self.repositorio.guardar_cambios()
            return color_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer_cambios()
            raise

    def cambiar_estado_color(
        self,
        color_id: int,
        datos: dict,
        responsable_id: int,
    ) -> tuple[Color, str]:
        color = self.consultar_color(color_id)
        version_esperada = datos["version"]

        if color.version != version_esperada:
            raise self._error(
                "STALE_VERSION",
                "El color cambió. Consulta su versión actual antes de continuar.",
                status.HTTP_409_CONFLICT,
            )

        antes = self._foto_color(color)
        trace_id = str(uuid4())
        despues = {
            "id": color.id,
            "codigo": color.codigo,
            "nombre": color.nombre,
            "activo": datos["activo"],
            "version": version_esperada + 1,
            "motivo": datos["motivo"],
        }
        cambios = {
            "activo": datos["activo"],
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
            "version": version_esperada + 1,
        }

        try:
            actualizado = self.repositorio.actualizar_color_si_version_coincide(
                color_id=color_id,
                version=version_esperada,
                cambios=cambios,
            )

            if not actualizado:
                self.repositorio.deshacer_cambios()
                raise self._error(
                    "STALE_VERSION",
                    "El color cambió. Consulta su versión actual antes de continuar.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            color_actualizado = self.consultar_color(color_id)

            self._auditar(
                color=color_actualizado,
                responsable_id=responsable_id,
                accion="ACTIVAR" if datos["activo"] else "INACTIVAR",
                antes=antes,
                despues=despues,
                trace_id=trace_id,
            )

            self.repositorio.guardar_cambios()
            return color_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer_cambios()
            raise