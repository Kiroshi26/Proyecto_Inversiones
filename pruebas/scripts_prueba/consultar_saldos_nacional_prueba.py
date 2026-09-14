import argparse
import getpass
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyodbc

from src.configuracion import (
    ErrorConfiguracion,
    cargar_configuracion,
    validar_carpetas,
    validar_modo_seguro,
)
from src.consultas import (
    ErrorConsulta,
    construir_consulta_saldos,
)
from src.parametros import (
    ErrorParametros,
    crear_parametros,
)

CARPETA_PROYECTO = Path(__file__).resolve().parent

RUTA_CONFIGURACION = CARPETA_PROYECTO / "config.yaml"

COLUMNAS_ESPERADAS = [
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

COLUMNAS_NUMERICAS = [
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

COLUMNAS_IDENTIFICADOR = [
    "CONTABILIDAD",
    "CUENTA",
]


class ErrorConsultaNacional(Exception):
    """
    Error controlado durante la consulta
    de saldos en Nacional.
    """


def leer_argumentos():
    """
    Lee el año y el mes enviados desde PowerShell.

    Ejemplo:
        python consultar_saldos_nacional_prueba.py
            --anio 2025 --mes 12
    """
    parser = argparse.ArgumentParser(
        description=(
            "Consulta saldos reales de Nacional " "y guarda el resultado localmente."
        )
    )

    parser.add_argument(
        "--anio",
        type=int,
        required=True,
        help="Año contable que se consultará.",
    )

    parser.add_argument(
        "--mes",
        type=int,
        required=True,
        help="Mes contable entre 1 y 12.",
    )

    return parser.parse_args()


def validar_dsn(nombre_dsn):
    """
    Comprueba que el DSN esté visible para Python.
    """
    fuentes = pyodbc.dataSources()

    coincidencias = {
        nombre.strip().upper(): controlador for nombre, controlador in fuentes.items()
    }

    nombre_normalizado = str(nombre_dsn).strip().upper()

    if nombre_normalizado not in coincidencias:
        disponibles = ", ".join(sorted(fuentes.keys()))

        raise ErrorConsultaNacional(
            f"El DSN '{nombre_dsn}' no está disponible. "
            f"DSN visibles: {disponibles or 'ninguno'}"
        )

    return coincidencias[nombre_normalizado]


def solicitar_credenciales():
    """
    Solicita las credenciales de iSeries.

    La contraseña no se muestra y no se guarda.
    """
    print()
    print("Ingrese las credenciales autorizadas de iSeries.")
    print("La contraseña no se mostrará ni se guardará.")
    print()

    usuario = input("Usuario de Nacional: ").strip().upper()

    clave = getpass.getpass("Contraseña de Nacional: ")

    if not usuario:
        raise ErrorConsultaNacional("El usuario de Nacional está vacío.")

    if not clave:
        raise ErrorConsultaNacional("La contraseña de Nacional está vacía.")

    return usuario, clave


def construir_cadena_conexion(
    nombre_dsn,
    usuario,
    clave,
):
    """
    Construye la cadena ODBC únicamente en memoria.
    """
    return f"DSN={nombre_dsn};" f"UID={usuario};" f"PWD={clave};"


def ejecutar_consulta(
    conexion,
    consulta,
):
    """
    Ejecuta la consulta mediante un cursor ODBC.

    No modifica información en Nacional.
    """
    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute(consulta)

        if cursor.description is None:
            raise ErrorConsultaNacional("La consulta no devolvió columnas.")

        columnas = [descripcion[0] for descripcion in cursor.description]

        filas = cursor.fetchall()

        datos = [tuple(fila) for fila in filas]

        dataframe = pd.DataFrame(
            datos,
            columns=columnas,
        )

        return dataframe

    except pyodbc.Error as error:
        raise ErrorConsultaNacional(
            "No fue posible ejecutar la consulta " f"contable. Detalle ODBC: {error}"
        ) from error

    finally:
        if cursor is not None:
            cursor.close()


def validar_columnas_resultado(
    dataframe,
):
    """
    Comprueba que Nacional haya devuelto
    todas las columnas esperadas.
    """
    columnas_actuales = {str(columna).strip().upper() for columna in dataframe.columns}

    columnas_faltantes = [
        columna for columna in COLUMNAS_ESPERADAS if columna not in columnas_actuales
    ]

    if columnas_faltantes:
        raise ErrorConsultaNacional(
            "La consulta no devolvió las columnas "
            "esperadas: " + ", ".join(columnas_faltantes)
        )


def normalizar_identificador(valor):
    """
    Conserva los códigos contables como texto.
    """
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

        if parte_entera.isdigit():
            return parte_entera

    return texto


def normalizar_resultado(
    dataframe,
):
    """
    Normaliza tipos de datos sin sumar,
    agrupar ni eliminar registros.
    """
    if dataframe.empty:
        raise ErrorConsultaNacional("La consulta no devolvió registros.")

    resultado = dataframe.copy()

    resultado.columns = [str(columna).strip().upper() for columna in resultado.columns]

    validar_columnas_resultado(resultado)

    resultado = resultado[COLUMNAS_ESPERADAS].copy()

    for columna in COLUMNAS_IDENTIFICADOR:
        resultado[columna] = resultado[columna].apply(normalizar_identificador)

    for columna in COLUMNAS_NUMERICAS:
        resultado[columna] = pd.to_numeric(
            resultado[columna],
            errors="coerce",
        ).fillna(0)

    resultado["ANIO"] = resultado["ANIO"].astype(int)

    cuentas_invalidas = ~resultado["CUENTA"].str.startswith("13")

    if cuentas_invalidas.any():
        cantidad = int(cuentas_invalidas.sum())

        raise ErrorConsultaNacional(
            "Nacional devolvió "
            f"{cantidad} registros cuya cuenta "
            "no comienza por 13."
        )

    return resultado


def construir_diagnostico(
    saldos,
    periodo,
    duracion_segundos,
):
    """
    Construye métricas de control de la consulta.
    """
    duplicados_clave = saldos.duplicated(
        subset=[
            "ANIO",
            "CONTABILIDAD",
            "CUENTA",
        ],
        keep=False,
    )

    cantidad_duplicados = int(duplicados_clave.sum())

    resumen = pd.DataFrame(
        [
            {
                "INDICADOR": "Periodo consultado",
                "VALOR": periodo,
            },
            {
                "INDICADOR": "Cantidad de registros",
                "VALOR": len(saldos),
            },
            {
                "INDICADOR": "Contabilidades únicas",
                "VALOR": saldos["CONTABILIDAD"].nunique(),
            },
            {
                "INDICADOR": "Cuentas únicas",
                "VALOR": saldos["CUENTA"].nunique(),
            },
            {
                "INDICADOR": ("Filas con clave contable repetida"),
                "VALOR": cantidad_duplicados,
            },
            {
                "INDICADOR": "Total saldo inicial",
                "VALOR": saldos["SALDO_INICIAL"].sum(),
            },
            {
                "INDICADOR": "Total débitos acumulados",
                "VALOR": saldos["DEBITOA"].sum(),
            },
            {
                "INDICADOR": "Total créditos acumulados",
                "VALOR": saldos["CREDITOA"].sum(),
            },
            {
                "INDICADOR": "Total saldo final acumulado",
                "VALOR": saldos["SALDO_FINAL_ACUM"].sum(),
            },
            {
                "INDICADOR": "Total saldo anterior",
                "VALOR": saldos["SALDO_ANTERIOR"].sum(),
            },
            {
                "INDICADOR": "Total débito del mes",
                "VALOR": saldos["DEBITOM"].sum(),
            },
            {
                "INDICADOR": "Total crédito del mes",
                "VALOR": saldos["CREDITOM"].sum(),
            },
            {
                "INDICADOR": "Total del mes",
                "VALOR": saldos["TOTAL_MES"].sum(),
            },
            {
                "INDICADOR": "Duración en segundos",
                "VALOR": round(
                    duracion_segundos,
                    2,
                ),
            },
        ]
    )

    if cantidad_duplicados > 0:
        duplicados = saldos.loc[duplicados_clave].copy()

        duplicados = duplicados.sort_values(
            by=[
                "CONTABILIDAD",
                "CUENTA",
            ],
            kind="stable",
            ignore_index=True,
        )

    else:
        duplicados = pd.DataFrame(columns=COLUMNAS_ESPERADAS)

    return resumen, duplicados


def guardar_consulta_sql(
    consulta,
    carpeta_salida,
    periodo,
):
    """
    Guarda localmente el SQL realmente ejecutado.
    """
    ruta_sql = carpeta_salida / f"Consulta_Saldos_{periodo}_PRUEBA.sql"

    ruta_sql.write_text(
        consulta,
        encoding="utf-8",
    )

    return ruta_sql


def guardar_resultado_excel(
    saldos,
    resumen,
    duplicados,
    carpeta_salida,
    periodo,
):
    """
    Guarda el resultado bruto y el diagnóstico
    en un archivo Excel local.
    """
    nombre_archivo = f"Saldos_Nacional_" f"{periodo}_BRUTO_PRUEBA.xlsx"

    ruta_salida = carpeta_salida / nombre_archivo

    if ruta_salida.exists():
        fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")

        ruta_salida = carpeta_salida / (
            f"Saldos_Nacional_" f"{periodo}_BRUTO_PRUEBA_" f"{fecha_hora}.xlsx"
        )

    try:
        with pd.ExcelWriter(
            ruta_salida,
            engine="xlsxwriter",
        ) as writer:
            saldos.to_excel(
                writer,
                sheet_name="SALDOS_BRUTOS",
                index=False,
            )

            resumen.to_excel(
                writer,
                sheet_name="RESUMEN",
                index=False,
            )

            duplicados.to_excel(
                writer,
                sheet_name="CLAVES_REPETIDAS",
                index=False,
            )

            libro = writer.book

            formato_monetario = libro.add_format(
                {"num_format": ("#,##0.00;[Red]-#,##0.00")}
            )

            formato_texto = libro.add_format(
                {
                    "num_format": "@",
                }
            )

            hoja_saldos = writer.sheets["SALDOS_BRUTOS"]

            hoja_saldos.freeze_panes(
                1,
                0,
            )

            hoja_saldos.autofilter(
                0,
                0,
                len(saldos),
                len(saldos.columns) - 1,
            )

            hoja_saldos.set_column(
                "A:A",
                12,
            )

            hoja_saldos.set_column(
                "B:C",
                18,
                formato_texto,
            )

            hoja_saldos.set_column(
                "D:K",
                22,
                formato_monetario,
            )

            hoja_resumen = writer.sheets["RESUMEN"]

            hoja_resumen.set_column(
                "A:A",
                40,
            )

            hoja_resumen.set_column(
                "B:B",
                25,
            )

            hoja_duplicados = writer.sheets["CLAVES_REPETIDAS"]

            hoja_duplicados.freeze_panes(
                1,
                0,
            )

            hoja_duplicados.set_column(
                "A:A",
                12,
            )

            hoja_duplicados.set_column(
                "B:C",
                18,
                formato_texto,
            )

            hoja_duplicados.set_column(
                "D:K",
                22,
                formato_monetario,
            )

    except PermissionError as error:
        raise ErrorConsultaNacional(
            "No fue posible guardar el resultado. "
            "Compruebe que el archivo no esté "
            "abierto en Excel."
        ) from error

    if not ruta_salida.exists():
        raise ErrorConsultaNacional("No se creó el archivo local " "de resultados.")

    if ruta_salida.stat().st_size == 0:
        raise ErrorConsultaNacional("El archivo local de resultados " "quedó vacío.")

    return ruta_salida


def main():
    """
    Ejecuta una consulta contable real y guarda
    el resultado exclusivamente de forma local.
    """
    usuario = None
    clave = None
    cadena_conexion = None
    conexion = None

    try:
        argumentos = leer_argumentos()

        configuracion = cargar_configuracion(str(RUTA_CONFIGURACION))

        validar_modo_seguro(configuracion)

        rutas = validar_carpetas(configuracion)

        parametros = crear_parametros(
            anio=argumentos.anio,
            mes=argumentos.mes,
        )

        configuracion_base = configuracion.get(
            "base_datos",
            {},
        )

        nombre_dsn = configuracion_base.get(
            "dsn",
            "NACIONALET01",
        )

        timeout_segundos = int(
            configuracion_base.get(
                "timeout_segundos",
                120,
            )
        )

        controlador = validar_dsn(nombre_dsn)

        consulta = construir_consulta_saldos(
            anio=parametros.anio,
            mes=parametros.mes,
        )

        print("=" * 70)
        print("CONSULTA REAL DE SALDOS DE INVERSIONES")
        print("=" * 70)
        print(f"Periodo: {parametros.periodo}")
        print(f"Fecha de corte: {parametros.fecha_corte}")
        print(f"DSN: {nombre_dsn}")
        print(f"Controlador: {controlador}")
        print()
        print("La consulta es de solo lectura.")
        print("El resultado se guardará únicamente " "en una carpeta local de pruebas.")
        print("No se publicará información en la red.")

        usuario, clave = solicitar_credenciales()

        cadena_conexion = construir_cadena_conexion(
            nombre_dsn=nombre_dsn,
            usuario=usuario,
            clave=clave,
        )

        print()
        print("Abriendo conexión...")

        conexion = pyodbc.connect(
            cadena_conexion,
            timeout=timeout_segundos,
        )

        print("Conexión abierta.")
        print("Ejecutando consulta contable...")

        inicio = time.perf_counter()

        saldos_brutos = ejecutar_consulta(
            conexion=conexion,
            consulta=consulta,
        )

        duracion = time.perf_counter() - inicio

        saldos = normalizar_resultado(saldos_brutos)

        resumen, duplicados = construir_diagnostico(
            saldos=saldos,
            periodo=parametros.periodo,
            duracion_segundos=duracion,
        )

        carpeta_salida = Path(rutas["datos_prueba"])

        ruta_sql = guardar_consulta_sql(
            consulta=consulta,
            carpeta_salida=carpeta_salida,
            periodo=parametros.periodo,
        )

        ruta_excel = guardar_resultado_excel(
            saldos=saldos,
            resumen=resumen,
            duplicados=duplicados,
            carpeta_salida=carpeta_salida,
            periodo=parametros.periodo,
        )

        print()
        print("=" * 70)
        print("CONSULTA TERMINADA CORRECTAMENTE")
        print("=" * 70)
        print(f"Registros recibidos: {len(saldos):,}")
        print(
            "Contabilidades únicas:",
            saldos["CONTABILIDAD"].nunique(),
        )
        print(
            "Cuentas únicas:",
            saldos["CUENTA"].nunique(),
        )
        print(
            "Filas con clave repetida:",
            len(duplicados),
        )
        print(
            "Total del mes:",
            f"{saldos['TOTAL_MES'].sum():,.2f}",
        )
        print(
            "Duración:",
            f"{duracion:,.2f} segundos",
        )
        print()
        print("Resultado local:")
        print(ruta_excel)
        print()
        print("Consulta SQL ejecutada:")
        print(ruta_sql)
        print()
        print("No se escribieron archivos " "en carpetas corporativas.")
        print("=" * 70)

        return 0

    except (
        ErrorConfiguracion,
        ErrorParametros,
        ErrorConsulta,
        ErrorConsultaNacional,
    ) as error:
        print()
        print("=" * 70)
        print("ERROR CONTROLADO")
        print("=" * 70)
        print(error)
        print("=" * 70)

        return 1

    except KeyboardInterrupt:
        print()
        print("Consulta cancelada por el usuario.")

        return 2

    except pyodbc.Error as error:
        print()
        print("=" * 70)
        print("ERROR ODBC")
        print("=" * 70)
        print(error)
        print("=" * 70)

        return 3

    except Exception as error:
        print()
        print("=" * 70)
        print("ERROR NO CONTROLADO")
        print("=" * 70)
        print(f"Tipo: {type(error).__name__}")
        print(f"Detalle: {error}")
        print()
        traceback.print_exc()
        print("=" * 70)

        return 4

    finally:
        if conexion is not None:
            conexion.close()

            print()
            print("Conexión cerrada correctamente.")

        usuario = None
        clave = None
        cadena_conexion = None


if __name__ == "__main__":
    raise SystemExit(main())
