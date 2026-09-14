import traceback

from src.configuracion import (
    cargar_configuracion,
    validar_carpetas,
    validar_configuracion_red,
    validar_modo_seguro,
)

from src.credenciales import (
    solicitar_credenciales,
)

from src.insumos import (
    cargar_insumos,
)

from src.insumos_red import (
    preparar_insumos_desde_red,
)

from src.logger import (
    configurar_logger,
)

from src.parametros import (
    crear_parametros,
)

from src.procesamiento import (
    preparar_insumos,
)

from src.proceso_inversiones import (
    ejecutar_proceso_inversiones,
)

from src.version import (
    VERSION,
    NOMBRE,
)


def solicitar_periodo():

    print()
    print("=" * 70)
    print("PERIODO DE PROCESO")
    print("=" * 70)

    anio = int(input("Año: "))

    mes = int(input("Mes (1-12): "))

    return anio, mes


def mostrar_resultado(resultado):

    print()
    print("=" * 70)
    print("PROCESO FINALIZADO CORRECTAMENTE")
    print("=" * 70)

    print()

    print(f"Archivo generado : " f"{resultado.ruta_archivo}")

    print(f"Registros SALDOS : " f"{resultado.cantidad_saldos:,}")

    print(f"Registros BASENEG : " f"{resultado.cantidad_baseneg:,}")

    print(f"TOTAL MES : " f"{resultado.total_mes:,.2f}")

    print()
    print("=" * 70)


def main():

    logger = None

    try:

        print()
        print("=" * 70)
        print(NOMBRE)
        print(f"VERSION {VERSION}")
        print("=" * 70)

        #
        # Periodo
        #
        anio, mes = solicitar_periodo()

        parametros = crear_parametros(
            anio=anio,
            mes=mes,
        )

        #
        # Configuración
        #
        configuracion = cargar_configuracion()

        validar_modo_seguro(configuracion)

        rutas_locales = validar_carpetas(configuracion)

        rutas_red = validar_configuracion_red(configuracion)

        #
        # Log
        #
        logger = configurar_logger(rutas_locales["logs"])

        logger.info("Inicio proceso.")

        logger.info(
            "Periodo: %s",
            parametros.periodo,
        )

        #
        # Copia insumos corporativos
        #
        print()
        print("Copiando insumos...")

        ejecucion = preparar_insumos_desde_red(
            configuracion=configuracion,
            rutas_red=rutas_red,
            carpeta_ejecuciones=(rutas_locales["ejecuciones"]),
            fecha_corte=(parametros.fecha_corte),
        )

        logger.info(
            "Carpeta ejecución: %s",
            ejecucion.carpeta_ejecucion,
        )

        print("Insumos copiados correctamente.")

        #
        # Lectura insumos
        #
        print()
        print("Leyendo insumos...")

        rutas_descargadas = {
            "formato_351": ejecucion.formato_351.ruta_destino,
            "mapas_contables": ejecucion.mapas_contables.ruta_destino,
            "mapas_centros_costos": ejecucion.mapas_centros_costos.ruta_destino,
        }

        insumos = cargar_insumos(configuracion, rutas_descargadas)

        resultado_preparacion = preparar_insumos(insumos)

        logger.info(
            "Base negocios: %s registros",
            len(resultado_preparacion.base_negocios),
        )

        logger.info(
            "Formato 351: %s registros",
            len(resultado_preparacion.formato_351),
        )

        #
        # Credenciales Nacional
        #
        usuario, clave = solicitar_credenciales()

        #
        # Proceso principal
        #
        print()
        print("Consultando Nacional...")

        resultado = ejecutar_proceso_inversiones(
            configuracion=configuracion,
            parametros=parametros,
            resultado_preparacion=(resultado_preparacion),
            usuario=usuario,
            clave=clave,
        )

        logger.info(
            "Archivo generado: %s",
            resultado.ruta_archivo,
        )

        mostrar_resultado(resultado)

        return 0

    except Exception as error:

        if logger is not None:

            logger.exception("Error del proceso.")

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print()

        print(f"{type(error).__name__}: " f"{error}")

        print()
        traceback.print_exc()

        return 1


if __name__ == "__main__":

    raise SystemExit(main())
