from datetime import date

from src.configuracion import (
    cargar_configuracion,
    validar_carpetas,
    validar_configuracion_red,
)

from src.insumos_red import (
    preparar_insumos_desde_red,
)

print("Cargando configuración...")

config = cargar_configuracion()

print("Validando carpetas...")

rutas_locales = validar_carpetas(
    config
)

rutas_red = validar_configuracion_red(
    config
)

print("Copiando insumos desde red...")

resultado = preparar_insumos_desde_red(
    configuracion=config,
    rutas_red=rutas_red,
    carpeta_ejecuciones=rutas_locales[
        "ejecuciones"
    ],
    fecha_corte=date(
        2025,
        12,
        31,
    ),
)

print()
print("=" * 70)
print("COPIA FINALIZADA")
print("=" * 70)

print()

print(
    "Carpeta ejecución:"
)

print(
    resultado.carpeta_ejecucion
)

print()

print(
    "Formato 351:"
)

print(
    resultado.formato_351.ruta_destino
)

print()

print(
    "Mapas Contables:"
)

print(
    resultado.mapas_contables.ruta_destino
)

print()

print(
    "Centros Costos:"
)

print(
    resultado.mapas_centros_costos.ruta_destino
)

print()

print("=" * 70)
