from pathlib import Path

import pandas as pd

carpeta = Path(
    r"C:\Proyectos\Proyecto_Inversiones\pruebas\ejecuciones\2025-12_20260914_085258"
)

print("=" * 70)
print("FORMATO 351")
print("=" * 70)

df351 = pd.read_excel(
    carpeta / "Formato351_Fiduciaria_20251231.xls",
    sheet_name="F_351_FIDUCIARIA",
    skiprows=3,
    usecols=[8, 36, 83],
    engine="xlrd",
)

print(df351.head())
print()
print(df351.columns)

print()
print("=" * 70)
print("NEGOCIOS VIGENTES")
print("=" * 70)

df_negocios = pd.read_excel(
    carpeta / "BASE MAPAS CONTABLES.xlsb",
    sheet_name="NEGOCIOS VIGENTES",
    usecols=[0, 3, 4],
    engine="pyxlsb",
)

print(df_negocios.head())
print()
print(df_negocios.columns)

print()
print("=" * 70)
print("CENTROS COSTOS")
print("=" * 70)

df_cc = pd.read_excel(
    carpeta / "BASE MAPAS CONTABLES CON CENTROS DE COSTOS.xlsx",
    sheet_name="CENTRO DE COSTOS ",
    usecols=[1, 4, 5],
    engine="openpyxl",
)

print(df_cc.head())
print()
print(df_cc.columns)