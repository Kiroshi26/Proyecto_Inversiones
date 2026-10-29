# Conciliación de Inversiones Fiduciarias

Sistema automatizado para la conciliación contable y regulatoria de inversiones fiduciarias entre el sistema contable **Óptima (Nacional - `SCTATER`)** y el **Formato 351 (`F_351_FIDUCIARIA`)** reportado a la Superintendencia Financiera de Colombia.

---

## 📁 Estructura del Proyecto

```text
Proyecto_Inversiones/
│
├── insumos/                                # Carpeta donde el usuario deposita los archivos mensuales
│   ├── BASE_NEGOCIOS_FIDUCIARIOS.xlsx      # Maestro de negocios con Grupo Óptima y Códigos SFC/Contables
│   └── Formato351_Fiduciaria_YYYYMMDD.xlsx # Reporte regulatorio F351 oficial
│
├── salidas/                                # Carpeta donde se genera el resultado final
│   └── Saldos_Inversiones.xlsx             # Archivo conciliado final (hojas SALDOS y BASENEG)
│
├── logs/                                   # Registros detallados de ejecución
│
├── src/                                    # Código fuente modular
│   ├── __init__.py
│   ├── base_datos.py                       # Conexión ODBC a Óptima/Nacional (DSN NACIONALET01)
│   ├── conciliacion.py                     # Motor de conciliación (Caso 1 y 2, 22 subcuentas, outer join)
│   ├── configuracion.py                    # Carga y validación de config.yaml
│   ├── consultas.py                        # Generación de consulta SQL optimizada para las 22 subcuentas
│   ├── credenciales.py                     # Captura segura de usuario y contraseña
│   ├── generador_saldos_inversiones.py     # Generador Excel con formato corporativo de 10 columnas
│   ├── insumos.py                          # Carga y normalización de insumos
│   ├── logger.py                           # Sistema de registro y logging
│   ├── parametros.py                       # Parámetros del periodo y catálogo de 22 subcuentas
│   ├── proceso_inversiones.py              # Orquestador del flujo
│   ├── validaciones.py                     # Validaciones de archivos y DataFrames
│   └── version.py                          # Control de versión
│
├── tests/                                  # Suite de pruebas unitarias automatizadas
│   ├── run_tests.py                        # Ejecutor de pruebas
│   ├── test_conciliacion.py
│   ├── test_consultas.py
│   ├── test_parametros.py
│   └── test_validaciones.py
│
├── config.yaml                             # Configuración general del proyecto
├── main.py                                 # Punto de entrada de la aplicación
├── requirements.txt                        # Librerías de Python requeridas
└── README.md                               # Documentación del sistema
```

---

## ⚙️ Reglas de Negocio y Lógica de Conciliación

El proceso opera bajo la especificación oficial de la **Hoja 3 (`Procedimiento`)**:

1. **Llave de Cruce:**
   - `BASE NEG FIDU` (`Código SFC`) $\longleftrightarrow$ `Formato F351` (`77 - Código del fideicomiso`).
   - `BASE NEG FIDU` (`Código Contable`) $\longleftrightarrow$ `Óptima / SCTATER` (`A.CONTER`).
2. **Subcuentas Oficiales Validadas (22 subcuentas):**
   - **Disponible / Equivalentes:** `111505`, `111510`.
   - **Inversiones (Clase 13):** `130105`, `130110`, `130115`, `130120`, `130205`, `130210`, `130305`, `130315`, `130405`, `130505`, `130905`, `131605`, `131705`, `131715`, `132105`, `132205`, `132310`, `136000`.
   - **Otras Inversiones / Bienes:** `182705`.
   - **Cuentas de Orden:** `821505`.
3. **Escenarios Operativos:**
   - **Caso 1 (Negocio Individual):** Cuando la columna `GRUPO OPTIMA` se encuentra vacía o `'N/A'`, se concilia el negocio por su propio `CÓDIGO CONTABLE`.
   - **Caso 2 (Negocios Agrupados por Grupo Óptima / Padre-Hijo):** Cuando el negocio cuenta con `GRUPO OPTIMA`, se concilian todos los códigos contables asociados al grupo y al fideicomiso (SFC), desglosando cada negocio y comparándolo contra el F351.
4. **Cruce Completo (*Outer Join*):**
   - Si una subcuenta existe en Óptima y F351: Calcula la diferencia real.
   - Si una subcuenta existe solo en Óptima: Saldo F351 = 0, Diferencia = Saldo Contable.
   - Si una subcuenta existe solo en F351: Saldo Contable = 0, Diferencia = -Saldo F351.
5. **Estructura Oficial del Reporte Final (`SALDOS`):**
   - `Código SFC`
   - `Código contable`
   - `Grupo Óptima`
   - `Tipo`
   - `Subtipo`
   - `Nombre del negocio`
   - `Subcuenta CUIF`
   - `Saldo contable`
   - `Saldo F351`
   - `Diferencias`

---

## 🚀 Uso del Sistema

### 1. Insumos Mensuales
Cada mes, deposita los dos archivos en la carpeta `insumos/`:
- `BASE_NEGOCIOS_FIDUCIARIOS.xlsx`
- `Formato351_Fiduciaria_YYYYMMDD.xlsx` (o `Formato351_Fiduciaria.xlsx`)

### 2. Ejecutar la Conciliación
Ejecuta en consola:
```powershell
python main.py
```
El sistema solicitará:
1. El **Año** (ej. `2026`).
2. El **Mes** (1 a 12, ej. `9`).
3. Tus credenciales de acceso a Óptima/Nacional (`Usuario` y `Contraseña`).

El reporte generado se guardará automáticamente en:
```text
salidas/Saldos_Inversiones.xlsx
```

### 3. Ejecutar Pruebas Automatizadas
Para verificar la integridad del sistema en cualquier momento:
```powershell
python tests/run_tests.py
```
