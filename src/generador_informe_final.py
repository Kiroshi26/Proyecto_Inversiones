from pathlib import Path

import pandas as pd


class ErrorInformeFinal(Exception):
    pass


def validar_saldos(
    saldos: pd.DataFrame,
) -> None:

    if saldos is None:
        raise ErrorInformeFinal(
            "No existe información de SALDOS."
        )

    if saldos.empty:
        raise ErrorInformeFinal(
            "La hoja SALDOS está vacía."
        )


def construir_resumen(
    saldos: pd.DataFrame,
) -> pd.DataFrame:

    resumen = (
        saldos
        .groupby(
            [
                "Código contable",
                "No. Super",
                "Nombre del Fideicomiso",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            TOTAL_MES=(
                "TOTAL_MES",
                "sum",
            ),
            VALOR_351=(
                "Valor_351",
                "sum",
            ),
            DIFERENCIA=(
                "DIFERENCIA",
                "sum",
            ),
        )
    )

    resumen["ABS_DIFERENCIA"] = (
        resumen["DIFERENCIA"]
        .abs()
    )

    resumen = resumen.sort_values(
        by="ABS_DIFERENCIA",
        ascending=False,
        kind="stable",
        ignore_index=True,
    )

    return resumen


def aplicar_formato(
    writer,
    dataframe,
    hoja_nombre,
):

    workbook = writer.book
    worksheet = writer.sheets[hoja_nombre]

    formato_encabezado = workbook.add_format(
        {
            "bold": True,
            "font_color": "white",
            "bg_color": "black",
            "align": "center",
            "border": 1,
        }
    )

    formato_texto = workbook.add_format(
        {
            "align": "left",
        }
    )

    formato_numero = workbook.add_format(
        {
            "num_format":
            "#,##0.00;[Red]-#,##0.00",
            "align": "right",
        }
    )

    worksheet.freeze_panes(1, 0)
    worksheet.hide_gridlines(2)

    for idx, columna in enumerate(
        dataframe.columns
    ):

        worksheet.write(
            0,
            idx,
            columna,
            formato_encabezado,
        )

        ancho = max(
            18,
            len(str(columna)) + 4,
        )

        if dataframe[columna].dtype == object:

            worksheet.set_column(
                idx,
                idx,
                ancho,
                formato_texto,
            )

        else:

            worksheet.set_column(
                idx,
                idx,
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


def generar_informe_final(
    saldos: pd.DataFrame,
    carpeta_salida: Path,
    periodo: str,
) -> Path:

    validar_saldos(
        saldos
    )

    carpeta_salida = Path(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    resumen = construir_resumen(
        saldos
    )

    ruta_archivo = (
        carpeta_salida
        /
        f"Informe_Val_Inv_{periodo}.xlsx"
    )

    try:

        with pd.ExcelWriter(
            ruta_archivo,
            engine="xlsxwriter",
        ) as writer:

            saldos.to_excel(
                writer,
                sheet_name="SALDOS_DETALLE",
                index=False,
            )

            resumen.to_excel(
                writer,
                sheet_name="RESUMEN",
                index=False,
            )

            aplicar_formato(
                writer,
                saldos,
                "SALDOS_DETALLE",
            )

            aplicar_formato(
                writer,
                resumen,
                "RESUMEN",
            )

    except PermissionError as error:

        raise ErrorInformeFinal(
            "El informe está abierto en Excel."
        ) from error

    except Exception as error:

        raise ErrorInformeFinal(
            f"Error generando informe: {error}"
        ) from error

    if not ruta_archivo.exists():

        raise ErrorInformeFinal(
            "No fue posible generar el informe."
        )

    if ruta_archivo.stat().st_size == 0:

        raise ErrorInformeFinal(
            "El informe quedó vacío."
        )

    return ruta_archivo