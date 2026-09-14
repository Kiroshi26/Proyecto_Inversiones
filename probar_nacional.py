from src.consultas import construir_consulta_saldos

sql = construir_consulta_saldos(
    anio=2025,
    mes=12,
)

print(sql)