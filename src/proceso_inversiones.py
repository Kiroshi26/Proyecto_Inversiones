from dataclasses import dataclass
from pathlib import Path

from src.base_datos import ejecutar_consulta_saldos
from src.conciliacion import ejecutar_conciliacion
from src.consultas import construir_consulta_saldos
from src.generador_saldos_inversiones import (
    generar_saldos_inversiones,
)
from src.parametros import ParametrosProceso
from src.procesamiento import ResultadoPreparacion


class ErrorProcesoInversiones(Exception):
    pass


@dataclass
class ResultadoProcesoInversiones:

    ruta_archivo: Path

    cantidad_saldos: int

    cantidad_baseneg: int

    total_mes: float


def consultar_nacional(
    configuracion: dict,
    parametros: ParametrosProceso,
    usuario: str,
    clave: str,
):

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
    configuracion: dict,
    parametros: ParametrosProceso,
    resultado_preparacion: ResultadoPreparacion,
    usuario: str,
    clave: str,
) -> ResultadoProcesoInversiones:

    saldos_nacional = consultar_nacional(
        configuracion=configuracion,
        parametros=parametros,
        usuario=usuario,
        clave=clave,
    )

    resultado_conciliacion = ejecutar_conciliacion(
        saldos_nacional=saldos_nacional,
        base_negocios=(resultado_preparacion.base_negocios),
        formato_351=(resultado_preparacion.formato_351),
    )

    carpeta_salida = Path(configuracion["rutas"]["datos_prueba"])

    ruta_archivo = generar_saldos_inversiones(
        resultado=resultado_conciliacion,
        carpeta_salida=carpeta_salida,
    )

    return ResultadoProcesoInversiones(
        ruta_archivo=ruta_archivo,
        cantidad_saldos=len(resultado_conciliacion.saldos),
        cantidad_baseneg=len(resultado_conciliacion.baseneg),
        total_mes=float(resultado_conciliacion.saldos["TOTAL_MES"].sum()),
    )
