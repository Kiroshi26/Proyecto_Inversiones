import sys
import traceback
from pathlib import Path

from src.configuracion import cargar_configuracion, validar_carpetas
from src.credenciales import solicitar_credenciales
from src.insumos import cargar_insumos
from src.logger import configurar_logger
from src.parametros import crear_parametros
from src.proceso_inversiones import ejecutar_proceso_inversiones
from src.version import NOMBRE, VERSION


def solicitar_periodo():
    print()
    print("=" * 70)
    print("PERIODO DE CONCILIACION")
    print("=" * 70)
    while True:
        try:
            anio_input = input("Año (ej. 2026): ").strip()
            anio = int(anio_input)
            mes_input = input("Mes (1-12): ").strip()
            mes = int(mes_input)
            parametros = crear_parametros(anio=anio, mes=mes)
            return parametros
        except Exception as err:
            print(f"Entrada no valida: {err}. Intente nuevamente.\n")


def mostrar_resultado(resultado):
    print()
    print("=" * 70)
    print("PROCESO FINALIZADO EXITOSAMENTE")
    print("=" * 70)
    print(f"Archivo generado          : {resultado.ruta_archivo}")
    print(f"Registros en SALDOS       : {resultado.cantidad_saldos:,}")
    print(f"Registros en BASENEG      : {resultado.cantidad_baseneg:,}")
    print(f"Total Saldo Contable      : ${resultado.total_saldo_contable:,.2f}")
    print(f"Total Saldo F351          : ${resultado.total_saldo_f351:,.2f}")
    print(f"Total Diferencias         : ${resultado.total_diferencias:,.2f}")
    print(f"Partidas con diferencia   : {resultado.registros_con_diferencia:,}")
    print("=" * 70)
    print()


def main():
    logger = None
    try:
        print()
        print("=" * 70)
        print(f" {NOMBRE} - v{VERSION}")
        print("=" * 70)

        # 1. Periodo a conciliar
        parametros = solicitar_periodo()

        # 2. Configuracion y carpetas
        configuracion = cargar_configuracion()
        rutas = validar_carpetas(configuracion)

        # 3. Logger
        logger = configurar_logger(rutas["logs"])
        logger.info("Inicio del proceso de conciliacion de inversiones.")
        logger.info("Periodo seleccionado: %s (Fecha corte: %s)", parametros.periodo, parametros.fecha_corte)

        # 4. Carga de Insumos (BASE_NEGOCIOS_FIDUCIARIOS y Formato 351)
        print()
        print("Cargando archivos de insumos desde carpeta 'insumos'...")
        insumos = cargar_insumos(configuracion)

        logger.info("Base de negocios cargada: %d registros.", len(insumos.base_negocios))
        logger.info("Formato 351 cargado y agregado: %d registros.", len(insumos.formato_351))
        print(f"-> Base de Negocios Fiduciarios : {len(insumos.base_negocios):,} registros.")
        print(f"-> Formato 351 (22 subcuentas)   : {len(insumos.formato_351):,} registros.")

        # 5. Credenciales Optima / Nacional
        print()
        print("Autenticación en Óptima (Nacional)...")
        usuario, clave = solicitar_credenciales()

        # 6. Proceso principal
        print()
        print(f"Consultando Óptima y ejecutando conciliación para {parametros.periodo}...")
        resultado = ejecutar_proceso_inversiones(
            configuracion=configuracion,
            parametros=parametros,
            insumos=insumos,
            usuario=usuario,
            clave=clave,
        )

        logger.info("Proceso completado exitosamente. Archivo: %s", resultado.ruta_archivo)
        mostrar_resultado(resultado)
        return 0

    except KeyboardInterrupt:
        print("\nProceso cancelado por el usuario.")
        return 1
    except Exception as error:
        if logger is not None:
            logger.exception("Error durante la ejecucion del proceso.")
        print()
        print("=" * 70)
        print("ERROR EN EL PROCESO")
        print("=" * 70)
        print(f"{type(error).__name__}: {error}\n")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
