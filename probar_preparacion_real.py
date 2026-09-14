from pathlib import Path

from src.insumos import (
    cargar_formato_351,
    cargar_negocios_vigentes,
    cargar_centros_costos,
)

from src.insumos import InsumosProceso

from src.procesamiento import preparar_insumos

carpeta = Path(
    r"C:\Proyectos\Proyecto_Inversiones\pruebas\ejecuciones\2025-12_20260914_085258"
)

insumos = InsumosProceso(
    formato_351=cargar_formato_351(
        carpeta / "Formato351_Fiduciaria_20251231.xls",
        "F_351_FIDUCIARIA",
    ),
    negocios_vigentes=cargar_negocios_vigentes(
        carpeta / "BASE MAPAS CONTABLES.xlsb",
        "NEGOCIOS VIGENTES",
    ),
    centros_costos=cargar_centros_costos(
        carpeta / "BASE MAPAS CONTABLES CON CENTROS DE COSTOS.xlsx",
        "CENTRO DE COSTOS ",
    ),
)

resultado = preparar_insumos(insumos)

print()
print("=" * 70)
print("BASE NEGOCIOS")
print("=" * 70)

print(resultado.base_negocios.head())

print()

print("TOTAL BASE NEGOCIOS")
print(len(resultado.base_negocios))

print()

print("=" * 70)
print("CUENTAS TRANSMISION")
print("=" * 70)

print(resultado.cuentas_transmision.head())

print()

print("TOTAL CUENTAS")
print(len(resultado.cuentas_transmision))

print()

print("=" * 70)
print("FORMATO 351")
print("=" * 70)

print(resultado.formato_351.head())

print()

print("TOTAL REGISTROS 351")
print(len(resultado.formato_351))