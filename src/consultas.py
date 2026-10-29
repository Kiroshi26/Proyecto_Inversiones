from src.parametros import MESES, SUBCUENTAS_VALIDACION


class ErrorConsulta(Exception):
    """Error relacionado con la construccion de consultas SQL."""


COLUMNAS_MENSUALES = {
    1: ("ENDTER", "ENCTER"),
    2: ("FEDTER", "FECTER"),
    3: ("MADTER", "MACTER"),
    4: ("ABDTER", "ABCTER"),
    5: ("MYDTER", "MYCTER"),
    6: ("JUDTER", "JUCTER"),
    7: ("JLDTER", "JLCTER"),
    8: ("AGDTER", "AGCTER"),
    9: ("SEDTER", "SECTER"),
    10: ("OCDTER", "OCCTER"),
    11: ("NODTER", "NOCTER"),
    12: ("DIDTER", "DICTER"),
}


def validar_periodo_consulta(anio: int, mes: int) -> None:
    if not isinstance(anio, int) or not isinstance(mes, int):
        raise ErrorConsulta("El anio y el mes deben ser numeros enteros.")

    if not 2020 <= anio <= 2035:
        raise ErrorConsulta(f"El anio {anio} no esta permitido.")

    if mes not in COLUMNAS_MENSUALES:
        raise ErrorConsulta(f"El mes {mes} no esta configurado.")


def obtener_columnas_hasta_mes(mes: int):
    if mes not in COLUMNAS_MENSUALES:
        raise ErrorConsulta(f"El mes {mes} no esta configurado.")

    debitos = []
    creditos = []

    for numero_mes in range(1, mes + 1):
        debito, credito = COLUMNAS_MENSUALES[numero_mes]
        debitos.append(debito)
        creditos.append(credito)

    return debitos, creditos


def validar_nombre_columna(columna: str) -> str:
    nombre = str(columna).strip().upper()
    if not nombre:
        raise ErrorConsulta("Se encontro un nombre de columna vacio.")
    if not nombre.isalnum():
        raise ErrorConsulta(f"El nombre de columna contiene caracteres no permitidos: {nombre}")
    return nombre


def construir_suma(columnas, alias="A") -> str:
    if not columnas:
        return "0"
    expresiones = []
    for columna in columnas:
        nombre = validar_nombre_columna(columna)
        expresiones.append(f"{alias}.{nombre}")
    return " + ".join(expresiones)


def construir_movimiento_neto(debitos, creditos, alias="A") -> str:
    if len(debitos) != len(creditos):
        raise ErrorConsulta("La cantidad de columnas de debito y credito no coincide.")
    if not debitos:
        return "0"
    expresiones = []
    for debito, credito in zip(debitos, creditos):
        nombre_debito = validar_nombre_columna(debito)
        nombre_credito = validar_nombre_columna(credito)
        expresiones.append(f"({alias}.{nombre_debito} - {alias}.{nombre_credito})")
    return " + ".join(expresiones)


def construir_filtro_cuentas(alias="A") -> str:
    """Construye la condicion SQL para filtrar las cuentas contables."""
    # Cubre las 22 subcuentas definidas: disponible (111505, 111510), inversiones (13%),
    # activos fiduciarios (182705) y cuentas de orden (821505)
    return (
        f"({alias}.CTATER LIKE '111505%' OR {alias}.CTATER LIKE '111510%' OR "
        f"{alias}.CTATER LIKE '13%' OR {alias}.CTATER LIKE '182705%' OR {alias}.CTATER LIKE '821505%')"
    )


def construir_consulta_saldos(anio: int, mes: int) -> str:
    """
    Construye la consulta SQL de saldos contables en SCTATER para las subcuentas oficiales.
    """
    validar_periodo_consulta(anio, mes)

    debitos_acumulados, creditos_acumulados = obtener_columnas_hasta_mes(mes)
    debito_mes, credito_mes = COLUMNAS_MENSUALES[mes]
    debito_mes = validar_nombre_columna(debito_mes)
    credito_mes = validar_nombre_columna(credito_mes)

    if mes == 1:
        debitos_anteriores = []
        creditos_anteriores = []
    else:
        debitos_anteriores = debitos_acumulados[:-1]
        creditos_anteriores = creditos_acumulados[:-1]

    suma_debitos = construir_suma(debitos_acumulados)
    suma_creditos = construir_suma(creditos_acumulados)
    movimiento_acumulado = construir_movimiento_neto(debitos_acumulados, creditos_acumulados)
    movimiento_anterior = construir_movimiento_neto(debitos_anteriores, creditos_anteriores)

    if mes == 1:
        expresion_saldo_anterior = "A.INITER"
    else:
        expresion_saldo_anterior = f"A.INITER + {movimiento_anterior}"

    expresion_total_mes = f"A.INITER + {movimiento_acumulado}"
    filtro_cuentas = construir_filtro_cuentas(alias="A")

    consulta = f"""
SELECT
    A.ANOTER AS ANIO,
    A.CONTER AS CONTABILIDAD,
    A.CTATER AS CUENTA,
    A.INITER AS SALDO_INICIAL,
    ({suma_debitos}) AS DEBITOA,
    ({suma_creditos}) AS CREDITOA,
    ({expresion_total_mes}) AS SALDO_FINAL_ACUM,
    ({expresion_saldo_anterior}) AS SALDO_ANTERIOR,
    A.{debito_mes} AS DEBITOM,
    A.{credito_mes} AS CREDITOM,
    ({expresion_total_mes}) AS TOTAL_MES
FROM FOPLIBNOR3.SCTATER A
WHERE A.ANOTER = {anio}
    AND {filtro_cuentas}
    AND ({expresion_total_mes}) <> 0
""".strip()

    return consulta


def obtener_descripcion_consulta(anio: int, mes: int) -> str:
    validar_periodo_consulta(anio, mes)
    abreviatura, nombre = MESES[mes]
    return f"Consulta de saldos para {nombre} de {anio} ({abreviatura})"
