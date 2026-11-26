import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.domain.catalogo import (
    AuditoriaCatalogo,
    CatalogoParametro,
    ValorParametro,
)
from app.repositories.catalogo_repository import CatalogoRepository


class CatalogoService:
    def __init__(self, repositorio: CatalogoRepository):
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

    def _registrar_auditoria(
        self,
        catalogo_codigo: str,
        registro_id: int,
        accion: str,
        responsable_id: int,
        trace_id: str,
        antes: dict | None,
        despues: dict | None,
        motivo: str | None = None,
    ) -> None:
        auditoria = AuditoriaCatalogo(
            catalogo_codigo=catalogo_codigo,
            registro_id=registro_id,
            accion=accion,
            responsable_id=responsable_id,
            trace_id=trace_id,
            antes=(
                json.dumps(antes, ensure_ascii=False)
                if antes is not None
                else None
            ),
            despues=(
                json.dumps(despues, ensure_ascii=False)
                if despues is not None
                else None
            ),
            motivo=motivo,
        )
        self.repositorio.agregar_auditoria(auditoria)

    def _obtener_catalogo(self, codigo: str) -> CatalogoParametro:
        catalogo = self.repositorio.obtener_catalogo(codigo.strip().upper())

        if catalogo is None:
            raise self._error(
                "PARAMETER_NOT_FOUND",
                "No se encontró el catálogo solicitado.",
                status.HTTP_404_NOT_FOUND,
            )

        return catalogo

    def _foto_catalogo(self, catalogo: CatalogoParametro) -> dict:
        return {
            "id": catalogo.id,
            "codigo": catalogo.codigo,
            "nombre": catalogo.nombre,
            "descripcion": catalogo.descripcion,
            "activo": catalogo.activo,
            "version": catalogo.version,
        }

    def _foto_valor(self, valor: ValorParametro) -> dict:
        return {
            "id": valor.id,
            "codigo": valor.codigo,
            "nombre": valor.nombre,
            "orden": valor.orden,
            "activo": valor.activo,
            "version": valor.version,
        }

    def listar_catalogos(self) -> list[CatalogoParametro]:
        return self.repositorio.listar_catalogos()

    def crear_catalogo(
        self,
        datos: dict,
        responsable_id: int,
    ) -> tuple[CatalogoParametro, str]:
        codigo = datos["codigo"].strip().upper()

        if self.repositorio.obtener_catalogo(codigo):
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe un catálogo con ese código.",
                status.HTTP_409_CONFLICT,
            )

        catalogo = CatalogoParametro(
            codigo=codigo,
            nombre=datos["nombre"].strip(),
            descripcion=datos.get("descripcion"),
            creado_por=responsable_id,
        )
        trace_id = str(uuid4())

        try:
            self.repositorio.agregar_catalogo(catalogo)
            self._registrar_auditoria(
                catalogo_codigo=codigo,
                registro_id=catalogo.id,
                accion="CREAR",
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=None,
                despues=self._foto_catalogo(catalogo),
            )
            self.repositorio.guardar()
            return catalogo, trace_id

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ya existe un catálogo con ese código.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise

    def actualizar_catalogo(
        self,
        codigo: str,
        datos: dict,
        responsable_id: int,
    ) -> tuple[CatalogoParametro, str]:
        catalogo = self._obtener_catalogo(codigo)

        if catalogo.version != datos["version"]:
            raise self._error(
                "STALE_VERSION",
                "El catálogo cambió. Consulta su versión actual antes de editarlo.",
                status.HTTP_409_CONFLICT,
            )

        antes = self._foto_catalogo(catalogo)
        version = datos["version"]
        trace_id = str(uuid4())

        cambios = {
            "nombre": datos["nombre"].strip(),
            "descripcion": datos.get("descripcion"),
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
            "version": version + 1,
        }

        try:
            actualizado = (
                self.repositorio.actualizar_catalogo_si_version_coincide(
                    catalogo_id=catalogo.id,
                    version=version,
                    cambios=cambios,
                )
            )

            if not actualizado:
                self.repositorio.deshacer()
                raise self._error(
                    "STALE_VERSION",
                    "El catálogo cambió. Consulta su versión actual antes de editarlo.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            catalogo_actualizado = self._obtener_catalogo(codigo)

            self._registrar_auditoria(
                catalogo_codigo=catalogo.codigo,
                registro_id=catalogo.id,
                accion="MODIFICAR",
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=antes,
                despues=self._foto_catalogo(catalogo_actualizado),
            )

            self.repositorio.guardar()
            return catalogo_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer()
            raise

    def cambiar_estado_catalogo(
        self,
        codigo: str,
        datos: dict,
        responsable_id: int,
    ) -> tuple[CatalogoParametro, str]:
        catalogo = self._obtener_catalogo(codigo)

        if catalogo.version != datos["version"]:
            raise self._error(
                "STALE_VERSION",
                "El catálogo cambió. Consulta su versión actual antes de continuar.",
                status.HTTP_409_CONFLICT,
            )

        antes = self._foto_catalogo(catalogo)
        version = datos["version"]
        trace_id = str(uuid4())

        cambios = {
            "activo": datos["activo"],
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
            "version": version + 1,
        }

        try:
            actualizado = (
                self.repositorio.actualizar_catalogo_si_version_coincide(
                    catalogo_id=catalogo.id,
                    version=version,
                    cambios=cambios,
                )
            )

            if not actualizado:
                self.repositorio.deshacer()
                raise self._error(
                    "STALE_VERSION",
                    "El catálogo cambió. Consulta su versión actual antes de continuar.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            catalogo_actualizado = self._obtener_catalogo(codigo)

            despues = self._foto_catalogo(catalogo_actualizado)
            despues["motivo"] = datos["motivo"]

            self._registrar_auditoria(
                catalogo_codigo=catalogo.codigo,
                registro_id=catalogo.id,
                accion=(
                    "ACTIVAR"
                    if datos["activo"]
                    else "INACTIVAR"
                ),
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=antes,
                despues=despues,
                motivo=datos["motivo"],
            )

            self.repositorio.guardar()
            return catalogo_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer()
            raise

    def listar_valores(
        self,
        codigo: str,
        buscar: str | None,
        activo: bool | None,
        page: int,
        page_size: int,
    ):
        if page < 1 or page_size < 1 or page_size > 100:
            raise self._error(
                "BAD_REQUEST",
                "La página debe ser mayor que cero y page_size debe estar entre 1 y 100.",
                status.HTTP_400_BAD_REQUEST,
            )

        catalogo = self._obtener_catalogo(codigo)
        valores, total = self.repositorio.listar_valores(
            catalogo.id,
            buscar,
            activo,
            page,
            page_size,
        )
        return catalogo, valores, total

    def crear_valor(
        self,
        codigo: str,
        datos: dict,
        responsable_id: int,
    ) -> tuple[ValorParametro, str]:
        catalogo = self._obtener_catalogo(codigo)

        if not catalogo.activo:
            raise self._error(
                "CATALOG_INACTIVE",
                "No se pueden agregar opciones a un catálogo inactivo.",
                status.HTTP_409_CONFLICT,
            )

        codigo_valor = datos["codigo"].strip().upper()

        if self.repositorio.existe_codigo_valor(
            catalogo.id,
            codigo_valor,
        ):
            raise self._error(
                "DUPLICATE_CODE",
                "Ese código ya existe dentro del catálogo.",
                status.HTTP_409_CONFLICT,
            )

        valor = ValorParametro(
            catalogo_id=catalogo.id,
            codigo=codigo_valor,
            nombre=datos["nombre"].strip(),
            orden=datos["orden"],
            creado_por=responsable_id,
        )
        trace_id = str(uuid4())

        try:
            self.repositorio.agregar_valor(valor)
            self._registrar_auditoria(
                catalogo_codigo=catalogo.codigo,
                registro_id=valor.id,
                accion="CREAR",
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=None,
                despues=self._foto_valor(valor),
            )
            self.repositorio.guardar()
            return valor, trace_id

        except IntegrityError as error:
            self.repositorio.deshacer()
            raise self._error(
                "DUPLICATE_CODE",
                "Ese código ya existe dentro del catálogo.",
                status.HTTP_409_CONFLICT,
            ) from error

        except Exception:
            self.repositorio.deshacer()
            raise
    def actualizar_valor(
        self,
        codigo: str,
        valor_id: int,
        datos: dict,
        responsable_id: int,
    ) -> tuple[ValorParametro, str]:
        catalogo = self._obtener_catalogo(codigo)
        valor = self.repositorio.obtener_valor(catalogo.id, valor_id)

        if valor is None:
            raise self._error(
                "PARAMETER_NOT_FOUND",
                "No se encontró la opción solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        version = datos["version"]

        if valor.version != version:
            raise self._error(
                "STALE_VERSION",
                "La opción cambió. Consulta su versión actual antes de editarla.",
                status.HTTP_409_CONFLICT,
            )

        antes = self._foto_valor(valor)
        trace_id = str(uuid4())

        cambios = {
            "nombre": datos["nombre"].strip(),
            "orden": datos["orden"],
            "version": version + 1,
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
        }

        try:
            actualizado = (
                self.repositorio.actualizar_valor_si_version_coincide(
                    valor_id=valor_id,
                    version=version,
                    cambios=cambios,
                )
            )

            if not actualizado:
                self.repositorio.deshacer()
                raise self._error(
                    "STALE_VERSION",
                    "La opción cambió. Consulta su versión actual antes de editarla.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            valor_actualizado = self.repositorio.obtener_valor(
                catalogo.id,
                valor_id,
            )

            self._registrar_auditoria(
                catalogo_codigo=catalogo.codigo,
                registro_id=valor_id,
                accion="MODIFICAR",
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=antes,
                despues=self._foto_valor(valor_actualizado),
            )

            self.repositorio.guardar()
            return valor_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer()
            raise
    def cambiar_estado_valor(
        self,
        codigo: str,
        valor_id: int,
        datos: dict,
        responsable_id: int,
    ) -> tuple[ValorParametro, str]:
        catalogo = self._obtener_catalogo(codigo)
        valor = self.repositorio.obtener_valor(catalogo.id, valor_id)

        if valor is None:
            raise self._error(
                "PARAMETER_NOT_FOUND",
                "No se encontró la opción solicitada.",
                status.HTTP_404_NOT_FOUND,
            )

        version = datos["version"]

        if valor.version != version:
            raise self._error(
                "STALE_VERSION",
                "La opción cambió. Consulta su versión actual antes de continuar.",
                status.HTTP_409_CONFLICT,
            )
        antes = self._foto_valor(valor)
        trace_id = str(uuid4())
        if (
            datos["activo"] is False
            and self.repositorio.tiene_dependencias_activas(valor_id)
        ):
            raise self._error(
                "PARAMETER_IN_USE",
                "La opción está siendo utilizada y no se puede inactivar.",
                status.HTTP_409_CONFLICT,
            )

        cambios = {
            "activo": datos["activo"],
            "version": version + 1,
            "actualizado_en": datetime.now(timezone.utc),
            "actualizado_por": responsable_id,
        }

        try:
            actualizado = (
                self.repositorio.actualizar_valor_si_version_coincide(
                    valor_id=valor_id,
                    version=version,
                    cambios=cambios,
                )
            )

            if not actualizado:
                self.repositorio.deshacer()
                raise self._error(
                    "STALE_VERSION",
                    "La opción cambió. Consulta su versión actual antes de continuar.",
                    status.HTTP_409_CONFLICT,
                )

            self.repositorio.db.expire_all()
            valor_actualizado = self.repositorio.obtener_valor(
                catalogo.id,
                valor_id,
            )

            despues = self._foto_valor(valor_actualizado)
            despues["motivo"] = datos["motivo"]

            self._registrar_auditoria(
                catalogo_codigo=catalogo.codigo,
                registro_id=valor_id,
                accion="ACTIVAR" if datos["activo"] else "INACTIVAR",
                responsable_id=responsable_id,
                trace_id=trace_id,
                antes=antes,
                despues=despues,
                motivo=datos["motivo"],
            )

            self.repositorio.guardar()
            return valor_actualizado, trace_id

        except Exception:
            self.repositorio.deshacer()
            raise