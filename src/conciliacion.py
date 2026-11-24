from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.insumos import normalizar_identificador
from src.parametros import SUBCUENTAS_VALIDACION


class ErrorConciliacion(Exception):
    """Error producido durante el proceso de conciliacion."""


@dataclass
class ResultadoConciliacion:
    saldos: pd.DataFrame
    resumen_subcuentas: pd.DataFrame
    baseneg: pd.DataFrame


COLUMNAS_SALDOS = [
    "Código SFC",
    "Código contable",
    "Grupo Óptima",
    "Tipo",
    "Subtipo",
    "Nombre del negocio",
    "Subcuenta CUIF",
    "Saldo contable",
    "Saldo F351",
    "Diferencias",
]

COLUMNAS_RESUMEN = [
    "Subcuenta CUIF",
    "Cantidad Negocios",
    "Saldo contable",
    "Saldo F351",
    "Diferencias",
]


def preparar_saldos_nacional(saldos_nacional: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza y filtra los saldos contables de Optima/Nacional para las 22 subcuentas oficiales.
    """
    if saldos_nacional.empty:
        raise ErrorConciliacion("No existen registros de saldos en Nacional/Optima.")

    df = saldos_nacional.copy()

    col_contable = "CONTABILIDAD" if "CONTABILIDAD" in df.columns else df.columns[1]
    col_cuenta = "CUENTA" if "CUENTA" in df.columns else df.columns[2]
    col_saldo = "TOTAL_MES" if "TOTAL_MES" in df.columns else df.columns[-1]

    df["CÓDIGO CONTABLE"] = df[col_contable].apply(normalizar_identificador)
    df["Subcuenta CUIF"] = df[col_cuenta].apply(normalizar_identificador).str[:6]
    df["Saldo contable"] = pd.to_numeric(df[col_saldo], errors="coerce").fillna(0.0)

    # Filtrar unicamente por las 22 subcuentas oficiales
    df = df[df["Subcuenta CUIF"].isin(SUBCUENTAS_VALIDACION)].copy()
    df = df[df["CÓDIGO CONTABLE"] != ""].copy()

    # Agrupar suma por (CÓDIGO CONTABLE, Subcuenta CUIF)
    agrupado = (
        df.groupby(["CÓDIGO CONTABLE", "Subcuenta CUIF"], as_index=False)["Saldo contable"]
        .sum()
    )

    return agrupado


def ejecutar_conciliacion(
    saldos_nacional: pd.DataFrame,
    base_negocios: pd.DataFrame,
    formato_351: pd.DataFrame,
) -> ResultadoConciliacion:
    """
    Ejecuta el motor de conciliacion segun las especificaciones de la Hoja 3 (Procedimiento).

    Unifica el resultado por subcuentas:
    Cuando un negocio (fideicomiso SFC) posee multiples codigos contables (ej. esquemas padre/hijo o
    etapas) asociados a la misma subcuenta contable, los saldos contables se suman y se consolidan
    en una sola fila para compararse contra el saldo unico reportado en el Formato 351, evitando
    duplicidades en el F351 y falsas diferencias.
    """
    df_optima = preparar_saldos_nacional(saldos_nacional)
    df_base = base_negocios.copy()
    df_f351 = formato_351.copy()

    cols_metadata = [
        "CÓDIGO SFC",
        "CÓDIGO CONTABLE",
        "Grupo Óptima",
        "Tipo",
        "Subtipo",
        "Nombre del negocio",
    ]
    df_base_meta = df_base[cols_metadata].drop_duplicates(subset=["CÓDIGO SFC", "CÓDIGO CONTABLE"])

    # 1. Asociar saldos de Optima con la metadata del negocio (por CÓDIGO CONTABLE)
    optima_con_base = df_optima.merge(df_base_meta, on="CÓDIGO CONTABLE", how="inner")

    # 2. Asociar saldos de F351 con la metadata del negocio (por CÓDIGO SFC)
    f351_con_base = df_f351.merge(df_base_meta, on="CÓDIGO SFC", how="inner")

    # 3. Construir el universo total de claves (CÓDIGO SFC, CÓDIGO CONTABLE, Subcuenta CUIF)
    keys_optima = optima_con_base[cols_metadata + ["Subcuenta CUIF"]]
    keys_f351 = f351_con_base[cols_metadata + ["Subcuenta CUIF"]]

    keys_totales = (
        pd.concat([keys_optima, keys_f351], ignore_index=True)
        .drop_duplicates(subset=["CÓDIGO SFC", "CÓDIGO CONTABLE", "Subcuenta CUIF"])
        .reset_index(drop=True)
    )

    # 4. Cruzar saldos de Optima por (CÓDIGO CONTABLE, Subcuenta CUIF)
    resultado = keys_totales.merge(
        df_optima[["CÓDIGO CONTABLE", "Subcuenta CUIF", "Saldo contable"]],
        on=["CÓDIGO CONTABLE", "Subcuenta CUIF"],
        how="left",
    )

    # 5. Cruzar saldos de F351 por (CÓDIGO SFC, Subcuenta CUIF)
    resultado = resultado.merge(
        df_f351[["CÓDIGO SFC", "Subcuenta CUIF", "Saldo F351"]],
        on=["CÓDIGO SFC", "Subcuenta CUIF"],
        how="left",
    )

    resultado["Saldo contable"] = resultado["Saldo contable"].fillna(0.0)
    resultado["Saldo F351"] = resultado["Saldo F351"].fillna(0.0)

    resultado.rename(
        columns={
            "CÓDIGO SFC": "Código SFC",
            "CÓDIGO CONTABLE": "Código contable",
        },
        inplace=True,
    )
    resultado["Código SFC"] = resultado["Código SFC"].fillna("N/A").replace({"": "N/A"})
    resultado["Grupo Óptima"] = resultado["Grupo Óptima"].fillna("N/A").replace({"": "N/A"})

    # 6. UNIFICACION POR SUBCUENTAS:
    # Si un negocio tiene filas con la misma subcuenta, se suman los saldos contables y se consolida en una sola fila.
    df_con_sfc = resultado[resultado["Código SFC"] != "N/A"].copy()
    df_sin_sfc = resultado[resultado["Código SFC"] == "N/A"].copy()

    # Negocios con Código SFC
    unified_con_sfc = (
        df_con_sfc.groupby(["Código SFC", "Subcuenta CUIF"], as_index=False)
        .agg({
            "Código contable": lambda cods: " / ".join(sorted(set(str(c) for c in cods if str(c) != ""))),
            "Grupo Óptima": "first",
            "Tipo": "first",
            "Subtipo": "first",
            "Nombre del negocio": "first",
            "Saldo contable": "sum",
            "Saldo F351": "first",
        })
    )

    # Negocios sin Código SFC (agrupados por Código contable)
    unified_sin_sfc = (
        df_sin_sfc.groupby(["Código contable", "Subcuenta CUIF"], as_index=False)
        .agg({
            "Código SFC": "first",
            "Grupo Óptima": "first",
            "Tipo": "first",
            "Subtipo": "first",
            "Nombre del negocio": "first",
            "Saldo contable": "sum",
            "Saldo F351": "first",
        })
    )

    saldos_unificados = pd.concat([unified_con_sfc, unified_sin_sfc], ignore_index=True)
    saldos_unificados["Diferencias"] = saldos_unificados["Saldo contable"] - saldos_unificados["Saldo F351"]

    saldos_unificados.sort_values(
        by=["Código SFC", "Código contable", "Subcuenta CUIF"],
        inplace=True,
        ignore_index=True,
        kind="stable",
    )
    saldos_final = saldos_unificados[COLUMNAS_SALDOS].copy()

    # 7. Resumen consolidado global por Subcuenta CUIF
    resumen_subcuentas = (
        saldos_final.groupby("Subcuenta CUIF", as_index=False)
        .agg(
            Cantidad_Negocios=("Código SFC", "count"),
            Saldo_Contable=("Saldo contable", "sum"),
            Saldo_F351=("Saldo F351", "sum"),
            Diferencias=("Diferencias", "sum"),
        )
        .rename(
            columns={
                "Cantidad_Negocios": "Cantidad Negocios",
                "Saldo_Contable": "Saldo contable",
                "Saldo_F351": "Saldo F351",
            }
        )
    )
    resumen_subcuentas = resumen_subcuentas[COLUMNAS_RESUMEN].sort_values(
        by="Subcuenta CUIF", ignore_index=True
    )

    # 8. Catalogo BASENEG
    baseneg = df_base_meta.rename(
        columns={
            "CÓDIGO SFC": "Código SFC",
            "CÓDIGO CONTABLE": "Código contable",
        }
    ).sort_values(
        by=["Código SFC", "Código contable"],
        ignore_index=True,
        kind="stable",
    )

    return ResultadoConciliacion(
        saldos=saldos_final,
        resumen_subcuentas=resumen_subcuentas,
        baseneg=baseneg,
    )
