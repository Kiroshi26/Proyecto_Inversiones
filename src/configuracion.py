from pathlib import Path
from typing import Any, Dict

import yaml


class ErrorConfiguracion(Exception):
    """
    Error relacionado con la configuracion del proyecto.
    """


def cargar_configuracion(
    ruta: str = "config.yaml",
) -> Dict[str, Any]:
    """
    Lee el archivo YAML de configuracion.
    """
    ruta_configuracion = Path(ruta)

    if not ruta_configuracion.exists():
        raise ErrorConfiguracion(
            "No se encontro el archivo de configuracion: "
            f"{ruta_configuracion.resolve()}"
        )

    if not ruta_configuracion.is_file():
        raise ErrorConfiguracion(
            "La ruta de configuracion no corresponde "
            f"a un archivo: {ruta_configuracion}"
        )

    try:
        with ruta_configuracion.open(
            "r",
            encoding="utf-8",
        ) as archivo:
            configuracion = yaml.safe_load(
                archivo
            )

    except yaml.YAMLError as error:
        raise ErrorConfiguracion(
            "El archivo config.yaml no es valido: "
            f"{error}"
        ) from error

    except OSError as error:
        raise ErrorConfiguracion(
            "No fue posible leer config.yaml: "
            f"{error}"
        ) from error

    if not isinstance(
        configuracion,
        dict,
    ):
        raise ErrorConfiguracion(
            "El archivo config.yaml esta vacio "
            "o no contiene una configuracion valida."
        )

    return configuracion


def validar_carpetas(
    configuracion: Dict[str, Any],
) -> Dict[str, Path]:
    """
    Valida y crea las carpetas locales utilizadas
    durante las pruebas.

    Esta funcion nunca crea carpetas en la red corporativa.
    """
    rutas_configuracion = configuracion.get(
        "rutas",
        {},
    )

    nombres_requeridos = [
        "insumos_prueba",
        "insumos_respaldo",
        "ejecuciones",
        "datos_prueba",
        "informes_prueba",
        "comparaciones",
        "respaldos",
        "logs",
    ]

    rutas_validadas: Dict[str, Path] = {}

    for nombre in nombres_requeridos:
        valor = rutas_configuracion.get(
            nombre
        )

        if not valor:
            raise ErrorConfiguracion(
                f"Falta configurar la ruta '{nombre}' "
                "en config.yaml."
            )

        ruta = Path(valor)

        try:
            ruta.mkdir(
                parents=True,
                exist_ok=True,
            )

        except OSError as error:
            raise ErrorConfiguracion(
                "No fue posible crear o acceder "
                f"a la carpeta local {ruta}: {error}"
            ) from error

        rutas_validadas[nombre] = ruta

    return rutas_validadas


def validar_modo_seguro(
    configuracion: Dict[str, Any],
) -> None:
    """
    Impide que una configuracion de pruebas permita
    publicar resultados en carpetas corporativas.
    """
    proyecto = configuracion.get(
        "proyecto",
        {},
    )

    modo = str(
        proyecto.get(
            "modo",
            "",
        )
    ).strip().lower()

    publicar = bool(
        proyecto.get(
            "publicar_resultados_corporativos",
            False,
        )
    )

    if modo != "pruebas":
        raise ErrorConfiguracion(
            "El proyecto debe permanecer en modo 'pruebas' "
            "hasta recibir aprobacion explicita."
        )

    if publicar:
        raise ErrorConfiguracion(
            "La publicacion corporativa esta bloqueada "
            "durante las pruebas. Configure "
            "'publicar_resultados_corporativos: false'."
        )


def validar_configuracion_red(
    configuracion: Dict[str, Any],
) -> Dict[str, Path]:
    """
    Obtiene y valida la configuracion de las carpetas
    corporativas de solo lectura.

    Esta funcion no crea ni modifica carpetas en la red.
    """
    rutas_red = configuracion.get(
        "rutas_red",
        {},
    )

    claves_requeridas = [
        "formato_351",
        "mapas_contables",
    ]

    rutas_validadas: Dict[str, Path] = {}

    for clave in claves_requeridas:
        valor = rutas_red.get(
            clave
        )

        if not valor:
            raise ErrorConfiguracion(
                "Falta configurar la ruta corporativa "
                f"'rutas_red.{clave}'."
            )

        ruta = Path(valor)

        if not ruta.exists():
            raise ErrorConfiguracion(
                "No se puede acceder a la carpeta "
                f"corporativa de solo lectura: {ruta}"
            )

        if not ruta.is_dir():
            raise ErrorConfiguracion(
                "La ruta corporativa no corresponde "
                f"a una carpeta: {ruta}"
            )

        rutas_validadas[clave] = ruta

    return rutas_validadas
