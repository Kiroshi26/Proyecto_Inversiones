import getpass


class ErrorCredenciales(Exception):
    pass


def solicitar_credenciales():

    usuario = input("Usuario Nacional: ").strip().upper()

    clave = getpass.getpass("Contraseña Nacional: ")

    if not usuario:

        raise ErrorCredenciales("Usuario vacío.")

    if not clave:

        raise ErrorCredenciales("Contraseña vacía.")

    return usuario, clave
