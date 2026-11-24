import unittest
import pandas as pd
from src.conciliacion import COLUMNAS_SALDOS, COLUMNAS_RESUMEN, ejecutar_conciliacion


class TestConciliacion(unittest.TestCase):
    def test_conciliacion_unificada_por_subcuentas(self):
        """
        Verifica que la logica de conciliacion unifique por subcuentas:
        Si un negocio posee multiples codigos contables con la misma subcuenta
        (ej. Tower One: 17285 y 99283 ambos con 130210), sus saldos contables se suman
        y forman una sola fila para esa subcuenta contra el saldo unico de F351.
        """
        df_optima = pd.DataFrame([
            {"CONTABILIDAD": "444", "CUENTA": "130205001", "TOTAL_MES": 255000278.26},
            {"CONTABILIDAD": "17285", "CUENTA": "130210001", "TOTAL_MES": 0.0},
            {"CONTABILIDAD": "99283", "CUENTA": "130210001", "TOTAL_MES": 7128013482.75},
            {"CONTABILIDAD": "13538", "CUENTA": "111505001", "TOTAL_MES": 15243830.86},
            {"CONTABILIDAD": "13538", "CUENTA": "130205001", "TOTAL_MES": 415571894702.47},
            {"CONTABILIDAD": "13538", "CUENTA": "136000001", "TOTAL_MES": 70695317495.19},
            {"CONTABILIDAD": "13538", "CUENTA": "182705001", "TOTAL_MES": 182813793202.16},
        ])

        df_base = pd.DataFrame([
            {
                "CÓDIGO SFC": "2529",
                "CÓDIGO CONTABLE": "444",
                "Grupo Óptima": "N/A",
                "Tipo": 4,
                "Subtipo": 1,
                "Nombre del negocio": "CIMPAC LTDA",
            },
            {
                "CÓDIGO SFC": "120967",
                "CÓDIGO CONTABLE": "17285",
                "Grupo Óptima": "BJ",
                "Tipo": 4,
                "Subtipo": 2,
                "Nombre del negocio": "PA PCF/ Tower one I",
            },
            {
                "CÓDIGO SFC": "120967",
                "CÓDIGO CONTABLE": "99283",
                "Grupo Óptima": "BJ",
                "Tipo": 4,
                "Subtipo": 2,
                "Nombre del negocio": "P.A. PCF/TOWER ONE I INVERSIÓN",
            },
            {
                "CÓDIGO SFC": "95754",
                "CÓDIGO CONTABLE": "13538",
                "Grupo Óptima": "3A",
                "Tipo": 9,
                "Subtipo": 7,
                "Nombre del negocio": "FCP CARTAMA",
            },
        ])

        df_f351 = pd.DataFrame([
            {"CÓDIGO SFC": "2529", "Subcuenta CUIF": "130205", "Saldo F351": 255000278.44},
            {"CÓDIGO SFC": "2529", "Subcuenta CUIF": "130505", "Saldo F351": 1000000.0},
            {"CÓDIGO SFC": "120967", "Subcuenta CUIF": "130210", "Saldo F351": 7128013482.46},
            {"CÓDIGO SFC": "95754", "Subcuenta CUIF": "111505", "Saldo F351": 15243830.86},
            {"CÓDIGO SFC": "95754", "Subcuenta CUIF": "130205", "Saldo F351": 415571894702.46},
            {"CÓDIGO SFC": "95754", "Subcuenta CUIF": "136000", "Saldo F351": 70695317495.19},
            {"CÓDIGO SFC": "95754", "Subcuenta CUIF": "182705", "Saldo F351": 182813793202.25},
        ])

        resultado = ejecutar_conciliacion(df_optima, df_base, df_f351)
        df_saldos = resultado.saldos
        df_resumen = resultado.resumen_subcuentas

        self.assertEqual(list(df_saldos.columns), COLUMNAS_SALDOS)
        self.assertEqual(list(df_resumen.columns), COLUMNAS_RESUMEN)

        # 1. Verificar Tower One (SFC 120967): debe ser UNA SOLA fila para 130210
        tower_rows = df_saldos[df_saldos["Código SFC"] == "120967"]
        self.assertEqual(len(tower_rows), 1)

        tower_row = tower_rows.iloc[0]
        self.assertEqual(tower_row["Subcuenta CUIF"], "130210")
        self.assertEqual(tower_row["Código contable"], "17285 / 99283")
        # El saldo contable sumado de 17285 (0) + 99283 (7,128,013,482.75)
        self.assertEqual(tower_row["Saldo contable"], 7128013482.75)
        self.assertEqual(tower_row["Saldo F351"], 7128013482.46)
        self.assertAlmostEqual(tower_row["Diferencias"], 0.29, places=2)

        # 2. Verificar CIMPAC 130205
        cimpac_130205 = df_saldos[
            (df_saldos["Código SFC"] == "2529") & (df_saldos["Subcuenta CUIF"] == "130205")
        ].iloc[0]
        self.assertEqual(cimpac_130205["Saldo contable"], 255000278.26)
        self.assertEqual(cimpac_130205["Saldo F351"], 255000278.44)
        self.assertAlmostEqual(cimpac_130205["Diferencias"], -0.18, places=2)

        # 3. Verificar CIMPAC 130505 (solo en F351)
        cimpac_130505 = df_saldos[
            (df_saldos["Código SFC"] == "2529") & (df_saldos["Subcuenta CUIF"] == "130505")
        ].iloc[0]
        self.assertEqual(cimpac_130505["Saldo contable"], 0.0)
        self.assertEqual(cimpac_130505["Saldo F351"], 1000000.0)
        self.assertEqual(cimpac_130505["Diferencias"], -1000000.0)

        # 4. Verificar Cartama (4 subcuentas distintas)
        cartama_rows = df_saldos[df_saldos["Código SFC"] == "95754"]
        self.assertEqual(len(cartama_rows), 4)

        # 5. Verificar hoja de Resumen por Subcuentas
        self.assertIn("130210", df_resumen["Subcuenta CUIF"].values)
        res_130210 = df_resumen[df_resumen["Subcuenta CUIF"] == "130210"].iloc[0]
        self.assertEqual(res_130210["Saldo contable"], 7128013482.75)
        self.assertEqual(res_130210["Saldo F351"], 7128013482.46)


if __name__ == "__main__":
    unittest.main()
