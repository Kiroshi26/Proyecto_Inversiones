from src.configuracion import cargar_configuracion
from src.insumos import cargar_insumos
from src.procesamiento import preparar_insumos

config = cargar_configuracion()

insumos = cargar_insumos(config)

resultado = preparar_insumos(insumos)

print()
print("=" * 70)
print("BASE NEGOCIOS")
print("=" * 70)

print(resultado.base_negocios.head(20))

print()

print("Total registros:")
print(len(resultado.base_negocios))

print()

print("=" * 70)
print("FORMATO 351")
print("=" * 70)

print(resultado.formato_351.head(20))

print()

print("Total registros:")
print(len(resultado.formato_351))

print()

print("=" * 70)
print("CUENTAS TRANSMISION")
print("=" * 70)

print(resultado.cuentas_transmision.head(20))

print()

print("Total cuentas:")
print(len(resultado.cuentas_transmision))