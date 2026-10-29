import unittest
from src.parametros import (
    ErrorParametros,
    SUBCUENTAS_VALIDACION,
    crear_parametros,
    validar_periodo,
)


class TestParametros(unittest.TestCase):
    def test_subcuentas_oficiales_count(self):
        self.assertEqual(len(SUBCUENTAS_VALIDACION), 22)
        self.assertIn("111505", SUBCUENTAS_VALIDACION)
        self.assertIn("130205", SUBCUENTAS_VALIDACION)
        self.assertIn("182705", SUBCUENTAS_VALIDACION)
        self.assertIn("821505", SUBCUENTAS_VALIDACION)

    def test_crear_parametros_valido(self):
        p = crear_parametros(2026, 9)
        self.assertEqual(p.anio, 2026)
        self.assertEqual(p.mes, 9)
        self.assertEqual(p.periodo, "2026-09")
        self.assertEqual(p.fecha_corte, "20260930")

    def test_fecha_corte_febrero_bisiesto(self):
        p = crear_parametros(2024, 2)
        self.assertEqual(p.fecha_corte, "20240229")

        p2 = crear_parametros(2026, 2)
        self.assertEqual(p2.fecha_corte, "20260228")

    def test_validar_periodo_invalido(self):
        with self.assertRaises(ErrorParametros):
            validar_periodo(2015, 5)

        with self.assertRaises(ErrorParametros):
            validar_periodo(2026, 13)

        with self.assertRaises(ErrorParametros):
            validar_periodo("2026", 9)


if __name__ == "__main__":
    unittest.main()
