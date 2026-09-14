from pathlib import Path

import pandas as pd

from src.conciliacion import ResultadoConciliacion


class ErrorGeneradorSaldos(Exception):
    pass


def validar_dataframe(
    dataframe: pd.DataFrame,
    nombre: str,
):

    if dataframe is None:
        raise ErrorGeneradorSaldos(
            f"{nombre} no existe."
        )

    if dataframe.empty:
        raise ErrorGeneradorSaldos(
            f"{nombre} está vacío."
        )


def aplicar_formato_excel(
    writer,
    dataframe,
    hoja_nombre,
):

    workbook = writer.book
    worksheet = writer.sheets[hoja_nombre]

    formato_texto = workbook.add_format(
        {
            "align": "left"
        }
    )

    formato_numero = workbook.add_format(
        {
            "num_format":
            "#,##0.00;[Red]-#,##0.00",
            "align": "right"
        }
    )

    formato_encabezado = workbook.add_format(
        {
            "bold": True,
            "font_color": "white",
            "bg_color": "black",
            "align": "center",
            "border": 1,
        }
    )

    worksheet.freeze_panes(1, 0)
    worksheet.hide_gridlines(2)

    for columna_idx, columna in enumerate(
        dataframe.columns
    ):

        worksheet.write(
            0,
            columna_idx,
            columna,
            formato_encabezado,
        )

        ancho = max(
            18,
            len(str(columna)) + 5
        )

        if dataframe[columna].dtype == object:

            worksheet.set_column(
                columna_idx,
                columna_idx,
                ancho,
                formato_texto,
            )

        else:

            worksheet.set_column(
                columna_idx,
                columna_idx,
                ancho,
                formato_numero,
            )

    worksheet.add_table(
        0,
        0,
        len(dataframe),
        len(dataframe.columns) - 1,
        {
            "style": "Table Style Medium 1",
            "columns": [
                {"header": c}
                for c in dataframe.columns
            ],
        },
    )


def generar_saldos_inversiones(
    resultado: ResultadoConciliacion,
    carpeta_salida: Path,
) -> Path:

    validar_dataframe(
        resultado.saldos,
        "SALDOS",
    )

    validar_dataframe(
        resultado.baseneg,
        "BASENEG",
    )

    carpeta_salida = Path(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_archivo = (
        carpeta_salida
        / "Saldos_Inversiones.xlsx"
    )

    try:

        with pd.ExcelWriter(
            ruta_archivo,
            engine="xlsxwriter",
        ) as writer:

            resultado.saldos.to_excel(
                writer,
                sheet_name="SALDOS",
                index=False,
            )

            resultado.baseneg.to_excel(
                writer,
                sheet_name="BASENEG",
                index=False,
            )

            aplicar_formato_excel(
                writer,
                resultado.saldos,
                "SALDOS",
            )

            aplicar_formato_excel(
                writer,
                resultado.baseneg,
                "BASENEG",
            )

    except PermissionError as error:

        raise ErrorGeneradorSaldos(
            "El archivo está abierto."
        ) from error

    except Exception as error:

        raise ErrorGeneradorSaldos(
            f"Error generando archivo: {error}"
        ) from error

    if not ruta_archivo.exists():

        raise ErrorGeneradorSaldos(
            "No se generó el archivo."
        )

    if ruta_archivo.stat().st_size == 0:

        raise ErrorGeneradorSaldos(
            "El archivo quedó vacío."
        )

    return ruta_archivo