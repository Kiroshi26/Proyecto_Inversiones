from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import re


SUBCUENTAS_VALIDACION: List[str] = [
    "111505",
    "111510",
    "130105",
    "130110",
    "130115",
    "130120",
    "130205",
    "130210",
    "130305",
    "130315",
    "130405",
    "130505",
    "130905",
    "131605",
    "131705",
    "131715",
    "132105",
    "132205",
    "132310",
    "136000",
    "182705",
    "821505",
]


MESES: Dict[int, Tuple[str, str]] = {
    1: ("ENE", "Enero"),
    2: ("FEB", "Febrero"),
    3: ("MAR", "Marzo"),
    4: ("ABR", "Abril"),
    5: ("MAY", "Mayo"),
    6: ("JUN", "Junio"),
    7: ("JUL", "Julio"),
    8: ("AGO", "Agosto"),
    9: ("SEP", "Septiembre"),
    10: ("OCT", "Octubre"),
    11: ("NOV", "Noviembre"),
    12: ("DIC", "Diciembre"),
}


class ErrorParametros(Exception):
    """Error al validar los parametros de ejecucion."""


@dataclass
class ParametrosProceso:
    anio: int
    mes: int

    @property
    def periodo(self) -> str:
        return f"{self.anio}-{self.mes:02d}"

    @property
    def fecha_corte(self) -> str:
        dias_por_mes = {
            1: 31,
            2: (
                29
                if self.anio % 4 == 0
                and (
                    self.anio % 100 != 0
                    or self.anio % 400 == 0
                )
                else 28
            ),
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }

        ultimo_dia = dias_por_mes[self.mes]

        return (
            f"{self.anio}"
            f"{self.mes:02d}"
            f"{ultimo_dia:02d}"
        )


def validar_periodo(
    anio: int,
    mes: int,
) -> None:

    if (
        not isinstance(anio, int)
        or not isinstance(mes, int)
    ):
        raise ErrorParametros(
            "El anio y el mes deben ser enteros."
        )

    if not 2020 <= anio <= 2035:
        raise ErrorParametros(
            f"El anio {anio} se encuentra "
            "fuera de rango (2020-2035)."
        )

    if not 1 <= mes <= 12:
        raise ErrorParametros(
            f"El mes {mes} no es valido "
            "(debe estar entre 1 y 12)."
        )


def crear_parametros(
    anio: int,
    mes: int,
) -> ParametrosProceso:

    validar_periodo(anio, mes)

    return ParametrosProceso(
        anio=anio,
        mes=mes,
    )


def obtener_periodo_desde_f351(
    ruta_archivo: str,
) -> ParametrosProceso:
    """
    Extrae el periodo desde nombres como:

    Formato351_Fiduciaria_20251231.xlsx

    Resultado:
        anio = 2025
        mes = 12
    """

    nombre = Path(
        ruta_archivo
    ).name

    coincidencia = re.search(
        r"(\d{8})",
        nombre,
    )

    if not coincidencia:
        raise ErrorParametros(
            "No fue posible identificar la fecha "
            "en el nombre del archivo F351. "
            "Se esperaba un formato tipo "
            "Formato351_Fiduciaria_20251231.xlsx"
        )

    fecha = coincidencia.group(1)

    anio = int(fecha[:4])
    mes = int(fecha[4:6])

    validar_periodo(
        anio,
        mes,
    )

    return ParametrosProceso(
        anio=anio,
        mes=mes,
    )