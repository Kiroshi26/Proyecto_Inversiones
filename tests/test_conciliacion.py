import unittest
import pandas as pd
from src.conciliacion import COLUMNAS_SALDOS, ejecutar_conciliacion


class TestConciliacion(unittest.TestCase):
    def test_conciliacion_casos_procedimiento(self):
        """
        Verifica que la logica de conciliacion reproduzca con precision los ejemplos
        de la Hoja 3 (Procedimiento): CIMPAC (Caso 1), Tower One y Cartama (Caso 2).
        """
        df_optima = pd.DataFrame([
            {"CONTABILIDAD": "444", "CUENTA": "130205001", "TOTAL_MES": 255000278.26},
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

        self.assertEqual(list(df_saldos.columns), COLUMNAS_SALDOS)

        # Verificar CIMPAC 130205
        cimpac_130205 = df_saldos[
            (df_saldos["Código SFC"] == "2529") & (df_saldos["Subcuenta CUIF"] == "130205")
        ].iloc[0]
        self.assertEqual(cimpac_130205["Saldo contable"], 255000278.26)
        self.assertEqual(cimpac_130205["Saldo F351"], 255000278.44)
        self.assertAlmostEqual(cimpac_130205["Diferencias"], -0.18, places=2)

        # Verificar CIMPAC 130505 (existe solo en F351, Saldo contable = 0)
        cimpac_130505 = df_saldos[
            (df_saldos["Código SFC"] == "2529") & (df_saldos["Subcuenta CUIF"] == "130505")
        ].iloc[0]
        self.assertEqual(cimpac_130505["Saldo contable"], 0.0)
        self.assertEqual(cimpac_130505["Saldo F351"], 1000000.0)
        self.assertEqual(cimpac_130505["Diferencias"], -1000000.0)

        # Verificar Tower One 17285 (Papa con saldo contable 0)
        tower_papa = df_saldos[
            (df_saldos["Código SFC"] == "120967") & (df_saldos["Código contable"] == "17285")
        ].iloc[0]
        self.assertEqual(tower_papa["Saldo contable"], 0.0)
        self.assertEqual(tower_papa["Saldo F351"], 7128013482.46)
        self.assertEqual(tower_papa["Diferencias"], -7128013482.46)

        # Verificar Tower One 99283 (Hijo con saldo)
        tower_hijo = df_saldos[
            (df_saldos["Código SFC"] == "120967") & (df_saldos["Código contable"] == "99283")
        ].iloc[0]
        self.assertEqual(tower_hijo["Saldo contable"], 7128013482.75)
        self.assertEqual(tower_hijo["Saldo F351"], 7128013482.46)
        self.assertAlmostEqual(tower_hijo["Diferencias"], 0.29, places=2)

        # Verificar Cartama 111505 (diferencia 0)
        cartama_disp = df_saldos[
            (df_saldos["Código SFC"] == "95754") & (df_saldos["Subcuenta CUIF"] == "111505")
        ].iloc[0]
        self.assertAlmostEqual(cartama_disp["Diferencias"], 0.0, places=2)


if __name__ == "__main__":
    unittest.main()
