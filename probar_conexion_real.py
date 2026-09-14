from getpass import getpass

from src.base_datos import (
    ejecutar_consulta_saldos,
)

from src.consultas import (
    construir_consulta_saldos,
)

usuario = input(
    "Usuario Nacional: "
).strip().upper()

clave = getpass(
    "Contraseña: "
)

sql = construir_consulta_saldos(
    anio=2025,
    mes=12,
)

print()
print("Consultando Nacional...")
print()

resultado = ejecutar_consulta_saldos(
    nombre_dsn="NACIONALET01",
    usuario=usuario,
    clave=clave,
    consulta=sql,
)

print()

print("FILAS:")

print(len(resultado))

print()

print(resultado.head())