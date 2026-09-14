from src.configuracion import cargar_configuracion
from src.insumos import cargar_insumos
from src.procesamiento import preparar_insumos

config = cargar_configuracion()

insumos = cargar_insumos(config)

resultado = preparar_insumos(insumos)

print(resultado.base_negocios.head())
print(resultado.formato_351.head())