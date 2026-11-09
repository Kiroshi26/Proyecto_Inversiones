import sys
import traceback

from src.configuracion import (
    cargar_configuracion,
    validar_carpetas,
)
from src.credenciales import (
    solicitar_credenciales,
)
from src.insumos import (
    cargar_insumos,
)
from src.logger import (
    configurar_logger,
)
from src.parametros import (
    obtener_periodo_desde_f351,
)
from src.proceso_inversiones import (
    ejecutar_proceso_inversiones,
)
from src.version import (
    NOMBRE,
    VERSION,
)


def mostrar_resultado(resultado):
    print()
    print("=" * 70)
    print("PROCESO FINALIZADO EXITOSAMENTE")
    print("=" * 70)
    print(
        f"Archivo generado          : "
        f"{resultado.ruta_archivo}"
    )
    print(
        f"Registros en SALDOS       : "
        f"{resultado.cantidad_saldos:,}"
    )
    print(
        f"Registros en BASENEG      : "
        f"{resultado.cantidad_baseneg:,}"
    )
    print(
        f"Total Saldo Contable      : "
        f"${resultado.total_saldo_contable:,.2f}"
    )
    print(
        f"Total Saldo F351          : "
        f"${resultado.total_saldo_f351:,.2f}"
    )
    print(
        f"Total Diferencias         : "
        f"${resultado.total_diferencias:,.2f}"
    )
    print(
        f"Partidas con diferencia   : "
        f"{resultado.registros_con_diferencia:,}"
    )
    print("=" * 70)
    print()


def main():
    logger = None

    try:
        print()
        print("=" * 70)
        print(f" {NOMBRE} - v{VERSION}")
        print("=" * 70)

        # 1. Configuración y carpetas
        configuracion = cargar_configuracion()
        rutas = validar_carpetas(configuracion)

        # 2. Logger
        logger = configurar_logger(
            rutas["logs"]
        )

        logger.info(
            "Inicio del proceso de conciliacion de inversiones."
        )

        # 3. Carga de insumos
        print()
        print(
            "Cargando archivos de insumos "
            "desde carpeta 'insumos'..."
        )

        insumos = cargar_insumos(
            configuracion
        )

        logger.info(
            "Base de negocios cargada: %d registros.",
            len(insumos.base_negocios),
        )

        logger.info(
            "Formato 351 cargado y agregado: %d registros.",
            len(insumos.formato_351),
        )

        print(
            f"-> Base de Negocios Fiduciarios : "
            f"{len(insumos.base_negocios):,} registros."
        )

        print(
            f"-> Formato 351 (22 subcuentas)  : "
            f"{len(insumos.formato_351):,} registros."
        )

        # 4. Periodo automático desde F351
        parametros = (
            obtener_periodo_desde_f351(
                insumos.ruta_f351
            )
        )

        print()
        print(
            f"Periodo detectado "
            f"automaticamente: "
            f"{parametros.periodo}"
        )

        logger.info(
            "Periodo detectado: %s "
            "(Fecha corte: %s)",
            parametros.periodo,
            parametros.fecha_corte,
        )

        # 5. Credenciales Nacional
        print()
        print(
            "Autenticación en "
            "Óptima (Nacional)..."
        )

        usuario, clave = (
            solicitar_credenciales()
        )

        # 6. Proceso principal
        print()
        print(
            f"Consultando Óptima y "
            f"ejecutando conciliación para "
            f"{parametros.periodo}..."
        )

        resultado = (
            ejecutar_proceso_inversiones(
                configuracion=configuracion,
                parametros=parametros,
                insumos=insumos,
                usuario=usuario,
                clave=clave,
            )
        )

        logger.info(
            "Proceso completado exitosamente. "
            "Archivo: %s",
            resultado.ruta_archivo,
        )

        mostrar_resultado(
            resultado
        )

        return 0

    except KeyboardInterrupt:

        print(
            "\nProceso cancelado por el usuario."
        )

        return 1

    except Exception as error:

        if logger is not None:
            logger.exception(
                "Error durante la ejecucion del proceso."
            )

        print()
        print("=" * 70)
        print("ERROR EN EL PROCESO")
        print("=" * 70)
        print(
            f"{type(error).__name__}: "
            f"{error}\n"
        )

        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())