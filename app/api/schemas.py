import re
from typing import Literal
from datetime import date, datetime
from decimal import Decimal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
)


AREAS_VALIDAS = {
    "ADMINISTRACION",
    "PRODUCCION",
    "BODEGA",
    "VENTAS",
    "CONTABILIDAD",
}

ESTADOS_VALIDOS = {"ACTIVO", "INACTIVO"}

TALLAS_VALIDAS_PLAN = {"S", "M", "L", "XL", "XXL"}
MAX_CANTIDAD_PLAN = 1_000_000


class DatosUsuario(BaseModel):
    nombres: str = Field(min_length=1, max_length=80)
    apellidos: str = Field(min_length=1, max_length=80)
    correo: str = Field(min_length=5, max_length=254)
    nombre_usuario: str = Field(min_length=1, max_length=50)
    area: str

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, valor: str) -> str:
        valor = valor.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El correo debe tener un formato válido")
        return valor

    @field_validator("nombre_usuario")
    @classmethod
    def normalizar_nombre_usuario(cls, valor: str) -> str:
        valor = valor.strip().lower()
        if not valor:
            raise ValueError("El nombre de usuario no puede estar vacío")
        return valor

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_nombres(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Este campo no puede estar vacío")
        return valor

    @field_validator("area")
    @classmethod
    def validar_area(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in AREAS_VALIDAS:
            raise ValueError("El área indicada no está permitida")
        return valor


class UsuarioCrear(DatosUsuario):
    roles: list[str] = Field(default_factory=list)
    estado: str = "ACTIVO"

    @field_validator("roles")
    @classmethod
    def normalizar_roles(cls, valores: list[str]) -> list[str]:
        return [valor.strip().upper() for valor in valores]

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in ESTADOS_VALIDOS:
            raise ValueError("El estado debe ser ACTIVO o INACTIVO")
        return valor


class UsuarioActualizar(BaseModel):
    nombres: str | None = Field(default=None, min_length=1, max_length=80)
    apellidos: str | None = Field(default=None, min_length=1, max_length=80)
    correo: str | None = Field(default=None, min_length=5, max_length=254)
    nombre_usuario: str | None = Field(default=None, min_length=1, max_length=50)
    area: str | None = None
    estado: str | None = None

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        valor = valor.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El correo debe tener un formato válido")
        return valor

    @field_validator("nombre_usuario")
    @classmethod
    def normalizar_nombre_usuario(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip().lower()
        if not valor:
            raise ValueError("El nombre de usuario no puede estar vacío")
        return valor

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_nombres_actualizados(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()
        if not valor:
            raise ValueError("Este campo no puede estar vacío")
        return valor

    @field_validator("area")
    @classmethod
    def validar_area_actualizada(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        valor = valor.strip().upper()
        if valor not in AREAS_VALIDAS:
            raise ValueError("El área indicada no está permitida")
        return valor

    @field_validator("estado")
    @classmethod
    def validar_estado_actualizado(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip().upper()
        if valor not in ESTADOS_VALIDOS:
            raise ValueError("El estado debe ser ACTIVO o INACTIVO")
        return valor


class RolResumen(BaseModel):
    codigo: str
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioRespuesta(BaseModel):
    id: int
    nombres: str
    apellidos: str
    correo: str
    nombre_usuario: str
    area: str
    estado: str
    creado_en: datetime | None = None
    roles: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RolCrear(BaseModel):
    codigo: str = Field(min_length=2, max_length=40)
    nombre: str = Field(min_length=1, max_length=80)
    descripcion: str | None = Field(default=None, max_length=250)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_rol(cls, valor: str) -> str:
        return valor.strip().upper()

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_rol(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre del rol no puede estar vacío")
        return valor


class RolActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    descripcion: str | None = Field(default=None, max_length=250)
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_actualizado(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre del rol no puede estar vacío")
        return valor


class RolesActualizar(BaseModel):
    roles: list[str]

    @field_validator("roles")
    @classmethod
    def normalizar_roles(cls, valores: list[str]) -> list[str]:
        return [valor.strip().upper() for valor in valores]


class PermisoEntrada(BaseModel):
    modulo: str = Field(min_length=1, max_length=30)
    recurso: str = Field(min_length=1, max_length=50)
    accion: str = Field(min_length=1, max_length=30)

    @field_validator("modulo", "recurso", "accion")
    @classmethod
    def normalizar_codigo_permiso(cls, valor: str) -> str:
        return valor.strip().upper()


class PermisosRolActualizar(BaseModel):
    permisos: list[PermisoEntrada]


class PermisoRespuesta(PermisoEntrada):
    id: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class RolRespuesta(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    activo: bool
    permisos: list[PermisoRespuesta] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ActivarCredenciales(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    contrasena: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    identificador: str = Field(min_length=1, max_length=254)
    contrasena: str = Field(min_length=1, max_length=128)


class RenovarSesionRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class CambiarContrasenaRequest(BaseModel):
    contrasena_actual: str = Field(min_length=1, max_length=128)
    contrasena_nueva: str = Field(min_length=12, max_length=128)


class SolicitarRecuperacionRequest(BaseModel):
    correo: str = Field(min_length=5, max_length=254)

    @field_validator("correo")
    @classmethod
    def validar_correo_recuperacion(cls, valor: str) -> str:
        valor = valor.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El correo debe tener un formato válido")
        return valor


class ConfirmarRecuperacionRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    contrasena_nueva: str = Field(min_length=12, max_length=128)


class TokenRespuesta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    usuario_id: int
    nombre_usuario: str


class ColorCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_color(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ColorActualizar(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    version: int = Field(ge=1)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_color_actualizado(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ColorRespuesta(BaseModel):
    id: int
    codigo: str
    nombre: str
    activo: bool
    version: int

    model_config = ConfigDict(from_attributes=True)


class TallaRespuesta(BaseModel):
    id: int
    codigo: str
    nombre: str
    orden: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class ColorEstadoActualizar(BaseModel):
    activo: bool
    version: int = Field(ge=1)
    motivo: str = Field(min_length=5, max_length=250)

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El motivo no puede estar vacío")
        return valor


class CatalogoCrear(BaseModel):
    codigo: str = Field(min_length=2, max_length=40)
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=250)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_catalogo(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("El código no puede estar vacío")
        return valor

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_catalogo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class CatalogoActualizar(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=250)
    version: int = Field(ge=1)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_catalogo_actualizado(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class CatalogoEstadoActualizar(BaseModel):
    activo: bool
    version: int = Field(ge=1)
    motivo: str = Field(min_length=5, max_length=250)

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo_catalogo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El motivo no puede estar vacío")
        return valor


class ValorParametroCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = Field(default=1, ge=1)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_valor(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("El código no puede estar vacío")
        return valor

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_valor(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ValorParametroActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = Field(ge=1)
    version: int = Field(ge=1)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_valor_actualizado(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ValorParametroEstadoActualizar(BaseModel):
    activo: bool
    version: int = Field(ge=1)
    motivo: str = Field(min_length=5, max_length=250)

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo_valor(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El motivo no puede estar vacío")
        return valor


class ColeccionCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    anio: int = Field(ge=2000, le=2200)
    fecha_inicio: date
    fecha_inicio_preventa: date
    fecha_cierre_preventa: date
    fecha_entrega: date

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_coleccion(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ColeccionActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    anio: int | None = Field(default=None, ge=2000, le=2200)
    fecha_inicio: date | None = None
    fecha_inicio_preventa: date | None = None
    fecha_cierre_preventa: date | None = None
    fecha_entrega: date | None = None
    estado: str | None = None
    version: int = Field(ge=1)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_actualizado(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor

    @field_validator("estado")
    @classmethod
    def validar_estado_coleccion(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip().upper()
        if valor not in {"EN_CURSO", "COMPLETADA"}:
            raise ValueError("El estado debe ser EN_CURSO o COMPLETADA")
        return valor


class ReferenciaCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=30)
    nombre_referencia: str = Field(min_length=1, max_length=100)
    coleccion_id: int = Field(gt=0)
    color_id: int = Field(gt=0)
    categoria_id: int = Field(gt=0)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_referencia(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("El código no puede estar vacío")
        return valor

    @field_validator("nombre_referencia")
    @classmethod
    def limpiar_nombre_referencia(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre de referencia no puede estar vacío")
        return valor


class ReferenciaColorResumen(BaseModel):
    id: int
    codigo: str
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class ReferenciaColeccionResumen(BaseModel):
    id: int
    codigo: str
    nombre: str
    anio: int

    model_config = ConfigDict(from_attributes=True)


class ReferenciaCategoriaResumen(BaseModel):
    id: int
    codigo: str
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class ReferenciaRespuesta(BaseModel):
    id: int
    codigo: str
    nombre_referencia: str
    color: ReferenciaColorResumen
    coleccion: ReferenciaColeccionResumen
    anio: int
    categoria: ReferenciaCategoriaResumen
    activo: bool
    version: int

    model_config = ConfigDict(from_attributes=True)


class CantidadesTallaActualizar(BaseModel):
    cantidades_planeadas: dict[str, StrictInt] = Field(
        default_factory=dict,
        alias="cantidadesPlaneadas",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("cantidades_planeadas")
    @classmethod
    def validar_cantidades(
        cls,
        valores: dict[str, int],
    ) -> dict[str, int]:
        normalizadas: dict[str, int] = {}

        for talla, cantidad in valores.items():
            codigo_talla = talla.strip().upper()

            if codigo_talla not in TALLAS_VALIDAS_PLAN:
                raise ValueError(
                    "Solo se permiten las tallas S, M, L, XL y XXL"
                )

            if codigo_talla in normalizadas:
                raise ValueError(f"La talla {codigo_talla} está repetida")

            if cantidad < 0:
                raise ValueError("Las cantidades no pueden ser negativas")

            if cantidad > MAX_CANTIDAD_PLAN:
                raise ValueError("La cantidad supera el límite permitido")

            normalizadas[codigo_talla] = cantidad

        return normalizadas
class PreciosReferenciaActualizar(BaseModel):
    costo_produccion: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        alias="costoProduccion",
    )
    precio_detal: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        alias="precioDetal",
    )
    precio_mayorista_nacional: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        alias="precioMayoristaNacional",
    )
    precio_mayorista_exportacion: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        alias="precioMayoristaExportacion",
    )
    moneda: str = Field(
        min_length=3,
        max_length=3,
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("moneda")
    @classmethod
    def normalizar_moneda(cls, valor: str) -> str:
        valor = valor.strip().upper()

        if not re.fullmatch(r"[A-Z]{3}", valor):
            raise ValueError(
                "La moneda debe ser un código de tres letras, como COP o USD"
            )

        return valor
class InsumoCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=30)
    nombre: str = Field(min_length=1, max_length=100)
    tipo_insumo_id: int = Field(gt=0, alias="tipoInsumoId")
    unidad_medida_id: int = Field(gt=0, alias="unidadMedidaId")
    costo_referencia: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        alias="costoReferencia",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_insumo(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("El código no puede estar vacío")
        return valor

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre_insumo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class RequerimientoInsumoEntrada(BaseModel):
    insumo_id: int = Field(gt=0, alias="insumoId")
    cantidad: Decimal = Field(
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=3,
    )
    unidad_medida_id: int = Field(gt=0, alias="unidadMedidaId")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

class RequerimientosInsumoActualizar(BaseModel):
    base_calculo: Literal["POR_UNIDAD", "POR_LOTE"] = Field(
        alias="baseCalculo"
    )
    insumos: list[RequerimientoInsumoEntrada] = Field(
        default_factory=list,
        max_length=100,
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("insumos")
    @classmethod
    def validar_insumos_sin_duplicados(
        cls,
        valores: list[RequerimientoInsumoEntrada],
    ) -> list[RequerimientoInsumoEntrada]:
        ids = [item.insumo_id for item in valores]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "No se puede repetir un insumo en la misma base de cálculo"
            )

        return valores

# Alias para conservar compatibilidad con los nombres anteriores.
UsuarioCreate = UsuarioCrear
UsuarioUpdate = UsuarioActualizar
RolCreate = RolCrear
RolUpdate = RolActualizar
UsuarioRolesUpdate = RolesActualizar
RolPermisosUpdate = PermisosRolActualizar