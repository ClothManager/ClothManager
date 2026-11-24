from app.domain.catalogo import CatalogoParametro, ValorParametro


CATALOGOS_BASE = {
    "TIPO_PRENDA": (
        "Tipo de prenda",
        [
            ("PANTALONES", "Pantalones"),
            ("BLUSAS", "Blusas"),
            ("TOPS", "Tops"),
            ("SHORTS", "Shorts"),
            ("FALDAS", "Faldas"),
            ("ENTERIZOS", "Enterizos"),
            ("SETS", "Sets"),
            ("VESTIDOS", "Vestidos"),
        ],
    ),
    "ETAPA_PRODUCCION": (
        "Etapa de producción",
        [
            ("PLANEACION", "Planeación"),
            ("DISENO", "Diseño"),
            ("TRAZO", "Trazo"),
            ("CORTE", "Corte"),
            ("FUSIONADO", "Fusionado"),
            ("ENSAMBLE", "Ensamble"),
            ("REVISION_CALIDAD", "Revisión de calidad"),
            ("PLANCHA", "Plancha"),
            ("EMPAQUE", "Empaque"),
            ("BODEGA", "Bodega"),
        ],
    ),
    "TIPO_INSUMO": (
        "Tipo de insumo",
        [
            ("HILOS", "Hilos"),
            ("BOTONES", "Botones"),
            ("CIERRES", "Cierres"),
            ("TELAS", "Telas"),
            ("HILAZAS", "Hilazas"),
        ],
    ),
    "MOTIVO_MOVIMIENTO_BODEGA": (
        "Motivo de movimiento de bodega",
        [
            ("VENTA_WHATSAPP", "Venta de WhatsApp"),
            ("VENTA_WEB", "Venta web"),
            ("VENTA_MAYORISTA", "Venta mayorista"),
            ("AJUSTE_PRENDA", "Ajuste de prenda"),
        ],
    ),
    "TIPO_PERSONA": (
        "Tipo de persona",
        [
            ("NATURAL", "Natural"),
            ("JURIDICA", "Jurídica"),
        ],
    ),
    "TIPO_DOCUMENTO": (
        "Tipo de documento",
        [
            ("CC", "Cédula de ciudadanía"),
            ("PASAPORTE", "Pasaporte"),
            ("NIT", "NIT"),
        ],
    ),
    "MONEDA": (
        "Moneda",
        [
            ("COP", "Pesos colombianos"),
            ("USD", "Dólares estadounidenses"),
        ],
    ),
    "UNIDAD_MEDIDA": (
        "Unidad de medida",
        [
            ("CENTIMETRO", "Centímetro (cm)"),
        ],
    ),
        "TIPO_CLIENTE_MAYORISTA": (
        "Tipo de cliente mayorista",
        [
            ("NACIONAL", "Nacional"),
            ("EXPORTACION", "Exportación"),
        ],
    ),
    "CANAL_VENTA": (
        "Canal de venta",
        [
            ("WOOCOMMERCE", "WooCommerce"),
            ("WHATSAPP", "WhatsApp"),
            ("POS", "Punto de venta"),
            ("MAYORISTA", "Mayorista"),
        ],
    ),
}


def sembrar_catalogos_base(db) -> None:
    for codigo_catalogo, (nombre_catalogo, valores) in CATALOGOS_BASE.items():
        catalogo = (
            db.query(CatalogoParametro)
            .filter_by(codigo=codigo_catalogo)
            .first()
        )

        if catalogo is None:
            catalogo = CatalogoParametro(
                codigo=codigo_catalogo,
                nombre=nombre_catalogo,
                activo=True,
                version=1,
            )
            db.add(catalogo)
            db.flush()

        for orden, (codigo_valor, nombre_valor) in enumerate(valores, start=1):
            valor_existente = (
                db.query(ValorParametro)
                .filter_by(
                    catalogo_id=catalogo.id,
                    codigo=codigo_valor,
                )
                .first()
            )

            if valor_existente is None:
                db.add(
                    ValorParametro(
                        catalogo_id=catalogo.id,
                        codigo=codigo_valor,
                        nombre=nombre_valor,
                        orden=orden,
                        activo=True,
                        version=1,
                    )
                )