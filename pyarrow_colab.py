# Tutorial PyArrow en Google Colab
# Copia este código en celdas separadas de Colab

# ============================================
# CELDA 1: Verificar instalación
# ============================================
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd
import numpy as np

print(f"✅ PyArrow versión: {pa.__version__}")

# ============================================
# CELDA 2: Crear datos de ejemplo
# ============================================
# Crear un dataset de ventas
np.random.seed(42)

datos_ventas = {
    'fecha': pd.date_range('2025-01-01', periods=1000, freq='H'),
    'producto': np.random.choice(['Laptop', 'Mouse', 'Teclado', 'Monitor'], 1000),
    'cantidad': np.random.randint(1, 20, 1000),
    'precio': np.random.uniform(10, 1000, 1000).round(2),
    'region': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste'], 1000)
}

df = pd.DataFrame(datos_ventas)
print("📊 Dataset creado:")
print(df.head())
print(f"\nDimensiones: {df.shape}")

# ============================================
# CELDA 3: Convertir a PyArrow Table
# ============================================
tabla = pa.Table.from_pandas(df)

print("🔄 Tabla PyArrow:")
print(tabla)
print(f"\nSchema:")
print(tabla.schema)

# ============================================
# CELDA 4: Guardar en Parquet
# ============================================
# Guardar en formato Parquet
pq.write_table(tabla, 'ventas.parquet', compression='snappy')

# Verificar el tamaño del archivo
import os
tamaño_mb = os.path.getsize('ventas.parquet') / (1024 * 1024)
print(f"💾 Archivo guardado: ventas.parquet ({tamaño_mb:.2f} MB)")

# ============================================
# CELDA 5: Leer desde Parquet
# ============================================
tabla_leida = pq.read_table('ventas.parquet')
print("📖 Tabla leída desde Parquet:")
print(f"Filas: {tabla_leida.num_rows}")
print(f"Columnas: {tabla_leida.num_columns}")

# Leer solo algunas columnas
tabla_parcial = pq.read_table('ventas.parquet', columns=['producto', 'cantidad', 'precio'])
print(f"\n📋 Lectura parcial (solo 3 columnas): {tabla_parcial.column_names}")

# ============================================
# CELDA 6: Operaciones de filtrado
# ============================================
# Filtrar ventas de Laptops con cantidad > 10
mascara = pc.and_(
    pc.equal(tabla['producto'], 'Laptop'),
    pc.greater(tabla['cantidad'], 10)
)

ventas_filtradas = tabla.filter(mascara)
print(f"🔍 Ventas de Laptops con cantidad > 10: {ventas_filtradas.num_rows} registros")
print(ventas_filtradas.to_pandas().head())

# ============================================
# CELDA 7: Agregar columna calculada
# ============================================
# Calcular ingresos totales
ingresos = pc.multiply(tabla['cantidad'], tabla['precio'])
tabla_con_ingresos = tabla.append_column('ingresos', ingresos)

print("💰 Tabla con columna 'ingresos' agregada:")
print(tabla_con_ingresos.column_names)
print(tabla_con_ingresos.to_pandas().head())

# ============================================
# CELDA 8: Estadísticas y agregaciones
# ============================================
print("📈 Estadísticas de ventas:")
print(f"Total ingresos: ${pc.sum(ingresos).as_py():,.2f}")
print(f"Promedio ingresos: ${pc.mean(ingresos).as_py():,.2f}")
print(f"Mínimo: ${pc.min(ingresos).as_py():,.2f}")
print(f"Máximo: ${pc.max(ingresos).as_py():,.2f}")

# Contar ventas por producto
productos_unicos = pc.unique(tabla['producto'])
print(f"\nProductos únicos: {productos_unicos.to_pylist()}")

# ============================================
# CELDA 9: Trabajar con múltiples archivos
# ============================================
# Crear archivos particionados por región
for region in ['Norte', 'Sur', 'Este', 'Oeste']:
    mascara_region = pc.equal(tabla_con_ingresos['region'], region)
    tabla_region = tabla_con_ingresos.filter(mascara_region)
    pq.write_table(tabla_region, f'ventas_{region}.parquet')
    print(f"✅ Guardado: ventas_{region}.parquet ({tabla_region.num_rows} filas)")

# ============================================
# CELDA 10: Leer múltiples archivos con Dataset
# ============================================
import pyarrow.dataset as ds

# Leer todos los archivos de ventas
dataset = ds.dataset('.', format='parquet', 
                     partitioning='hive',
                     exclude_invalid_files=True)

print("\n📚 Dataset con múltiples archivos:")
print(f"Archivos encontrados: {len(list(dataset.get_fragments()))}")

# Consultar el dataset completo
tabla_completa = dataset.to_table()
print(f"Total de registros: {tabla_completa.num_rows}")

# ============================================
# CELDA 11: Análisis por región
# ============================================
print("\n🌎 Análisis por región:")

for region in ['Norte', 'Sur', 'Este', 'Oeste']:
    filtro = ds.field('region') == region
    tabla_region = dataset.to_table(filter=filtro)
    ingresos_region = pc.sum(tabla_region['ingresos'])
    print(f"{region}: {tabla_region.num_rows} ventas, ${ingresos_region.as_py():,.2f} ingresos")

# ============================================
# CELDA 12: Conversión a Pandas para visualización
# ============================================
# Convertir a Pandas para usar con matplotlib/seaborn
df_resultado = tabla_con_ingresos.to_pandas()

# Análisis por producto
resumen_productos = df_resultado.groupby('producto').agg({
    'cantidad': 'sum',
    'ingresos': 'sum'
}).round(2)

print("\n📊 Resumen por producto:")
print(resumen_productos)

# ============================================
# CELDA 13: Comparación de rendimiento
# ============================================
import time

# Crear un dataset más grande
datos_grandes = {
    'col1': np.random.randint(0, 1000, 100000),
    'col2': np.random.randn(100000),
    'col3': np.random.choice(['A', 'B', 'C', 'D'], 100000)
}

df_grande = pd.DataFrame(datos_grandes)
tabla_grande = pa.Table.from_pandas(df_grande)

# Guardar en Parquet
inicio = time.time()
pq.write_table(tabla_grande, 'grande.parquet', compression='snappy')
tiempo_parquet = time.time() - inicio

# Guardar en CSV
inicio = time.time()
df_grande.to_csv('grande.csv', index=False)
tiempo_csv = time.time() - inicio

print(f"⚡ Comparación de velocidad de escritura:")
print(f"Parquet: {tiempo_parquet:.3f} segundos")
print(f"CSV: {tiempo_csv:.3f} segundos")
print(f"Parquet es {tiempo_csv/tiempo_parquet:.1f}x más rápido")

# Comparar tamaños
tamaño_parquet = os.path.getsize('grande.parquet') / (1024 * 1024)
tamaño_csv = os.path.getsize('grande.csv') / (1024 * 1024)

print(f"\n💾 Comparación de tamaño:")
print(f"Parquet: {tamaño_parquet:.2f} MB")
print(f"CSV: {tamaño_csv:.2f} MB")
print(f"Parquet es {tamaño_csv/tamaño_parquet:.1f}x más pequeño")

# ============================================
# CELDA 14: Limpieza (opcional)
# ============================================
# Descomenta para limpiar archivos generados
# !rm -f *.parquet *.csv
# print("🧹 Archivos limpiados")