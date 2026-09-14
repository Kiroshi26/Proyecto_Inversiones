from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.validaciones import (
    ErrorValidacion,
    validar_archivo,
    validar_columnas,
    validar_dataframe_no_vacio,
)


@dataclass
class InsumosProceso:
    formato_351: pd.DataFrame
    negocios_vigentes: pd.DataFrame
    centros_costos: pd.DataFrame


def construir_rutas_insumos(
    configuracion: Dict[str, Any],
) -> Dict[str, Path]:
    """
    Construye las rutas locales de los insumos de prueba.
    """
    carpeta_insumos = Path(
        configuracion["rutas"]["insumos_prueba"]
    )

    archivos = configuracion["archivos"]

    return {
        "formato_351": carpeta_insumos / archivos["formato_351"],
        "mapas_contables": (
            carpeta_insumos / archivos["mapas_contables"]
        ),
        "mapas_centros_costos": (
            carpeta_insumos / archivos["mapas_centros_costos"]
        ),
    }


def validar_insumos_disponibles(
    configuracion: Dict[str, Any],
) -> Dict[str, Path]:
    """
    Comprueba que existan los tres archivos requeridos.
    """
    rutas = construir_rutas_insumos(configuracion)

    validar_archivo(
        rutas["formato_351"],
        extensiones_permitidas=[".xls"],
    )

    validar_archivo(
        rutas["mapas_contables"],
        extensiones_permitidas=[".xlsb"],
    )

    validar_archivo(
        rutas["mapas_centros_costos"],
        extensiones_permitidas=[".xlsx"],
    )

    return rutas


def cargar_formato_351(
    ruta: Path,
    nombre_hoja: str,
) -> pd.DataFrame:
    """
    Lee y prepara el Formato 351.
    """
    dataframe = pd.read_excel(
        ruta,
        sheet_name=nombre_hoja,
        skiprows=3,
        usecols=[8, 36, 83],
        engine="xlrd",
    )

    columnas_requeridas = [
        "2 - Código Catalogo Único de Informción Financiera",
        "77 - Código del fideicomiso",
        "30 - Vr. razonable o valor presente en $",
    ]

    validar_columnas(
        dataframe.columns,
        columnas_requeridas,
        "Formato 351",
    )

    dataframe = dataframe.rename(
        columns={
            "2 - Código Catalogo Único de Informción Financiera": (
                "Cta_Con351"
            ),
            "77 - Código del fideicomiso": "No. Sup351",
            "30 - Vr. razonable o valor presente en $": "Valor_351",
        }
    )

    dataframe = dataframe[
        dataframe["Cta_Con351"]
        .astype(str)
        .str.startswith("13")
    ].copy()

    dataframe["Valor_351"] = pd.to_numeric(
        dataframe["Valor_351"],
        errors="coerce",
    ).fillna(0)

    dataframe = (
        dataframe
        .groupby(
            ["Cta_Con351", "No. Sup351"],
            dropna=False,
            as_index=False,
        )["Valor_351"]
        .sum()
    )

    validar_dataframe_no_vacio(
        len(dataframe),
        "Formato 351 filtrado por cuentas 13",
    )

    return dataframe


def cargar_negocios_vigentes(
    ruta: Path,
    nombre_hoja: str,
) -> pd.DataFrame:
    """
    Lee los negocios vigentes de la Base de Mapas Contables.
    """
    dataframe = pd.read_excel(
        ruta,
        sheet_name=nombre_hoja,
        usecols=[0, 3, 4],
        engine="pyxlsb",
    )

    validar_dataframe_no_vacio(
        len(dataframe),
        "Negocios vigentes",
    )

    return dataframe


def cargar_centros_costos(
    ruta: Path,
    nombre_hoja: str,
) -> pd.DataFrame:
    """
    Lee los centros de costos.
    """
    dataframe = pd.read_excel(
        ruta,
        sheet_name=nombre_hoja,
        usecols=[1, 4, 5],
        engine="openpyxl",
    )

    validar_dataframe_no_vacio(
        len(dataframe),
        "Centros de costos",
    )

    return dataframe


def cargar_insumos(
    configuracion: Dict[str, Any],
) -> InsumosProceso:
    """
    Valida y carga todos los insumos de Excel.
    """
    rutas = validar_insumos_disponibles(configuracion)
    hojas = configuracion["hojas"]

    formato_351 = cargar_formato_351(
        ruta=rutas["formato_351"],
        nombre_hoja=hojas["formato_351"],
    )

    negocios_vigentes = cargar_negocios_vigentes(
        ruta=rutas["mapas_contables"],
        nombre_hoja=hojas["negocios_vigentes"],
    )

    centros_costos = cargar_centros_costos(
        ruta=rutas["mapas_centros_costos"],
        nombre_hoja=hojas["centros_costos"],
    )

    return InsumosProceso(
        formato_351=formato_351,
        negocios_vigentes=negocios_vigentes,
        centros_costos=centros_costos,
    )