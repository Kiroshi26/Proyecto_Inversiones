from dataclasses import dataclass

import pandas as pd

from src.insumos import InsumosProceso
from src.validaciones import (
    ErrorValidacion,
    validar_columnas,
    validar_dataframe_no_vacio,
)

COLUMNAS_NEGOCIOS = [
    "No. de Radicación del Negocio Fiduciario",
    "Código contable",
    "Nombre del Fideicomiso",
]


@dataclass
class ResultadoPreparacion:
    """
    Contiene las bases preparadas y las estadísticas del proceso.
    """

    base_negocios: pd.DataFrame
    cuentas_transmision: pd.DataFrame
    formato_351: pd.DataFrame
    filas_antes_duplicados: int
    duplicados_eliminados: int


def normalizar_identificador(valor: object) -> str:
    """
    Convierte códigos numéricos o alfanuméricos en texto limpio.

    Ejemplos:
        100030.0 -> "100030"
        " 100030 " -> "100030"
        None -> ""
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.lower() in {"nan", "none", "nat"}:
        return ""

    if texto.endswith(".0"):
        parte_entera = texto[:-2]

        if parte_entera.replace("-", "", 1).isdigit():
            texto = parte_entera

    return texto


def preparar_fuente_negocios(
    dataframe: pd.DataFrame,
    nombre_fuente: str,
) -> pd.DataFrame:
    """
    Valida y normaliza una fuente de negocios fiduciarios.
    """
    validar_columnas(
        dataframe.columns,
        COLUMNAS_NEGOCIOS,
        nombre_fuente,
    )

    resultado = dataframe[COLUMNAS_NEGOCIOS].copy()

    resultado["No. de Radicación del Negocio Fiduciario"] = resultado[
        "No. de Radicación del Negocio Fiduciario"
    ].apply(normalizar_identificador)

    resultado["Código contable"] = resultado["Código contable"].apply(
        normalizar_identificador
    )

    resultado["Nombre del Fideicomiso"] = (
        resultado["Nombre del Fideicomiso"].fillna("").astype(str).str.strip()
    )

    # Se eliminan únicamente las filas que no permiten identificar
    # ni el número Super ni el código contable.
    resultado = resultado[
        (resultado["No. de Radicación del Negocio Fiduciario"] != "")
        & (resultado["Código contable"] != "")
    ].copy()

    validar_dataframe_no_vacio(
        len(resultado),
        nombre_fuente,
    )

    return resultado


def preparar_formato_351(
    formato_351: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normaliza las cuentas, números Super y valores del Formato 351.
    """
    columnas_requeridas = [
        "Cta_Con351",
        "No. Sup351",
        "Valor_351",
    ]

    validar_columnas(
        formato_351.columns,
        columnas_requeridas,
        "Formato 351 preparado",
    )

    resultado = formato_351[columnas_requeridas].copy()

    resultado["Cta_Con351"] = resultado["Cta_Con351"].apply(normalizar_identificador)

    resultado["No. Sup351"] = resultado["No. Sup351"].apply(normalizar_identificador)

    resultado["Valor_351"] = pd.to_numeric(
        resultado["Valor_351"],
        errors="coerce",
    ).fillna(0)

    resultado = resultado[resultado["Cta_Con351"].str.startswith("13")].copy()

    resultado = resultado.groupby(
        ["Cta_Con351", "No. Sup351"],
        as_index=False,
        dropna=False,
    )["Valor_351"].sum()

    validar_dataframe_no_vacio(
        len(resultado),
        "Formato 351 normalizado",
    )

    return resultado


def construir_base_negocios(
    negocios_vigentes: pd.DataFrame,
    centros_costos: pd.DataFrame,
) -> tuple:
    """
    Une negocios vigentes y centros de costos.

    La prioridad se conserva según el proceso original:
    primero Centros de Costos y después Negocios Vigentes.
    Si existe la misma combinación de número Super y código
    contable, se conserva la primera aparición.
    """
    vigentes = preparar_fuente_negocios(
        negocios_vigentes,
        "Negocios vigentes",
    )

    centros = preparar_fuente_negocios(
        centros_costos,
        "Centros de costos",
    )

    centros["Fuente"] = "CENTROS DE COSTOS"
    vigentes["Fuente"] = "NEGOCIOS VIGENTES"

    base_completa = pd.concat(
        [centros, vigentes],
        ignore_index=True,
    )

    filas_antes = len(base_completa)

    base_completa = base_completa.drop_duplicates(
        subset=[
            "No. de Radicación del Negocio Fiduciario",
            "Código contable",
        ],
        keep="first",
    ).copy()

    duplicados_eliminados = filas_antes - len(base_completa)

    base_completa = base_completa.rename(
        columns={"No. de Radicación del Negocio Fiduciario": ("Nro. Super")}
    )

    base_completa = base_completa[
        [
            "Nro. Super",
            "Código contable",
            "Nombre del Fideicomiso",
            "Fuente",
        ]
    ].copy()

    base_completa = base_completa.sort_values(
        by=[
            "Nro. Super",
            "Código contable",
        ],
        kind="stable",
        ignore_index=True,
    )

    validar_dataframe_no_vacio(
        len(base_completa),
        "Base consolidada de negocios",
    )

    return (
        base_completa,
        filas_antes,
        duplicados_eliminados,
    )


def obtener_cuentas_transmision(
    formato_351: pd.DataFrame,
) -> pd.DataFrame:
    """
    Obtiene las cuentas de transmisión únicas del Formato 351.
    """
    cuentas = (
        formato_351[["Cta_Con351"]]
        .drop_duplicates()
        .rename(
            columns={
                "Cta_Con351": "Cta_tras",
            }
        )
        .sort_values(
            by="Cta_tras",
            kind="stable",
            ignore_index=True,
        )
    )

    validar_dataframe_no_vacio(
        len(cuentas),
        "Cuentas de transmisión",
    )

    return cuentas


def preparar_insumos(
    insumos: InsumosProceso,
) -> ResultadoPreparacion:
    """
    Ejecuta toda la preparación de los insumos.
    """
    formato_351 = preparar_formato_351(insumos.formato_351)

    (
        base_negocios,
        filas_antes,
        duplicados_eliminados,
    ) = construir_base_negocios(
        negocios_vigentes=insumos.negocios_vigentes,
        centros_costos=insumos.centros_costos,
    )

    cuentas_transmision = obtener_cuentas_transmision(formato_351)

    return ResultadoPreparacion(
        base_negocios=base_negocios,
        cuentas_transmision=cuentas_transmision,
        formato_351=formato_351,
        filas_antes_duplicados=filas_antes,
        duplicados_eliminados=duplicados_eliminados,
    )
