import logging
from datetime import datetime
from pathlib import Path


def configurar_logger(carpeta_logs: Path) -> logging.Logger:
    """
    Crea un registro de ejecución en archivo y consola.
    """
    carpeta_logs.mkdir(parents=True, exist_ok=True)

    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_log = carpeta_logs / f"proceso_inversiones_{fecha_hora}.log"

    logger = logging.getLogger("proyecto_inversiones")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    manejador_archivo = logging.FileHandler(
        ruta_log,
        encoding="utf-8",
    )
    manejador_archivo.setFormatter(formato)

    manejador_consola = logging.StreamHandler()
    manejador_consola.setFormatter(formato)

    logger.addHandler(manejador_archivo)
    logger.addHandler(manejador_consola)

    logger.info("Archivo de log creado: %s", ruta_log)

    return logger
