from pathlib import Path

import pandas as pd

from src.procesamiento import ResultadoPreparacion


class ErrorSalida(Exception):
    """Error relacionado con la generación de archivos de salida."""


def generar_diagnostico_insumos(
    resultado: ResultadoPreparacion,
    carpeta_salida: Path,
    periodo: str,
) -> Path:
    """
    Genera un archivo Excel de diagnóstico con las bases preparadas.

    Este archivo se guarda únicamente en la carpeta de pruebas.
    """
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    nombre_archivo = (
        f"Diagnostico_Insumos_{periodo}_PRUEBA.xlsx"
    )

    ruta_salida = carpeta_salida / nombre_archivo

    resumen = pd.DataFrame(
        [
            {
                "Indicador": "Periodo solicitado",
                "Valor": periodo,
            },
            {
                "Indicador": "Filas antes de eliminar duplicados",
                "Valor": resultado.filas_antes_duplicados,
            },
            {
                "Indicador": "Duplicados eliminados",
                "Valor": resultado.duplicados_eliminados,
            },
            {
                "Indicador": "Base consolidada de negocios",
                "Valor": len(resultado.base_negocios),
            },
            {
                "Indicador": "Cuentas de transmisión",
                "Valor": len(resultado.cuentas_transmision),
            },
            {
                "Indicador": "Registros Formato 351",
                "Valor": len(resultado.formato_351),
            },
            {
                "Indicador": "Total Valor 351",
                "Valor": resultado.formato_351[
                    "Valor_351"
                ].sum(),
            },
        ]
    )

    try:
        with pd.ExcelWriter(
            ruta_salida,
            engine="openpyxl",
        ) as writer:
            resumen.to_excel(
                writer,
                sheet_name="RESUMEN",
                index=False,
            )

            resultado.base_negocios.to_excel(
                writer,
                sheet_name="BASE_NEGOCIOS",
                index=False,
            )

            resultado.cuentas_transmision.to_excel(
                writer,
                sheet_name="CUENTAS_TRANSMISION",
                index=False,
            )

            resultado.formato_351.to_excel(
                writer,
                sheet_name="FORMATO_351",
                index=False,
            )

    except PermissionError as error:
        raise ErrorSalida(
            f"No fue posible guardar '{ruta_salida.name}'. "
            "Comprueba que el archivo no esté abierto."
        ) from error

    except OSError as error:
        raise ErrorSalida(
            f"No fue posible generar el archivo de diagnóstico: {error}"
        ) from error

    if not ruta_salida.exists():
        raise ErrorSalida(
            f"El archivo de diagnóstico no fue creado: {ruta_salida}"
        )

    if ruta_salida.stat().st_size == 0:
        raise ErrorSalida(
            f"El archivo de diagnóstico quedó vacío: {ruta_salida}"
        )

    return ruta_salida