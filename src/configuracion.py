from pathlib import Path
from typing import Any, Dict
import yaml


class ErrorConfiguracion(Exception):
    """Error relacionado con la configuracion del proyecto."""


def cargar_configuracion(ruta: str = "config.yaml") -> Dict[str, Any]:
    """Lee el archivo YAML de configuracion."""
    ruta_configuracion = Path(ruta)

    if not ruta_configuracion.exists():
        raise ErrorConfiguracion(
            f"No se encontro el archivo de configuracion: {ruta_configuracion.resolve()}"
        )

    if not ruta_configuracion.is_file():
        raise ErrorConfiguracion(
            f"La ruta de configuracion no corresponde a un archivo: {ruta_configuracion}"
        )

    try:
        with ruta_configuracion.open("r", encoding="utf-8") as archivo:
            configuracion = yaml.safe_load(archivo)
    except yaml.YAMLError as error:
        raise ErrorConfiguracion(f"El archivo config.yaml no es valido: {error}") from error
    except OSError as error:
        raise ErrorConfiguracion(f"No fue posible leer config.yaml: {error}") from error

    if not isinstance(configuracion, dict):
        raise ErrorConfiguracion("El archivo config.yaml esta vacio o no contiene una configuracion valida.")

    return configuracion


def validar_carpetas(configuracion: Dict[str, Any]) -> Dict[str, Path]:
    """
    Valida y asegura la existencia de las carpetas locales del proyecto:
    insumos, salidas y logs.
    """
    rutas_configuracion = configuracion.get("rutas", {})
    carpetas_requeridas = ["insumos", "salidas", "logs"]

    rutas_validadas: Dict[str, Path] = {}

    for nombre in carpetas_requeridas:
        valor = rutas_configuracion.get(nombre)
        if not valor:
            # Fallback por defecto si no esta especificado
            valor = nombre

        ruta = Path(valor)
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ErrorConfiguracion(
                f"No fue posible crear o acceder a la carpeta local '{nombre}' ({ruta}): {error}"
            ) from error

        rutas_validadas[nombre] = ruta.resolve()

    proyecto_path = Path(rutas_configuracion.get("proyecto", "."))
    rutas_validadas["proyecto"] = proyecto_path.resolve()

    return rutas_validadas
