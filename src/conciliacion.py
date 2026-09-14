from dataclasses import dataclass

import pandas as pd


class ErrorConciliacion(Exception):
    pass


@dataclass
class ResultadoConciliacion:
    saldos: pd.DataFrame
    baseneg: pd.DataFrame


def normalizar_texto(valor):

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

        if parte_entera.replace("-", "", 1).isdigit():
            texto = parte_entera

    return texto


def preparar_saldos_nacional(
    saldos_nacional: pd.DataFrame,
) -> pd.DataFrame:

    df = saldos_nacional.copy()

    df["CONTABILIDAD"] = df["CONTABILIDAD"].apply(normalizar_texto)

    df["CUENTA"] = df["CUENTA"].apply(normalizar_texto)

    df["CTA_6DG"] = df["CUENTA"].str[:6]

    return df


def construir_baseneg(
    base_negocios: pd.DataFrame,
) -> pd.DataFrame:

    columnas = [
        "Nro. Super",
        "Código contable",
        "Nombre del Fideicomiso",
    ]

    resultado = base_negocios[columnas].drop_duplicates().copy()

    resultado.sort_values(
        by=[
            "Nro. Super",
            "Código contable",
        ],
        inplace=True,
        kind="stable",
        ignore_index=True,
    )

    return resultado


def cruzar_base_negocios(
    nacional: pd.DataFrame,
    base_negocios: pd.DataFrame,
) -> pd.DataFrame:

    resultado = nacional.merge(
        base_negocios,
        left_on="CONTABILIDAD",
        right_on="Código contable",
        how="left",
    )

    return resultado


def agrupar_por_super_y_cta(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    agrupado = dataframe.groupby(
        [
            "Nro. Super",
            "CTA_6DG",
        ],
        as_index=False,
        dropna=False,
    ).agg(
        TOTAL_MES=(
            "TOTAL_MES",
            "sum",
        )
    )

    return agrupado


def recuperar_informacion_negocio(
    agrupado: pd.DataFrame,
    base_negocios: pd.DataFrame,
) -> pd.DataFrame:

    informacion = base_negocios[
        [
            "Nro. Super",
            "Código contable",
            "Nombre del Fideicomiso",
        ]
    ].drop_duplicates(
        subset=["Nro. Super"],
        keep="first",
    )

    resultado = agrupado.merge(
        informacion,
        on="Nro. Super",
        how="left",
    )

    return resultado


def cruzar_formato_351(
    dataframe: pd.DataFrame,
    formato_351: pd.DataFrame,
) -> pd.DataFrame:

    trabajo = dataframe.copy()

    trabajo["Nro. Super"] = trabajo["Nro. Super"].apply(normalizar_texto)

    trabajo["CTA_6DG"] = trabajo["CTA_6DG"].apply(normalizar_texto)

    formato = formato_351.copy()

    formato["No. Sup351"] = formato["No. Sup351"].apply(normalizar_texto)

    formato["Cta_Con351"] = formato["Cta_Con351"].apply(normalizar_texto)

    resultado = trabajo.merge(
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

    resultado["Valor_351"] = pd.to_numeric(
        resultado["Valor_351"],
        errors="coerce",
    ).fillna(0)

    resultado["DIFERENCIA"] = resultado["TOTAL_MES"] - resultado["Valor_351"]

    resultado.drop(
        columns=[
            "No. Sup351",
            "Cta_Con351",
        ],
        inplace=True,
        errors="ignore",
    )

    return resultado


def construir_saldos_final(
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

    resultado.sort_values(
        by=[
            "Código contable",
            "No. Super",
            "CTA_6DG",
        ],
        inplace=True,
        ignore_index=True,
        kind="stable",
    )

    return resultado


def ejecutar_conciliacion(
    saldos_nacional: pd.DataFrame,
    base_negocios: pd.DataFrame,
    formato_351: pd.DataFrame,
) -> ResultadoConciliacion:

    if saldos_nacional.empty:
        raise ErrorConciliacion("No existen registros de Nacional.")

    nacional = preparar_saldos_nacional(saldos_nacional)

    nacional = cruzar_base_negocios(
        nacional,
        base_negocios,
    )

    agrupado = agrupar_por_super_y_cta(nacional)

    agrupado = recuperar_informacion_negocio(
        agrupado,
        base_negocios,
    )

    agrupado = cruzar_formato_351(
        agrupado,
        formato_351,
    )

    saldos = construir_saldos_final(agrupado)

    baseneg = construir_baseneg(base_negocios)

    return ResultadoConciliacion(
        saldos=saldos,
        baseneg=baseneg,
    )
