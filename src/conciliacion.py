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


def preparar_saldos_nacional(saldos_nacional: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza y filtra los saldos contables de Optima/Nacional para las 22 subcuentas oficiales.
    """
    if saldos_nacional.empty:
        raise ErrorConciliacion("No existen registros de saldos en Nacional/Optima.")

    df = saldos_nacional.copy()

    # Identificar columna contable y cuenta
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
    
    Aplica tanto el Caso 1 (negocios individuales) como el Caso 2 (negocios con Grupo Optima),
    realizando un cruce completo (outer join) para reflejar:
    - Negocios con movimientos en Optima y en F351.
    - Negocios con movimientos solo en Optima (Saldo F351 = 0).
    - Negocios con movimientos solo en F351 (Saldo contable = 0).
    """
    df_optima = preparar_saldos_nacional(saldos_nacional)
    df_base = base_negocios.copy()
    df_f351 = formato_351.copy()

    # Asegurar nombres consistentes en df_base
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
    # Nota: Si un Código SFC agrupa varios códigos contables (Caso 2), se asocia a cada uno.
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

    # 6. Rellenar nulos con 0.0 y calcular Diferencias
    resultado["Saldo contable"] = resultado["Saldo contable"].fillna(0.0)
    resultado["Saldo F351"] = resultado["Saldo F351"].fillna(0.0)
    resultado["Diferencias"] = resultado["Saldo contable"] - resultado["Saldo F351"]

    # 7. Renombrar columnas al estandar oficial si difieren y limpiar vacios
    resultado.rename(
        columns={
            "CÓDIGO SFC": "Código SFC",
            "CÓDIGO CONTABLE": "Código contable",
        },
        inplace=True,
    )
    resultado["Código SFC"] = resultado["Código SFC"].fillna("N/A").replace({"": "N/A"})
    resultado["Grupo Óptima"] = resultado["Grupo Óptima"].fillna("N/A").replace({"": "N/A"})

    # 8. Ordenar segun especificacion
    resultado.sort_values(
        by=["Código SFC", "Código contable", "Subcuenta CUIF"],
        inplace=True,
        ignore_index=True,
        kind="stable",
    )

    saldos_final = resultado[COLUMNAS_SALDOS].copy()

    # 9. Construir BASENEG (catalogo de negocios ordenado)
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

    return ResultadoConciliacion(saldos=saldos_final, baseneg=baseneg)
