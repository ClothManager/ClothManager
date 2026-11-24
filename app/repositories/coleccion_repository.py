import re

from sqlalchemy import func, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.domain.coleccion import Coleccion, SecuenciaColeccion
from app.domain.usuario import Auditoria, Rol, UsuarioRol


class ColeccionRepository:
    def __init__(self, db: Session):
        self.db = db

    def es_administrador(self, usuario_id: int) -> bool:
        return (
            self.db.query(UsuarioRol)
            .join(Rol, Rol.id == UsuarioRol.rol_id)
            .filter(
                UsuarioRol.usuario_id == usuario_id,
                Rol.codigo == "ADMINISTRADOR",
                Rol.activo.is_(True),
            )
            .first()
            is not None
        )

    def existe_codigo(self, codigo: str) -> bool:
        return (
            self.db.query(Coleccion.id)
            .filter(func.lower(Coleccion.codigo) == codigo.lower())
            .first()
            is not None
        )

    def obtener_mayor_numero_codigo(self, anio: int) -> int:
        codigos = (
            self.db.query(Coleccion.codigo)
            .filter(Coleccion.anio == anio)
            .all()
        )

        patron = re.compile(rf"^COL(\d+)-{anio}$")
        numeros = []

        for (codigo,) in codigos:
            coincidencia = patron.fullmatch(codigo)
            if coincidencia:
                numeros.append(int(coincidencia.group(1)))

        return max(numeros, default=0)

    def generar_codigo_coleccion(self, anio: int) -> str:
        mayor_existente = self.obtener_mayor_numero_codigo(anio)

        instruccion = sqlite_insert(SecuenciaColeccion).values(
            anio=anio,
            ultimo_numero=mayor_existente + 1,
        )

        instruccion = instruccion.on_conflict_do_update(
            index_elements=[SecuenciaColeccion.anio],
            set_={
                "ultimo_numero": func.max(
                    SecuenciaColeccion.ultimo_numero,
                    mayor_existente,
                ) + 1
            },
        ).returning(SecuenciaColeccion.ultimo_numero)

        numero = self.db.execute(instruccion).scalar_one()
        return f"COL{numero:02d}-{anio}"

    def agregar(self, coleccion: Coleccion) -> Coleccion:
        self.db.add(coleccion)
        self.db.flush()
        return coleccion

    def listar(
        self,
        buscar: str | None,
        anio: int | None,
        estado: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Coleccion], int]:
        consulta = self.db.query(Coleccion)

        if buscar:
            termino = f"%{buscar.strip()}%"
            consulta = consulta.filter(
                or_(
                    Coleccion.codigo.ilike(termino),
                    Coleccion.nombre.ilike(termino),
                )
            )

        if anio is not None:
            consulta = consulta.filter(Coleccion.anio == anio)

        if estado:
            consulta = consulta.filter(Coleccion.estado == estado.upper())

        total = consulta.count()
        colecciones = (
            consulta
            .order_by(Coleccion.anio.desc(), Coleccion.codigo)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return colecciones, total

    def obtener_por_id(self, coleccion_id: int) -> Coleccion | None:
        return self.db.get(Coleccion, coleccion_id)

    def actualizar_si_version_coincide(
        self,
        coleccion_id: int,
        version: int,
        cambios: dict,
    ) -> bool:
        filas_actualizadas = (
            self.db.query(Coleccion)
            .filter(
                Coleccion.id == coleccion_id,
                Coleccion.version == version,
            )
            .update(cambios, synchronize_session=False)
        )
        return filas_actualizadas == 1

    def registrar_auditoria(
        self,
        usuario_objetivo_id: int,
        responsable_id: int,
        accion: str,
        antes: str | None,
        despues: str,
    ) -> None:
        self.db.add(
            Auditoria(
                usuario_objetivo_id=usuario_objetivo_id,
                responsable_id=responsable_id,
                accion=accion,
                antes=antes,
                despues=despues,
                resultado="EXITOSO",
            )
        )
        self.db.flush()

    def guardar(self) -> None:
        self.db.commit()

    def deshacer(self) -> None:
        self.db.rollback()