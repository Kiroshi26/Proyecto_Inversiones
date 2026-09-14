import calendar
from dataclasses import dataclass
from datetime import date


MESES = {
    1: ("ENE", "ENERO"),
    2: ("FEB", "FEBRERO"),
    3: ("MAR", "MARZO"),
    4: ("ABR", "ABRIL"),
    5: ("MAY", "MAYO"),
    6: ("JUN", "JUNIO"),
    7: ("JUL", "JULIO"),
    8: ("AGO", "AGOSTO"),
    9: ("SEP", "SEPTIEMBRE"),
    10: ("OCT", "OCTUBRE"),
    11: ("NOV", "NOVIEMBRE"),
    12: ("DIC", "DICIEMBRE"),
}


class ErrorParametros(Exception):
    """Error relacionado con el año o mes del proceso."""


@dataclass(frozen=True)
class ParametrosProceso:
    anio: int
    mes: int
    abreviatura_mes: str
    nombre_mes: str
    mes_anterior: int
    abreviatura_mes_anterior: str
    mes_siguiente: int
    abreviatura_mes_siguiente: str
    ultimo_dia: int
    periodo: str
    fecha_corte: date


def crear_parametros(anio: int, mes: int) -> ParametrosProceso:
    """
    Valida el año y mes y calcula los parámetros derivados.
    """
    if not 2022 <= anio <= 2031:
        raise ErrorParametros(
            f"El año {anio} no está dentro del rango permitido: 2022 a 2031."
        )

    if mes not in MESES:
        raise ErrorParametros(
            f"El mes {mes} no es válido. Debe estar entre 1 y 12."
        )

    mes_anterior = 12 if mes == 1 else mes - 1
    mes_siguiente = 1 if mes == 12 else mes + 1

    ultimo_dia = calendar.monthrange(anio, mes)[1]

    abreviatura, nombre = MESES[mes]
    abreviatura_anterior = MESES[mes_anterior][0]
    abreviatura_siguiente = MESES[mes_siguiente][0]

    return ParametrosProceso(
        anio=anio,
        mes=mes,
        abreviatura_mes=abreviatura,
        nombre_mes=nombre,
        mes_anterior=mes_anterior,
        abreviatura_mes_anterior=abreviatura_anterior,
        mes_siguiente=mes_siguiente,
        abreviatura_mes_siguiente=abreviatura_siguiente,
        ultimo_dia=ultimo_dia,
        periodo=f"{anio}-{mes:02d}",
        fecha_corte=date(anio, mes, ultimo_dia),
    )