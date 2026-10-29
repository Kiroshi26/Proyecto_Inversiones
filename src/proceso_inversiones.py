from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.base_datos import ejecutar_consulta_saldos
from src.conciliacion import ResultadoConciliacion, ejecutar_conciliacion
from src.consultas import construir_consulta_saldos
from src.generador_saldos_inversiones import generar_saldos_inversiones
from src.insumos import InsumosProceso
from src.parametros import ParametrosProceso


class ErrorProcesoInversiones(Exception):
    """Error general durante el flujo del proceso de inversiones."""


@dataclass
class ResultadoProcesoInversiones:
    ruta_archivo: Path
    cantidad_saldos: int
    cantidad_baseneg: int
    total_saldo_contable: float
    total_saldo_f351: float
    total_diferencias: float
    registros_con_diferencia: int


def consultar_nacional(
    configuracion: Dict[str, Any],
    parametros: ParametrosProceso,
    usuario: str,
    clave: str,
) -> pd.DataFrame:
    """
    Ejecuta la consulta en la base de datos Optima (Nacional) para el periodo indicado.
    """
    configuracion_bd = configuracion.get("base_datos", {})
    dsn = configuracion_bd.get("dsn", "NACIONALET01")
    timeout = int(configuracion_bd.get("timeout_segundos", 120))

    sql = construir_consulta_saldos(
        anio=parametros.anio,
        mes=parametros.mes,
    )

    return ejecutar_consulta_saldos(
        nombre_dsn=dsn,
        usuario=usuario,
        clave=clave,
        consulta=sql,
        timeout_segundos=timeout,
    )


def ejecutar_proceso_inversiones(
    configuracion: Dict[str, Any],
    parametros: ParametrosProceso,
    insumos: InsumosProceso,
    usuario: str,
    clave: str,
    saldos_nacional_override: pd.DataFrame = None,
) -> ResultadoProcesoInversiones:
    """
    Orquesta el flujo principal: consulta a Optima, conciliacion y reporte en Excel.
    Permite `saldos_nacional_override` para pruebas sin conexion activa a base de datos.
    """
    if saldos_nacional_override is not None:
        saldos_nacional = saldos_nacional_override
    else:
        saldos_nacional = consultar_nacional(
            configuracion=configuracion,
            parametros=parametros,
            usuario=usuario,
            clave=clave,
        )

    resultado_conciliacion = ejecutar_conciliacion(
        saldos_nacional=saldos_nacional,
        base_negocios=insumos.base_negocios,
        formato_351=insumos.formato_351,
    )

    rutas_cfg = configuracion.get("rutas", {})
    carpeta_salida = Path(rutas_cfg.get("salidas", "salidas"))
    archivos_salida = configuracion.get("salidas", {})
    nombre_archivo = archivos_salida.get("archivo_resultado", "Saldos_Inversiones.xlsx")

    ruta_archivo = generar_saldos_inversiones(
        resultado=resultado_conciliacion,
        carpeta_salida=carpeta_salida,
        nombre_archivo=nombre_archivo,
    )

    df_saldos = resultado_conciliacion.saldos
    total_contable = float(df_saldos["Saldo contable"].sum())
    total_f351 = float(df_saldos["Saldo F351"].sum())
    total_dif = float(df_saldos["Diferencias"].sum())
    con_dif = int((df_saldos["Diferencias"].abs() > 0.01).sum())

    return ResultadoProcesoInversiones(
        ruta_archivo=ruta_archivo,
        cantidad_saldos=len(df_saldos),
        cantidad_baseneg=len(resultado_conciliacion.baseneg),
        total_saldo_contable=total_contable,
        total_saldo_f351=total_f351,
        total_diferencias=total_dif,
        registros_con_diferencia=con_dif,
    )
