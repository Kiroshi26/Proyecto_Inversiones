from dataclasses import dataclass

import pandas as pd

from src.base_datos import normalizar_saldos
from src.procesamiento import ResultadoPreparacion


class ErrorMotorInversiones(Exception):
    pass


@dataclass
class ResultadoInversiones:
    saldos: pd.DataFrame
    baseneg: pd.DataFrame


def normalizar_texto(valor) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.lower() in {"nan", "none", "nat"}:
        return ""

    if texto.endswith(".0"):
        parte = texto[:-2]
        if parte.replace("-", "", 1).isdigit():
            return parte

    return texto


def construir_cta_6dg(
    saldos_nacional: pd.DataFrame,
) -> pd.DataFrame:
    resultado = saldos_nacional.copy()

    resultado["CONTABILIDAD"] = (
        resultado["CONTABILIDAD"]
        .apply(normalizar_texto)
    )

    resultado["CUENTA"] = (
        resultado["CUENTA"]
        .apply(normalizar_texto)
    )

    resultado["CTA_6DG"] = (
        resultado["CUENTA"]
        .str[:6]
    )

    return resultado


def cruzar_base_negocios(
    nacional: pd.DataFrame,
    base_negocios: pd.DataFrame,
) -> pd.DataFrame:

    trabajo = nacional.merge(
        base_negocios,
        left_on="CONTABILIDAD",
        right_on="Código contable",
        how="left",
    )

    trabajo["Nro. Super"] = (
        trabajo["Nro. Super"]
        .apply(normalizar_texto)
    )

    return trabajo


def agrupar_saldos(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    agrupado = (
        dataframe
        .groupby(
            [
                "Nro. Super",
                "CTA_6DG",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            TOTAL_MES=(
                "TOTAL_MES",
                "sum",
            )
        )
    )

    return agrupado


def recuperar_datos_negocio(
    saldos_agrupados: pd.DataFrame,
    base_negocios: pd.DataFrame,
) -> pd.DataFrame:

    datos_negocio = (
        base_negocios[
            [
                "Nro. Super",
                "Código contable",
                "Nombre del Fideicomiso",
            ]
        ]
        .drop_duplicates(
            subset=["Nro. Super"],
            keep="first",
        )
    )

    resultado = saldos_agrupados.merge(
        datos_negocio,
        on="Nro. Super",
        how="left",
    )

    return resultado


def cruzar_formato_351(
    dataframe: pd.DataFrame,
    formato_351: pd.DataFrame,
) -> pd.DataFrame:

    trabajo = dataframe.copy()

    trabajo["Nro. Super"] = (
        trabajo["Nro. Super"]
        .apply(normalizar_texto)
    )

    trabajo["CTA_6DG"] = (
        trabajo["CTA_6DG"]
        .apply(normalizar_texto)
    )

    formato = formato_351.copy()

    formato["No. Sup351"] = (
        formato["No. Sup351"]
        .apply(normalizar_texto)
    )

    formato["Cta_Con351"] = (
        formato["Cta_Con351"]
        .apply(normalizar_texto)
    )

    trabajo = trabajo.merge(
        formato,
        left_on=[
            "Nro. Super",
            "CTA_6DG",
        ],
        right_on=[
            "No. Sup351",
            "Cta_Con351",
        ],
        how="left",
    )

    trabajo["Valor_351"] = (
        pd.to_numeric(
            trabajo["Valor_351"],
            errors="coerce",
        )
        .fillna(0)
    )

    trabajo["DIFERENCIA"] = (
        trabajo["TOTAL_MES"]
        - trabajo["Valor_351"]
    )

    trabajo.drop(
        columns=[
            "No. Sup351",
            "Cta_Con351",
        ],
        inplace=True,
        errors="ignore",
    )

    return trabajo


def construir_saldos_finales(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    resultado = dataframe[
        [
            "Código contable",
            "Nro. Super",
            "Nombre del Fideicomiso",
            "CTA_6DG",
            "TOTAL_MES",
            "Valor_351",
            "DIFERENCIA",
        ]
    ].copy()

    resultado.rename(
        columns={
            "Nro. Super": "No. Super",
        },
        inplace=True,
    )

    resultado["Código contable"] = (
        resultado["Código contable"]
        .apply(normalizar_texto)
    )

    resultado["No. Super"] = (
        resultado["No. Super"]
        .apply(normalizar_texto)
    )

    resultado["CTA_6DG"] = (
        resultado["CTA_6DG"]
        .apply(normalizar_texto)
    )

    resultado["Nombre del Fideicomiso"] = (
        resultado["Nombre del Fideicomiso"]
        .fillna("")
    )

    resultado = resultado.sort_values(
        by=[
            "Código contable",
            "No. Super",
            "CTA_6DG",
        ],
        kind="stable",
        ignore_index=True,
    )

    return resultado


def ejecutar_motor_inversiones(
    saldos_nacional: pd.DataFrame,
    resultado_preparacion: ResultadoPreparacion,
) -> ResultadoInversiones:

    if saldos_nacional.empty:
        raise ErrorMotorInversiones(
            "No se recibieron saldos de Nacional."
        )

    nacional = normalizar_saldos(
        saldos_nacional
    )

    nacional = construir_cta_6dg(
        nacional
    )

    nacional = cruzar_base_negocios(
        nacional,
        resultado_preparacion.base_negocios,
    )

    agrupado = agrupar_saldos(
        nacional
    )

    agrupado = recuperar_datos_negocio(
        agrupado,
        resultado_preparacion.base_negocios,
    )

    agrupado = cruzar_formato_351(
        agrupado,
        resultado_preparacion.formato_351,
    )

    saldos = construir_saldos_finales(
        agrupado
    )

    baseneg = (
        resultado_preparacion.base_negocios.copy()
    )

    return ResultadoInversiones(
        saldos=saldos,
        baseneg=baseneg,
    )