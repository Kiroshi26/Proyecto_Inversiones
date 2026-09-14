import hashlib
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict


class ErrorInsumosRed(Exception):
    """
    Error relacionado con la lectura o copia
    de insumos desde la red corporativa.
    """


@dataclass
class ArchivoCopiado:
    """
    Informacion de trazabilidad de un archivo copiado.
    """

    nombre: str
    ruta_origen: Path
    ruta_destino: Path
    tamano_bytes: int
    fecha_modificacion_origen: datetime
    hash_sha256: str


@dataclass
class EjecucionLocal:
    """
    Informacion de la carpeta local congelada
    para una ejecucion.
    """

    periodo: str
    fecha_corte: date
    carpeta_ejecucion: Path
    formato_351: ArchivoCopiado
    mapas_contables: ArchivoCopiado
    mapas_centros_costos: ArchivoCopiado


def construir_nombre_formato_351(
    configuracion: Dict[str, Any],
    fecha_corte: date,
) -> str:
    """
    Construye el nombre exacto del Formato 351
    correspondiente a la fecha de corte.
    """
    archivos = configuracion.get(
        "archivos",
        {},
    )

    patron = archivos.get(
        "formato_351_patron"
    )

    if not patron:
        raise ErrorInsumosRed(
            "Falta configurar "
            "'archivos.formato_351_patron'."
        )

    fecha_texto = fecha_corte.strftime(
        "%Y%m%d"
    )

    try:
        nombre = patron.format(
            fecha_corte=fecha_texto
        )

    except (KeyError, ValueError) as error:
        raise ErrorInsumosRed(
            "El patron del Formato 351 no es valido. "
            "Debe contener '{fecha_corte}'."
        ) from error

    return nombre


def validar_archivo_origen(
    ruta: Path,
) -> None:
    """
    Valida un archivo de red sin modificarlo.
    """
    ruta = Path(ruta)

    if not ruta.exists():
        raise ErrorInsumosRed(
            f"No se encontro el archivo corporativo: {ruta}"
        )

    if not ruta.is_file():
        raise ErrorInsumosRed(
            "La ruta corporativa no corresponde "
            f"a un archivo: {ruta}"
        )

    if ruta.stat().st_size == 0:
        raise ErrorInsumosRed(
            f"El archivo corporativo esta vacio: {ruta}"
        )

    try:
        with ruta.open(
            "rb",
        ) as archivo:
            archivo.read(1)

    except OSError as error:
        raise ErrorInsumosRed(
            "No fue posible leer el archivo corporativo: "
            f"{ruta}. Detalle: {error}"
        ) from error


def calcular_hash_sha256(
    ruta: Path,
) -> str:
    """
    Calcula la huella SHA-256 de un archivo.

    La huella permite comprobar que la copia local
    es identica al archivo de red.
    """
    ruta = Path(ruta)
    hash_archivo = hashlib.sha256()

    try:
        with ruta.open(
            "rb",
        ) as archivo:
            while True:
                bloque = archivo.read(
                    1024 * 1024
                )

                if not bloque:
                    break

                hash_archivo.update(
                    bloque
                )

    except OSError as error:
        raise ErrorInsumosRed(
            "No fue posible calcular la huella "
            f"del archivo {ruta}: {error}"
        ) from error

    return hash_archivo.hexdigest()


def copiar_archivo_controlado(
    ruta_origen: Path,
    carpeta_destino: Path,
) -> ArchivoCopiado:
    """
    Copia un archivo de red a una carpeta local
    y verifica tamaño y huella SHA-256.
    """
    ruta_origen = Path(
        ruta_origen
    )

    carpeta_destino = Path(
        carpeta_destino
    )

    validar_archivo_origen(
        ruta_origen
    )

    carpeta_destino.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_destino = (
        carpeta_destino
        / ruta_origen.name
    )

    estadisticas_origen = ruta_origen.stat()
    hash_origen = calcular_hash_sha256(
        ruta_origen
    )

    try:
        shutil.copy2(
            ruta_origen,
            ruta_destino,
        )

    except PermissionError as error:
        raise ErrorInsumosRed(
            "No fue posible copiar el archivo a la "
            f"carpeta local: {ruta_destino}"
        ) from error

    except OSError as error:
        raise ErrorInsumosRed(
            "Ocurrio un error al copiar el archivo "
            f"{ruta_origen.name}: {error}"
        ) from error

    if not ruta_destino.exists():
        raise ErrorInsumosRed(
            f"No se creo la copia local: {ruta_destino}"
        )

    if ruta_destino.stat().st_size == 0:
        raise ErrorInsumosRed(
            f"La copia local quedo vacia: {ruta_destino}"
        )

    tamano_destino = ruta_destino.stat().st_size

    if tamano_destino != estadisticas_origen.st_size:
        raise ErrorInsumosRed(
            "La copia local no tiene el mismo tamaño "
            f"que el archivo de red: {ruta_origen.name}"
        )

    hash_destino = calcular_hash_sha256(
        ruta_destino
    )

    if hash_destino != hash_origen:
        raise ErrorInsumosRed(
            "La huella de la copia local no coincide "
            f"con el archivo de red: {ruta_origen.name}"
        )

    fecha_modificacion = datetime.fromtimestamp(
        estadisticas_origen.st_mtime
    )

    return ArchivoCopiado(
        nombre=ruta_origen.name,
        ruta_origen=ruta_origen,
        ruta_destino=ruta_destino,
        tamano_bytes=estadisticas_origen.st_size,
        fecha_modificacion_origen=fecha_modificacion,
        hash_sha256=hash_origen,
    )


def crear_carpeta_ejecucion(
    carpeta_base: Path,
    periodo: str,
) -> Path:
    """
    Crea una carpeta local única para una ejecución.
    """
    carpeta_base = Path(
        carpeta_base
    )

    fecha_hora = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    nombre_carpeta = (
        f"{periodo}_{fecha_hora}"
    )

    carpeta_ejecucion = (
        carpeta_base
        / nombre_carpeta
    )

    contador = 1

    while carpeta_ejecucion.exists():
        carpeta_ejecucion = (
            carpeta_base
            / f"{nombre_carpeta}_{contador}"
        )

        contador += 1

    carpeta_ejecucion.mkdir(
        parents=True,
        exist_ok=False,
    )

    return carpeta_ejecucion


def preparar_insumos_desde_red(
    configuracion: Dict[str, Any],
    rutas_red: Dict[str, Path],
    carpeta_ejecuciones: Path,
    fecha_corte: date,
) -> EjecucionLocal:
    """
    Localiza los tres archivos oficiales en la red,
    los copia a una carpeta local y valida cada copia.

    No crea, modifica ni elimina archivos en la red.
    """
    archivos = configuracion.get(
        "archivos",
        {},
    )

    nombre_formato_351 = construir_nombre_formato_351(
        configuracion=configuracion,
        fecha_corte=fecha_corte,
    )

    nombre_mapas = archivos.get(
        "mapas_contables"
    )

    nombre_centros = archivos.get(
        "mapas_centros_costos"
    )

    if not nombre_mapas:
        raise ErrorInsumosRed(
            "Falta configurar "
            "'archivos.mapas_contables'."
        )

    if not nombre_centros:
        raise ErrorInsumosRed(
            "Falta configurar "
            "'archivos.mapas_centros_costos'."
        )

    ruta_formato_351 = (
        rutas_red["formato_351"]
        / nombre_formato_351
    )

    ruta_mapas = (
        rutas_red["mapas_contables"]
        / nombre_mapas
    )

    ruta_centros = (
        rutas_red["mapas_contables"]
        / nombre_centros
    )

    periodo = fecha_corte.strftime(
        "%Y-%m"
    )

    carpeta_ejecucion = crear_carpeta_ejecucion(
        carpeta_base=carpeta_ejecuciones,
        periodo=periodo,
    )

    try:
        formato_351 = copiar_archivo_controlado(
            ruta_origen=ruta_formato_351,
            carpeta_destino=carpeta_ejecucion,
        )

        mapas_contables = copiar_archivo_controlado(
            ruta_origen=ruta_mapas,
            carpeta_destino=carpeta_ejecucion,
        )

        mapas_centros_costos = copiar_archivo_controlado(
            ruta_origen=ruta_centros,
            carpeta_destino=carpeta_ejecucion,
        )

    except Exception:
        shutil.rmtree(
            carpeta_ejecucion,
            ignore_errors=True,
        )

        raise

    return EjecucionLocal(
        periodo=periodo,
        fecha_corte=fecha_corte,
        carpeta_ejecucion=carpeta_ejecucion,
        formato_351=formato_351,
        mapas_contables=mapas_contables,
        mapas_centros_costos=mapas_centros_costos,
    )