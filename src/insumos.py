from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import glob

import pandas as pd

from src.parametros import SUBCUENTAS_VALIDACION
from src.validaciones import (
    ErrorValidacion,
    validar_archivo,
    validar_dataframe_no_vacio,
)


@dataclass
class InsumosProceso:
    base_negocios: pd.DataFrame
    formato_351: pd.DataFrame


def normalizar_identificador(valor: Any) -> str:
    """
    Normaliza codigos numericos o alfanumericos eliminando decimales y espacios.
    Ejemplo: 2529.0 -> '2529', ' 444 ' -> '444', None -> ''
    """
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.lower() in {"nan", "none", "nat", "[null]"}:
        return ""
    if texto.endswith(".0"):
        parte_entera = texto[:-2]
        if parte_entera.replace("-", "", 1).isdigit():
            texto = parte_entera
    return texto


def localizar_archivo(
    carpeta: Path,
    nombre_o_patron: str,
    carpeta_alternativa: Optional[Path] = None,
) -> Path:
    """
    Busca un archivo por nombre exacto o patron glob en la carpeta principal
    o alternativa.
    """
    # 1. Buscar coincidencia exacta en carpeta principal
    ruta_directa = carpeta / nombre_o_patron
    if ruta_directa.exists() and ruta_directa.is_file():
        return ruta_directa

    # 2. Buscar por patron glob en carpeta principal
    coincidencias = sorted(carpeta.glob(nombre_o_patron))
    if coincidencias:
        return coincidencias[-1]  # La mas reciente por orden alfabetico

    # 3. Intentar en carpeta alternativa (ej. raiz del proyecto)
    if carpeta_alternativa and carpeta_alternativa.exists():
        ruta_alt = carpeta_alternativa / nombre_o_patron
        if ruta_alt.exists() and ruta_alt.is_file():
            return ruta_alt
        coincidencias_alt = sorted(carpeta_alternativa.glob(nombre_o_patron))
        if coincidencias_alt:
            return coincidencias_alt[-1]

    raise ErrorValidacion(
        f"No se encontro ningun archivo que coincida con '{nombre_o_patron}' "
        f"en la carpeta '{carpeta}'."
    )


def cargar_base_negocios(
    ruta: Path,
    nombre_hoja: str = "BASE NEG FIDU",
) -> pd.DataFrame:
    """
    Carga y normaliza el catalogo de negocios fiduciarios desde BASE_NEGOCIOS_FIDUCIARIOS.xlsx.
    """
    validar_archivo(ruta, extensiones_permitidas=[".xlsx", ".xlsm"])

    df = pd.read_excel(ruta, sheet_name=nombre_hoja)
    validar_dataframe_no_vacio(len(df), f"Base Negocios Fiduciarios ({nombre_hoja})")

    # Mapeo flexible de columnas para evitar fallos por tildes o variaciones leves
    col_map = {}
    for c in df.columns:
        c_str = str(c).strip().upper()
        if "SFC" in c_str and "PRINCIPAL" not in c_str and "COMPARTIMENTO" not in c_str:
            col_map["sfc"] = c
        elif "CONTABLE" in c_str and "PLANTILLA" not in c_str:
            col_map["contable"] = c
        elif "GRUPO" in c_str and "OPTIMA" in c_str:
            col_map["grupo_optima"] = c
        elif c_str == "TIPO":
            col_map["tipo"] = c
        elif c_str == "SUBTIPO":
            col_map["subtipo"] = c
        elif "NOMBRE" in c_str and "NEGOCIO" in c_str:
            col_map["nombre"] = c
        elif c_str == "ESTADO":
            col_map["estado"] = c
        elif c_str == "TRANSMITE":
            col_map["transmite"] = c
        elif "PAP" in c_str and "HIJO" in c_str:
            col_map["papa_hijo"] = c

    requeridos = ["sfc", "contable", "nombre"]
    for req in requeridos:
        if req not in col_map:
            raise ErrorValidacion(f"Falta la columna obligatoria '{req}' en la hoja '{nombre_hoja}'.")

    resultado = pd.DataFrame()
    resultado["CÓDIGO SFC"] = df[col_map["sfc"]].apply(normalizar_identificador)
    resultado["CÓDIGO CONTABLE"] = df[col_map["contable"]].apply(normalizar_identificador)
    
    if "grupo_optima" in col_map:
        resultado["Grupo Óptima"] = (
            df[col_map["grupo_optima"]]
            .fillna("N/A")
            .astype(str)
            .str.strip()
            .replace({"": "N/A", "None": "N/A", "nan": "N/A", "NAN": "N/A"})
        )
    else:
        resultado["Grupo Óptima"] = "N/A"

    resultado["Tipo"] = df[col_map["tipo"]].fillna(0).astype(int) if "tipo" in col_map else 0
    resultado["Subtipo"] = df[col_map["subtipo"]].fillna(0).astype(int) if "subtipo" in col_map else 0
    resultado["Nombre del negocio"] = df[col_map["nombre"]].fillna("").astype(str).str.strip()
    resultado["Estado"] = df[col_map["estado"]].fillna("").astype(str).str.strip() if "estado" in col_map else ""
    resultado["Transmite"] = df[col_map["transmite"]].fillna("").astype(str).str.strip() if "transmite" in col_map else ""
    resultado["Papá / Hijo"] = df[col_map["papa_hijo"]].fillna("").astype(str).str.strip() if "papa_hijo" in col_map else ""

    # Filtrar negocios que cuenten con Codigo Contable
    resultado = resultado[resultado["CÓDIGO CONTABLE"] != ""].copy()
    resultado = resultado.drop_duplicates(subset=["CÓDIGO SFC", "CÓDIGO CONTABLE"]).reset_index(drop=True)

    validar_dataframe_no_vacio(len(resultado), "Base Negocios normalizada")
    return resultado


def cargar_formato_351(
    ruta: Path,
    nombre_hoja: str = "F_351_FIDUCIARIA",
) -> pd.DataFrame:
    """
    Carga y normaliza el reporte regulatorio Formato 351, filtrando por las 22 subcuentas oficiales.
    """
    validar_archivo(ruta, extensiones_permitidas=[".xlsx", ".xls", ".xlsm"])

    df = pd.read_excel(ruta, sheet_name=nombre_hoja, skiprows=3)
    validar_dataframe_no_vacio(len(df), f"Formato 351 ({nombre_hoja})")

    # Mapeo flexible de columnas de F351
    col_sfc = None
    col_cuif = None
    col_valor = None

    for c in df.columns:
        c_str = str(c).strip()
        if c_str.startswith("77 -") or c_str.startswith("77-"):
            col_sfc = c
        elif c_str.startswith("2 -") or c_str.startswith("2-"):
            col_cuif = c
        elif c_str.startswith("30 -") or c_str.startswith("30-"):
            col_valor = c

    if not col_sfc or not col_cuif or not col_valor:
        raise ErrorValidacion(
            "El archivo Formato 351 no contiene las columnas requeridas: "
            "'77 - Código del fideicomiso', '2 - CUIF', '30 - Vr. razonable en $'."
        )

    datos = pd.DataFrame()
    datos["CÓDIGO SFC"] = df[col_sfc].apply(normalizar_identificador)
    datos["Subcuenta CUIF"] = df[col_cuif].apply(normalizar_identificador).str[:6]
    datos["Saldo F351"] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0.0)

    # Filtrar por las 22 subcuentas oficiales
    datos = datos[datos["Subcuenta CUIF"].isin(SUBCUENTAS_VALIDACION)].copy()
    datos = datos[datos["CÓDIGO SFC"] != ""].copy()

    # Agrupar suma por (CÓDIGO SFC, Subcuenta CUIF)
    agrupado = (
        datos.groupby(["CÓDIGO SFC", "Subcuenta CUIF"], as_index=False)["Saldo F351"]
        .sum()
    )

    validar_dataframe_no_vacio(len(agrupado), "Formato 351 filtrado por subcuentas de validacion")
    return agrupado


def cargar_insumos(
    configuracion: Dict[str, Any],
    rutas_insumos: Optional[Dict[str, Path]] = None,
) -> InsumosProceso:
    """
    Carga todos los insumos necesarios para la conciliacion.
    """
    rutas_cfg = configuracion.get("rutas", {})
    carpeta_insumos = Path(rutas_cfg.get("insumos", "insumos"))
    carpeta_raiz = Path(rutas_cfg.get("proyecto", "."))
    archivos_cfg = configuracion.get("archivos", {})
    hojas_cfg = configuracion.get("hojas", {})

    if rutas_insumos:
        ruta_base = rutas_insumos["base_negocios"]
        ruta_f351 = rutas_insumos["formato_351"]
    else:
        patron_base = archivos_cfg.get("base_negocios", "BASE_NEGOCIOS_FIDUCIARIOS.xlsx")
        patron_f351 = archivos_cfg.get("formato_351_patron", "Formato351_Fiduciaria*.xlsx")

        ruta_base = localizar_archivo(carpeta_insumos, patron_base, carpeta_raiz)
        ruta_f351 = localizar_archivo(carpeta_insumos, patron_f351, carpeta_raiz)

    hoja_base = hojas_cfg.get("base_negocios", "BASE NEG FIDU")
    hoja_f351 = hojas_cfg.get("formato_351", "F_351_FIDUCIARIA")

    df_base = cargar_base_negocios(ruta_base, nombre_hoja=hoja_base)
    df_f351 = cargar_formato_351(ruta_f351, nombre_hoja=hoja_f351)

    return InsumosProceso(base_negocios=df_base, formato_351=df_f351)
