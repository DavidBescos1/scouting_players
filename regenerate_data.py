import os
import pandas as pd
import time
from sqlalchemy import create_engine
import numpy as np
import sys

# Añadir ruta actual al path para poder importar módulos locales
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importar funciones desde los archivos corregidos
from common.functions import convert_excel_to_parquet
from common.functions import create_sqlite_database

def regenerar_datos():
    """
    Regenera los archivos parquet y la base de datos desde cero
    """
    print("=== REGENERACIÓN DE DATOS ===")
    
    # Definir rutas
    excel_path = os.path.join('data', 'jugadores_formateados.xlsx')
    parquet_path = os.path.join('data', 'fbref_data.parquet')
    db_path = os.path.join('data', 'fbref_data.db')
    
    # Verificar si existe el archivo Excel
    if not os.path.exists(excel_path):
        print(f"ERROR: No se encontró el archivo {excel_path}")
        print("Por favor, coloca el archivo 'jugadores_formateados.xlsx' en la carpeta 'data'")
        return False
    
    # Eliminar los archivos existentes para forzar una conversión limpia
    if os.path.exists(parquet_path):
        os.remove(parquet_path)
        print(f"Archivo parquet existente eliminado: {parquet_path}")
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Archivo de base de datos existente eliminado: {db_path}")
    
    # Leer el Excel con los tipos correctos
    print(f"Leyendo Excel: {excel_path}")
    try:
        # Primero detectamos las columnas
        df_cols = pd.read_excel(excel_path, engine='openpyxl', nrows=0)
        columns = df_cols.columns.tolist()
        
        # Crear diccionario de tipos para las columnas de texto
        dtype_dict = {}
        for col in columns:
            if any(keyword in col.lower() for keyword in ['jugador', 'equipo', 'liga', 'nacionalidad', 'posición', 'position']):
                dtype_dict[col] = 'str'
        
        # Leer el Excel con los tipos específicos
        df = pd.read_excel(excel_path, engine='openpyxl', dtype=dtype_dict)
        
        # Verificar si existen las columnas críticas
        critical_columns = ['Nacionalidad', 'Posición']
        for col in critical_columns:
            if col in df.columns:
                # Asegurarse que sean texto
                df[col] = df[col].astype(str)
                # Reemplazar valores numéricos o null con vacío
                df[col] = df[col].replace(['0', '0.0', 'nan', 'None', 'NaN'], '')
                print(f"Columna {col} procesada. Ejemplos: {df[col].head(3).tolist()}")
            else:
                print(f"ADVERTENCIA: No se encontró la columna '{col}' en el Excel")
        
        # Guardar a Parquet
        print(f"Guardando a Parquet: {parquet_path}")
        df.to_parquet(parquet_path, index=False)
        
        # Crear base de datos SQLite
        print(f"Creando base de datos SQLite: {db_path}")
        engine = create_engine(f'sqlite:///{db_path}')
        df.to_sql('players_data', engine, if_exists='replace', index=False)
        
        print("\n¡REGENERACIÓN COMPLETADA CON ÉXITO!")
        return True
        
    except Exception as e:
        print(f"ERROR durante la regeneración: {e}")
        return False

if __name__ == "__main__":
    regenerar_datos()
    