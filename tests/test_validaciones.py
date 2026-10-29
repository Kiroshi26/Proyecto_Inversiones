import tempfile
import unittest
from pathlib import Path
from src.validaciones import (
    ErrorValidacion,
    validar_archivo,
    validar_columnas,
    validar_dataframe_no_vacio,
)


class TestValidaciones(unittest.TestCase):
    def test_validar_archivo_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "test.xlsx"
            archivo.write_text("dummy")
            res = validar_archivo(archivo, extensiones_permitidas=[".xlsx"])
            self.assertEqual(res, archivo)

    def test_validar_archivo_extension_invalida(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "test.txt"
            archivo.write_text("dummy")
            with self.assertRaises(ErrorValidacion):
                validar_archivo(archivo, extensiones_permitidas=[".xlsx"])

    def test_validar_columnas_ok(self):
        validar_columnas(["A", "B", "C"], ["A", "B"], "test")

    def test_validar_columnas_faltantes(self):
        with self.assertRaises(ErrorValidacion):
            validar_columnas(["A"], ["A", "B"], "test")

    def test_validar_dataframe_no_vacio(self):
        validar_dataframe_no_vacio(5, "test")
        with self.assertRaises(ErrorValidacion):
            validar_dataframe_no_vacio(0, "test")


if __name__ == "__main__":
    unittest.main()
