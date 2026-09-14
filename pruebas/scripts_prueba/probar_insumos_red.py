import sys
from datetime import date
from pathlib import Path

from src.configuracion import (
    ErrorConfiguracion,
    cargar_configuracion,
    validar_carpetas,
    validar_configuracion_red,
    validar_modo_seguro,
)
from src.insumos_red import (
    ErrorInsumosRed,
    preparar_insumos_desde_red,
)

CARPETA_PROYECTO = Path(__file__).resolve().parent

RUTA_CONFIGURACION = CARPETA_PROYECTO / "config.yaml"


def mostrar_archivo(
    titulo,
    archivo,
):
    """
    Muestra la trazabilidad básica de un archivo copiado.
    """
    print()
    print(titulo)
    print("-" * 70)
    print("Nombre:", archivo.nombre)
    print("Origen:", archivo.ruta_origen)
    print("Copia local:", archivo.ruta_destino)
    print("Tamaño:", archivo.tamano_bytes, "bytes")
    print(
        "Modificación en red:",
        archivo.fecha_modificacion_origen,
    )
    print(
        "SHA-256:",
        archivo.hash_sha256,
    )


def main():
    """
    Prueba la copia controlada de insumos
    para diciembre de 2025.
    """
    try:
        print("=" * 70)
        print("PRUEBA DE INSUMOS DESDE LA RED")
        print("=" * 70)
        print()
        print("Esta prueba solo leerá archivos corporativos.")
        print("Todas las copias y resultados serán locales.")
        print("No se publicarán archivos en la red.")

        configuracion = cargar_configuracion(str(RUTA_CONFIGURACION))

        validar_modo_seguro(configuracion)

        rutas_locales = validar_carpetas(configuracion)

        rutas_red = validar_configuracion_red(configuracion)

        fecha_corte = date(
            2025,
            12,
            31,
        )

        ejecucion = preparar_insumos_desde_red(
            configuracion=configuracion,
            rutas_red=rutas_red,
            carpeta_ejecuciones=rutas_locales["ejecuciones"],
            fecha_corte=fecha_corte,
        )

        print()
        print("=" * 70)
        print("COPIA LOCAL COMPLETADA")
        print("=" * 70)
        print("Periodo:", ejecucion.periodo)
        print("Fecha de corte:", ejecucion.fecha_corte)
        print(
            "Carpeta local:",
            ejecucion.carpeta_ejecucion,
        )

        mostrar_archivo(
            "FORMATO 351",
            ejecucion.formato_351,
        )

        mostrar_archivo(
            "MAPAS CONTABLES",
            ejecucion.mapas_contables,
        )

        mostrar_archivo(
            "MAPAS CON CENTROS DE COSTOS",
            ejecucion.mapas_centros_costos,
        )

        print()
        print("=" * 70)
        print("PRUEBA TERMINADA CORRECTAMENTE")
        print("=" * 70)
        print("No se escribieron resultados " "en carpetas corporativas.")

        return 0

    except (
        ErrorConfiguracion,
        ErrorInsumosRed,
    ) as error:
        print()
        print("=" * 70)
        print("ERROR CONTROLADO")
        print("=" * 70)
        print(error)
        print("=" * 70)

        return 1

    except Exception as error:
        print()
        print("=" * 70)
        print("ERROR NO CONTROLADO")
        print("=" * 70)
        print(f"{type(error).__name__}: {error}")
        print("=" * 70)

        return 2


if __name__ == "__main__":
    raise SystemExit(main())
