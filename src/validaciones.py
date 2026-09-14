from pathlib import Path
from typing import Iterable, Optional


class ErrorValidacion(Exception):
    """Error encontrado durante la validación del proceso."""


def validar_archivo(
    ruta: Path,
    extensiones_permitidas: Optional[Iterable[str]] = None,
) -> Path:
    """
    Comprueba que un archivo exista, sea accesible y tenga una extensión válida.
    """
    ruta = Path(ruta)

    if not ruta.exists():
        raise ErrorValidacion(f"No se encontró el archivo: {ruta}")

    if not ruta.is_file():
        raise ErrorValidacion(f"La ruta no corresponde a un archivo: {ruta}")

    if extensiones_permitidas:
        extensiones = {
            extension.lower()
            if extension.startswith(".")
            else f".{extension.lower()}"
            for extension in extensiones_permitidas
        }

        if ruta.suffix.lower() not in extensiones:
            raise ErrorValidacion(
                f"El archivo {ruta.name} tiene una extensión no permitida. "
                f"Extensiones esperadas: {sorted(extensiones)}"
            )

    try:
        with ruta.open("rb") as archivo:
            archivo.read(1)
    except OSError as error:
        raise ErrorValidacion(
            f"No fue posible leer el archivo {ruta}: {error}"
        ) from error

    return ruta


def validar_columnas(
    columnas_actuales: Iterable[str],
    columnas_requeridas: Iterable[str],
    nombre_fuente: str,
) -> None:
    """
    Comprueba que un DataFrame contenga las columnas requeridas.
    """
    actuales = {
        str(columna).strip()
        for columna in columnas_actuales
    }

    requeridas = {
        str(columna).strip()
        for columna in columnas_requeridas
    }

    faltantes = sorted(requeridas - actuales)

    if faltantes:
        raise ErrorValidacion(
            f"La fuente '{nombre_fuente}' no contiene estas columnas: "
            f"{', '.join(faltantes)}"
        )


def validar_dataframe_no_vacio(
    cantidad_filas: int,
    nombre_fuente: str,
) -> None:
    """
    Comprueba que una fuente haya producido al menos una fila.
    """
    if cantidad_filas <= 0:
        raise ErrorValidacion(
            f"La fuente '{nombre_fuente}' no contiene registros."
        )