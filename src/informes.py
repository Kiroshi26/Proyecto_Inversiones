import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


class ErrorInforme(Exception):
    """Error relacionado con la generación del informe."""


MAPEO_COLUMNAS_INFORME: Dict[str, str] = {
    "C\u00f3digo contable": "CONTABILIDAD",
    "No. Super": "SUPER",
    "Nombre del Fideicomiso": "NOMBRE FIDEICOMISO",
    "CTA_6DG": "CTA_6DG",
    "TOTAL_MES": "TOTAL_MES",
    "Valor_351": "VALOR 351",
    "DIFERENCIA": "DIFERENCIA",
}


COLUMNAS_TEXTO = [
    "CONTABILIDAD",
    "SUPER",
    "CTA_6DG",
]


COLUMNAS_NUMERICAS = [
    "TOTAL_MES",
    "VALOR 351",
    "DIFERENCIA",
]


def normalizar_identificador(valor: object) -> str:
    """
    Convierte un identificador numérico o alfanumérico
    en texto limpio.

    Ejemplos:
        100030.0 -> "100030"
        " 100030 " -> "100030"
        None -> ""
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.lower() in {
        "nan",
        "none",
        "nat",
    }:
        return ""

    if texto.endswith(".0"):
        parte_entera = texto[:-2]

        if parte_entera.replace(
            "-",
            "",
            1,
        ).isdigit():
            texto = parte_entera

    return texto


def preparar_datos_informe(
    saldos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara los datos con la estructura del informe final.

    El resultado contiene estas columnas:
        CONTABILIDAD
        SUPER
        NOMBRE FIDEICOMISO
        CTA_6DG
        TOTAL_MES
        VALOR 351
        DIFERENCIA
    """
    if not isinstance(
        saldos,
        pd.DataFrame,
    ):
        raise ErrorInforme(
            "Los saldos recibidos no corresponden "
            "a un DataFrame válido."
        )

    columnas_requeridas = list(
        MAPEO_COLUMNAS_INFORME.keys()
    )

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in saldos.columns
    ]

    if columnas_faltantes:
        raise ErrorInforme(
            "Faltan columnas para generar el informe: "
            + ", ".join(columnas_faltantes)
        )

    informe = saldos[
        columnas_requeridas
    ].copy()

    informe = informe.rename(
        columns=MAPEO_COLUMNAS_INFORME
    )

    for columna in COLUMNAS_TEXTO:
        informe[columna] = informe[
            columna
        ].apply(
            normalizar_identificador
        )

    informe["NOMBRE FIDEICOMISO"] = (
        informe["NOMBRE FIDEICOMISO"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    for columna in COLUMNAS_NUMERICAS:
        informe[columna] = pd.to_numeric(
            informe[columna],
            errors="coerce",
        ).fillna(0)

    if informe.empty:
        raise ErrorInforme(
            "No existen registros para generar el informe."
        )

    return informe


def limpiar_periodo(
    periodo: str,
) -> str:
    """
    Limpia el periodo para utilizarlo
    dentro del nombre del archivo.
    """
    periodo_limpio = str(
        periodo
    ).strip()

    reemplazos = {
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "-",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "-",
    }

    for caracter, reemplazo in reemplazos.items():
        periodo_limpio = periodo_limpio.replace(
            caracter,
            reemplazo,
        )

    if not periodo_limpio:
        raise ErrorInforme(
            "El periodo del informe está vacío."
        )

    return periodo_limpio


def validar_archivo_existente(
    ruta_archivo: Path,
) -> None:
    """
    Comprueba que un archivo existente sea válido
    antes de crear un respaldo.
    """
    ruta_archivo = Path(
        ruta_archivo
    )

    if not ruta_archivo.exists():
        raise ErrorInforme(
            f"No se encontró el archivo: {ruta_archivo}"
        )

    if not ruta_archivo.is_file():
        raise ErrorInforme(
            "La ruta no corresponde a un archivo: "
            f"{ruta_archivo}"
        )

    if ruta_archivo.stat().st_size == 0:
        raise ErrorInforme(
            "El archivo existente está vacío: "
            f"{ruta_archivo}"
        )


def crear_nombre_respaldo(
    ruta_informe: Path,
) -> str:
    """
    Construye el nombre del respaldo utilizando
    fecha y hora de ejecución.
    """
    fecha_hora = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        f"{ruta_informe.stem}_"
        f"{fecha_hora}"
        f"{ruta_informe.suffix}"
    )


def respaldar_informe_existente(
    ruta_informe: Path,
    carpeta_respaldos: Path,
) -> Optional:
    """
    Crea un respaldo del informe antes de reemplazarlo.

    Si el informe todavía no existe, devuelve None.
    """
    ruta_informe = Path(
        ruta_informe
    )

    carpeta_respaldos = Path(
        carpeta_respaldos
    )

    if not ruta_informe.exists():
        return None

    validar_archivo_existente(
        ruta_informe
    )

    carpeta_respaldos.mkdir(
        parents=True,
        exist_ok=True,
    )

    nombre_respaldo = crear_nombre_respaldo(
        ruta_informe
    )

    ruta_respaldo = (
        carpeta_respaldos
        / nombre_respaldo
    )

    contador = 1

    while ruta_respaldo.exists():
        nombre_respaldo = (
            f"{ruta_informe.stem}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
            f"{contador}"
            f"{ruta_informe.suffix}"
        )

        ruta_respaldo = (
            carpeta_respaldos
            / nombre_respaldo
        )

        contador += 1

    try:
        shutil.copy2(
            ruta_informe,
            ruta_respaldo,
        )

    except PermissionError as error:
        raise ErrorInforme(
            "No fue posible crear el respaldo del informe. "
            "Comprueba los permisos de la carpeta de respaldos."
        ) from error

    except OSError as error:
        raise ErrorInforme(
            "Ocurrió un error al crear el respaldo: "
            f"{error}"
        ) from error

    if not ruta_respaldo.exists():
        raise ErrorInforme(
            f"No se creó el respaldo: {ruta_respaldo}"
        )

    if ruta_respaldo.stat().st_size == 0:
        raise ErrorInforme(
            f"El respaldo quedó vacío: {ruta_respaldo}"
        )

    return ruta_respaldo


def crear_formatos_excel(
    libro,
) -> Dict[str, object]:
    """
    Crea los formatos utilizados en el informe.
    """
    formato_texto = libro.add_format(
        {
            "num_format": "@",
            "align": "left",
            "valign": "vcenter",
        }
    )

    formato_nombre = libro.add_format(
        {
            "align": "left",
            "valign": "vcenter",
        }
    )

    formato_numerico = libro.add_format(
        {
            "num_format": (
                '#,##0.00;[Red]-#,##0.00'
            ),
            "align": "right",
            "valign": "vcenter",
        }
    )

    formato_encabezado = libro.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#000000",
            "align": "center",
            "valign": "vcenter",
            "border": 1,
        }
    )

    return {
        "texto": formato_texto,
        "nombre": formato_nombre,
        "numerico": formato_numerico,
        "encabezado": formato_encabezado,
    }


def escribir_datos_informe(
    hoja,
    informe: pd.DataFrame,
    formatos: Dict[str, object],
) -> None:
    """
    Escribe los valores del informe en la hoja Excel.

    La fila cero queda reservada para los encabezados
    de la tabla.
    """
    encabezados = informe.columns.tolist()

    for numero_fila, fila in enumerate(
        informe.itertuples(
            index=False,
            name=None,
        ),
        start=1,
    ):
        for numero_columna, valor in enumerate(
            fila
        ):
            nombre_columna = encabezados[
                numero_columna
            ]

            if nombre_columna in COLUMNAS_TEXTO:
                hoja.write_string(
                    numero_fila,
                    numero_columna,
                    normalizar_identificador(valor),
                    formatos["texto"],
                )

            elif nombre_columna in COLUMNAS_NUMERICAS:
                valor_numerico = (
                    0.0
                    if pd.isna(valor)
                    else float(valor)
                )

                hoja.write_number(
                    numero_fila,
                    numero_columna,
                    valor_numerico,
                    formatos["numerico"],
                )

            else:
                texto = (
                    ""
                    if pd.isna(valor)
                    else str(valor)
                )

                hoja.write(
                    numero_fila,
                    numero_columna,
                    texto,
                    formatos["nombre"],
                )


def agregar_tabla_informe(
    hoja,
    informe: pd.DataFrame,
    formato_encabezado,
) -> None:
    """
    Crea la tabla estructurada SALDOS.
    """
    encabezados = informe.columns.tolist()

    columnas_tabla = []

    for encabezado in encabezados:
        columnas_tabla.append(
            {
                "header": encabezado,
                "header_format": formato_encabezado,
            }
        )

    ultima_fila = len(informe)
    ultima_columna = len(encabezados) - 1

    hoja.add_table(
        0,
        0,
        ultima_fila,
        ultima_columna,
        {
            "name": "SALDOS",
            "style": "Table Style Medium 1",
            "columns": columnas_tabla,
            "autofilter": True,
            "banded_rows": True,
            "banded_columns": False,
        },
    )


def configurar_presentacion_hoja(
    hoja,
    formatos: Dict[str, object],
) -> None:
    """
    Configura anchos, paneles, cuadrícula
    y opciones de impresión.
    """
    hoja.freeze_panes(
        1,
        0,
    )

    hoja.hide_gridlines(
        2
    )

    hoja.set_row(
        0,
        25,
    )

    hoja.set_column(
        "A:A",
        18,
        formatos["texto"],
    )

    hoja.set_column(
        "B:B",
        15,
        formatos["texto"],
    )

    hoja.set_column(
        "C:C",
        55,
        formatos["nombre"],
    )

    hoja.set_column(
        "D:D",
        14,
        formatos["texto"],
    )

    hoja.set_column(
        "E:G",
        22,
        formatos["numerico"],
    )

    hoja.set_landscape()

    hoja.fit_to_pages(
        1,
        0,
    )

    hoja.repeat_rows(
        0,
    )

    hoja.set_margins(
        left=0.25,
        right=0.25,
        top=0.50,
        bottom=0.50,
    )


def escribir_archivo_informe(
    informe: pd.DataFrame,
    ruta_informe: Path,
) -> None:
    """
    Genera físicamente el archivo Excel del informe.
    """
    try:
        with pd.ExcelWriter(
            ruta_informe,
            engine="xlsxwriter",
        ) as writer:
            libro = writer.book

            hoja = libro.add_worksheet(
                "Informe"
            )

            writer.sheets[
                "Informe"
            ] = hoja

            formatos = crear_formatos_excel(
                libro
            )

            escribir_datos_informe(
                hoja=hoja,
                informe=informe,
                formatos=formatos,
            )

            agregar_tabla_informe(
                hoja=hoja,
                informe=informe,
                formato_encabezado=formatos[
                    "encabezado"
                ],
            )

            configurar_presentacion_hoja(
                hoja=hoja,
                formatos=formatos,
            )

    except PermissionError as error:
        raise ErrorInforme(
            "No fue posible generar el informe. "
            "Comprueba que el archivo no esté abierto en Excel."
        ) from error

    except Exception as error:
        raise ErrorInforme(
            "Ocurrió un error al escribir el informe: "
            f"{type(error).__name__}: {error}"
        ) from error


def generar_informe_prueba(
    saldos: pd.DataFrame,
    carpeta_salida: Path,
    periodo: str,
    carpeta_respaldos: Optional[Path] = None,
) -> Path:
    """
    Genera un informe separado para pruebas.

    Si el informe ya existe:
        1. Crea un respaldo con fecha y hora.
        2. Reemplaza el archivo principal.

    El archivo contiene:
        - Una sola hoja llamada Informe.
        - Solo valores.
        - Tabla SALDOS.
        - Estilo Table Style Medium 1.
        - Filtros.
        - Formatos monetarios.
        - Identificadores guardados como texto.
    """
    carpeta_salida = Path(
        carpeta_salida
    )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    informe = preparar_datos_informe(
        saldos
    )

    periodo_limpio = limpiar_periodo(
        periodo
    )

    nombre_archivo = (
        f"Informe_Val_Inv_"
        f"{periodo_limpio}_PRUEBA.xlsx"
    )

    ruta_informe = (
        carpeta_salida
        / nombre_archivo
    )

    ruta_respaldo = None

    if ruta_informe.exists():
        if carpeta_respaldos is None:
            raise ErrorInforme(
                "El informe ya existe, pero no se configuró "
                "una carpeta para crear el respaldo."
            )

        ruta_respaldo = respaldar_informe_existente(
            ruta_informe=ruta_informe,
            carpeta_respaldos=carpeta_respaldos,
        )

    escribir_archivo_informe(
        informe=informe,
        ruta_informe=ruta_informe,
    )

    if not ruta_informe.exists():
        raise ErrorInforme(
            f"No se creó el informe: {ruta_informe}"
        )

    if ruta_informe.stat().st_size == 0:
        raise ErrorInforme(
            f"El informe quedó vacío: {ruta_informe}"
        )

    if ruta_respaldo is not None:
        print()
        print("RESPALDO CREADO:")
        print(ruta_respaldo)

    return ruta_informe