import pandas as pd

saldos = pd.DataFrame(
    {
        "Código contable": ["100001", "100002"],
        "No. Super": ["3248", "3249"],
        "Nombre del Fideicomiso": ["FIDUCIA A", "FIDUCIA B"],
        "CTA_6DG": ["130505", "130510"],
        "TOTAL_MES": [1000000, 2000000],
        "Valor_351": [1000000, 1950000],
        "DIFERENCIA": [0, 50000],
    }
)

baseneg = pd.DataFrame(
    {
        "Nro. Super": ["3248", "3249"],
        "Código contable": ["100001", "100002"],
        "Nombre del Fideicomiso": ["FIDUCIA A", "FIDUCIA B"],
    }
)

with pd.ExcelWriter("Saldos_Inversiones.xlsx", engine="xlsxwriter") as writer:

    saldos.to_excel(
        writer,
        sheet_name="SALDOS",
        index=False,
    )

    baseneg.to_excel(
        writer,
        sheet_name="BASENEG",
        index=False,
    )

print("Archivo generado correctamente.")
