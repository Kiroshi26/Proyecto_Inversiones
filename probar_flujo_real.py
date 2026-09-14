from src.configuracion import cargar_configuracion
from src.insumos import cargar_insumos
from src.procesamiento import preparar_insumos

print("Cargando configuración...")

config = cargar_configuracion()

print("Leyendo insumos...")

insumos = cargar_insumos(config)

print("Preparando insumos...")

resultado = preparar_insumos(insumos)

print()
print("=" * 70)

print("BASE NEGOCIOS")

print("=" * 70)

print(resultado.base_negocios.head(20))

print()

print("=" * 70)

print("FORMATO 351")

print("=" * 70)

print(resultado.formato_351.head(20))

print()

print("=" * 70)

print("RESUMEN")

print("=" * 70)

print(
    "Base Negocios:",
    len(resultado.base_negocios)
)

print(
    "Formato 351:",
    len(resultado.formato_351)
)

print(
    "Cuentas transmisión:",
    len(resultado.cuentas_transmision)
)