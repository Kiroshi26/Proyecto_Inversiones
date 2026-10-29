import unittest
from src.consultas import (
    ErrorConsulta,
    construir_consulta_saldos,
    construir_filtro_cuentas,
    obtener_columnas_hasta_mes,
)


class TestConsultas(unittest.TestCase):
    def test_obtener_columnas_hasta_mes(self):
        debitos, creditos = obtener_columnas_hasta_mes(3)
        self.assertEqual(len(debitos), 3)
        self.assertEqual(len(creditos), 3)
        self.assertEqual(debitos, ["ENDTER", "FEDTER", "MADTER"])
        self.assertEqual(creditos, ["ENCTER", "FECTER", "MACTER"])

    def test_filtro_cuentas_cubre_subcuentas(self):
        filtro = construir_filtro_cuentas("A")
        self.assertIn("A.CTATER LIKE '111505%'", filtro)
        self.assertIn("A.CTATER LIKE '111510%'", filtro)
        self.assertIn("A.CTATER LIKE '13%'", filtro)
        self.assertIn("A.CTATER LIKE '182705%'", filtro)
        self.assertIn("A.CTATER LIKE '821505%'", filtro)

    def test_construir_consulta_saldos(self):
        sql = construir_consulta_saldos(2026, 9)
        self.assertIn("FOPLIBNOR3.SCTATER", sql)
        self.assertIn("A.ANOTER = 2026", sql)
        self.assertIn("SEDTER", sql)
        self.assertIn("SECTER", sql)
        self.assertIn("TOTAL_MES", sql)

    def test_construir_consulta_invalida(self):
        with self.assertRaises(ErrorConsulta):
            construir_consulta_saldos(2015, 1)

        with self.assertRaises(ErrorConsulta):
            construir_consulta_saldos(2026, 0)


if __name__ == "__main__":
    unittest.main()
