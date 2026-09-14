from contextlib import closing
from typing import List

import pandas as pd
import pyodbc

from src.validaciones import (
    validar_columnas,
    validar_dataframe_no_vacio,
)

COLUMNAS_SALDOS = [
    "ANIO",
    "CONTABILIDAD",
    "CUENTA",
    "SALDO_INICIAL",
    "DEBITOA",
    "CREDITOA",
    "SALDO_FINAL_ACUM",
    "SALDO_ANTERIOR",
    "DEBITOM",
    "CREDITOM",
    "TOTAL_MES",
]


class ErrorBaseDatos(Exception):
    """Error relacionado con la conexión o consulta a Nacional."""


def obtener_dsn_disponibles() -> List:
    """
    Devuelve los DSN visibles para la arquitectura actual de Python.
    """
    return sorted(pyodbc.dataSources().keys())


def dsn_disponible(nombre_dsn: str) -> bool:
    """
    Comprueba si un DSN está disponible para Python.
    """
    if not nombre_dsn:
        return False

    nombre_buscado = nombre_dsn.strip().upper()

    return any(
        nombre.strip().upper() == nombre_buscado for nombre in obtener_dsn_disponibles()
    )


def validar_dsn(nombre_dsn: str) -> None:
    """
    Genera un error controlado si el DSN no está disponible.
    """
    if not nombre_dsn or not nombre_dsn.strip():
        raise ErrorBaseDatos("El nombre del DSN está vacío.")

    if not dsn_disponible(nombre_dsn):
        disponibles = obtener_dsn_disponibles()

        lista_disponibles = ", ".join(disponibles) if disponibles else "ninguno"

        raise ErrorBaseDatos(
            f"El DSN '{nombre_dsn}' no está disponible para "
            f"esta instalación de Python. "
            f"DSN visibles: {lista_disponibles}. "
            "Solicita al área de tecnología que configure el DSN "
            "con la misma arquitectura de Python."
        )


def construir_cadena_conexion(
    nombre_dsn: str,
    usuario: str,
    clave: str,
) -> str:
    """
    Construye la cadena ODBC sin almacenar las credenciales.
    """
    if not nombre_dsn or not nombre_dsn.strip():
        raise ErrorBaseDatos("El nombre del DSN está vacío.")

    if not usuario or not usuario.strip():
        raise ErrorBaseDatos("El usuario de Nacional está vacío.")

    if not clave:
        raise ErrorBaseDatos("La contraseña de Nacional está vacía.")

    usuario_normalizado = usuario.strip().upper()

    return f"DSN={nombre_dsn.strip()};" f"UID={usuario_normalizado};" f"PWD={clave}"


def normalizar_saldos(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Valida y normaliza el resultado recibido desde Nacional.
    """
    validar_columnas(
        dataframe.columns,
        COLUMNAS_SALDOS,
        "Saldos de Nacional",
    )

    resultado = dataframe[COLUMNAS_SALDOS].copy()

    for columna in ["CONTABILIDAD", "CUENTA"]:
        resultado[columna] = (
            resultado[columna]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )

    columnas_numericas = [
        "ANIO",
        "SALDO_INICIAL",
        "DEBITOA",
        "CREDITOA",
        "SALDO_FINAL_ACUM",
        "SALDO_ANTERIOR",
        "DEBITOM",
        "CREDITOM",
        "TOTAL_MES",
    ]

    for columna in columnas_numericas:
        resultado[columna] = pd.to_numeric(
            resultado[columna],
            errors="coerce",
        ).fillna(0)

    resultado["ANIO"] = resultado["ANIO"].astype(int)

    validar_dataframe_no_vacio(
        len(resultado),
        "Saldos de Nacional",
    )

    return resultado


def ejecutar_consulta_saldos(
    nombre_dsn: str,
    usuario: str,
    clave: str,
    consulta: str,
    timeout_segundos: int = 120,
) -> pd.DataFrame:
    """
    Abre la conexión, ejecuta la consulta y garantiza el cierre.

    La contraseña permanece únicamente en memoria.
    """
    validar_dsn(nombre_dsn)

    if not consulta or not consulta.strip():
        raise ErrorBaseDatos("La consulta SQL está vacía.")

    cadena_conexion = construir_cadena_conexion(
        nombre_dsn=nombre_dsn,
        usuario=usuario,
        clave=clave,
    )

    try:
        with closing(
            pyodbc.connect(
                cadena_conexion,
                timeout=timeout_segundos,
            )
        ) as conexion:
            dataframe = pd.read_sql_query(
                consulta,
                conexion,
            )

    except pyodbc.Error as error:
        raise ErrorBaseDatos(
            "No fue posible conectarse o ejecutar la consulta "
            "en Nacional. Verifica el DSN, el usuario, la "
            "contraseña y el acceso a la red corporativa. "
            f"Detalle técnico: {error}"
        ) from error

    return normalizar_saldos(dataframe)
