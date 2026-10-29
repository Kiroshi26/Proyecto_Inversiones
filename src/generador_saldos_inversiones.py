from pathlib import Path
from typing import Optional

import pandas as pd

from src.conciliacion import ResultadoConciliacion


class ErrorGeneradorSaldos(Exception):
    """Error al generar el archivo de reporte en Excel."""


def validar_dataframe(dataframe: Optional[pd.DataFrame], nombre: str) -> None:
    if dataframe is None:
        raise ErrorGeneradorSaldos(f"{nombre} no existe.")
    if dataframe.empty:
        raise ErrorGeneradorSaldos(f"{nombre} esta vacio.")


def aplicar_formato_excel(writer, dataframe: pd.DataFrame, hoja_nombre: str) -> None:
    workbook = writer.book
    worksheet = writer.sheets[hoja_nombre]

    formato_texto = workbook.add_format({"align": "left", "valign": "vcenter"})
    formato_centro = workbook.add_format({"align": "center", "valign": "vcenter"})
    formato_entero = workbook.add_format({"num_format": "0", "align": "center", "valign": "vcenter"})
    formato_moneda = workbook.add_format({
        "num_format": "$#,##0.00;[Red]($#,##0.00);$0.00",
        "align": "right",
        "valign": "vcenter",
    })

    worksheet.freeze_panes(1, 0)

    # Definir formato por columna
    columnas_moneda = {"Saldo contable", "Saldo F351", "Diferencias", "TOTAL_MES", "Valor_351"}
    columnas_centro = {"Código SFC", "Código contable", "Grupo Óptima", "Subcuenta CUIF", "Tipo", "Subtipo"}

    column_specs = []
    for col_idx, columna in enumerate(dataframe.columns):
        col_name = str(columna)
        # Calcular ancho adecuado
        max_len = max(len(col_name), 10)
        # Muestrear algunas filas para ancho
        sample_vals = dataframe[columna].dropna().astype(str).head(50)
        if not sample_vals.empty:
            sample_len = sample_vals.map(len).max()
            max_len = max(max_len, min(sample_len, 40))

        ancho = max_len + 5

        if col_name in columnas_moneda:
            worksheet.set_column(col_idx, col_idx, max(ancho, 18), formato_moneda)
        elif col_name in {"Tipo", "Subtipo"}:
            worksheet.set_column(col_idx, col_idx, max(ancho, 10), formato_entero)
        elif col_name in columnas_centro:
            worksheet.set_column(col_idx, col_idx, max(ancho, 14), formato_centro)
        else:
            worksheet.set_column(col_idx, col_idx, max(ancho, 20), formato_texto)

        column_specs.append({"header": col_name})

    worksheet.add_table(
        0,
        0,
        len(dataframe),
        len(dataframe.columns) - 1,
        {
            "style": "Table Style Medium 1",
            "columns": column_specs,
        },
    )


def generar_saldos_inversiones(
    resultado: ResultadoConciliacion,
    carpeta_salida: Path,
    nombre_archivo: str = "Saldos_Inversiones.xlsx",
) -> Path:
    """
    Genera el archivo final Excel con las hojas SALDOS y BASENEG con diseno profesional.
    """
    validar_dataframe(resultado.saldos, "SALDOS")
    validar_dataframe(resultado.baseneg, "BASENEG")

    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_archivo = carpeta / nombre_archivo

    try:
        with pd.ExcelWriter(ruta_archivo, engine="xlsxwriter") as writer:
            resultado.saldos.to_excel(writer, sheet_name="SALDOS", index=False)
            resultado.baseneg.to_excel(writer, sheet_name="BASENEG", index=False)

            aplicar_formato_excel(writer, resultado.saldos, "SALDOS")
            aplicar_formato_excel(writer, resultado.baseneg, "BASENEG")

    except PermissionError as error:
        raise ErrorGeneradorSaldos(
            f"El archivo '{ruta_archivo.name}' esta abierto por otra aplicacion. "
            "Por favor cierralo antes de continuar."
        ) from error

    return ruta_archivo
