from getpass import getpass
from pathlib import Path

from src.consultas import construir_consulta_saldos
from src.base_datos import ejecutar_consulta_saldos

from src.insumos import (
    cargar_formato_351,
    cargar_negocios_vigentes,
    cargar_centros_costos,
    InsumosProceso,
)

from src.procesamiento import preparar_insumos

from src.conciliacion import (
    ejecutar_conciliacion,
)

from src.generador_saldos_inversiones import (
    generar_saldos_inversiones,
)

usuario = input(
    "Usuario Nacional: "
).strip().upper()

clave = getpass(
    "Contraseña: "
)

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

resultado_preparacion = preparar_insumos(
    insumos
)

sql = construir_consulta_saldos(
    anio=2025,
    mes=12,
)

saldos_nacional = ejecutar_consulta_saldos(
    nombre_dsn="NACIONALET01",
    usuario=usuario,
    clave=clave,
    consulta=sql,
)

resultado = ejecutar_conciliacion(
    saldos_nacional=saldos_nacional,
    base_negocios=resultado_preparacion.base_negocios,
    formato_351=resultado_preparacion.formato_351,
)

ruta = generar_saldos_inversiones(
    resultado,
    Path(
        r"C:\Proyectos\Proyecto_Inversiones\pruebas\datos"
    ),
)

print()
print("ARCHIVO GENERADO:")
print(ruta)