import pandas as pd
import os
import time
from sqlalchemy import create_engine
import numpy as np

def convert_excel_to_parquet(excel_path, parquet_path):
    """
    Convierte un archivo Excel a formato Parquet preservando tipos de datos
    """
    print(f"Iniciando conversión de Excel a Parquet...")
    start_time = time.time()
    
    try:
        # Leer Excel con dtypes específicos para columnas importantes
        print(f"Leyendo archivo Excel desde {excel_path}...")
        
        # Primero leemos solo para obtener los nombres de las columnas
        df_cols = pd.read_excel(excel_path, engine='openpyxl', nrows=0)
        columns = df_cols.columns.tolist()
        print(f"Columnas en el archivo: {columns}")
        
        # Crear diccionario de tipos para forzar que ciertas columnas sean texto
        dtype_dict = {}
        text_column_keywords = ['jugador', 'equipo', 'liga', 'país', 'pais', 'player', 
                               'team', 'league', 'country', 'name', 'nombre', 
                               'posicion', 'posición', 'position', 'nacionalidad', 
                               'nationality']
        
        for col in columns:
            # Si la columna parece contener texto, la forzamos a string
            if any(keyword in col.lower() for keyword in text_column_keywords):
                dtype_dict[col] = 'str'
        
        # Añadir explícitamente Nacionalidad y Posición al dtype_dict si existen
        for specific_col in ['Nacionalidad', 'Posición', 'Posicion', 'Nationality', 'Position']:
            if specific_col in columns:
                dtype_dict[specific_col] = 'str'
        
        print(f"Columnas forzadas a tipo texto: {dtype_dict}")
        
        # Leer el Excel completo con los tipos especificados
        df = pd.read_excel(excel_path, engine='openpyxl', dtype=dtype_dict)
        
        print(f"Excel leído correctamente. Dimensiones: {df.shape}")
        
        # Preservar las columnas importantes como texto
        text_cols = []
        for col in df.columns:
            # Verificar si la columna parece contener texto
            if any(keyword in str(col).lower() for keyword in text_column_keywords):
                text_cols.append(col)
            # Añadir explícitamente las columnas específicas
            elif col in ['Nacionalidad', 'Posición', 'Posicion', 'Nationality', 'Position']:
                text_cols.append(col)
        
        print(f"Columnas de texto preservadas: {text_cols}")
        
        # Asegurarse de que Nacionalidad y Posición sean texto
        if 'Nacionalidad' in df.columns:
            df['Nacionalidad'] = df['Nacionalidad'].astype(str)
            # Reemplazar '0' o 'nan' por cadena vacía
            df['Nacionalidad'] = df['Nacionalidad'].replace(['0', '0.0', 'nan', 'None'], '')
            print(f"Valores de muestra en 'Nacionalidad': {df['Nacionalidad'].dropna().head(5).tolist()}")
        
        if 'Posición' in df.columns:
            df['Posición'] = df['Posición'].astype(str)
            # Reemplazar '0' o 'nan' por cadena vacía
            df['Posición'] = df['Posición'].replace(['0', '0.0', 'nan', 'None'], '')
            print(f"Valores de muestra en 'Posición': {df['Posición'].dropna().head(5).tolist()}")
            
        # Asegurarse de que player_name esté presente
        if 'Jugador' in df.columns and 'player_name' not in df.columns:
            df['player_name'] = df['Jugador']
            print("Creado campo 'player_name' a partir de 'Jugador'")
        
        # Solo convertir columnas numéricas, dejando las de texto intactas
        for col in df.columns:
            if col not in text_cols:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass  # Si no se puede convertir, dejarla como está
        
        # Reemplazar NaN con 0 solo en columnas numéricas
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Guardar como parquet preservando el schema
        print(f"Guardando archivo Parquet en {parquet_path}...")
        df.to_parquet(parquet_path, index=False)
        
        end_time = time.time()
        print(f"Conversión completada con éxito en {end_time - start_time:.2f} segundos!")
        print(f"Tamaño del archivo Excel: {os.path.getsize(excel_path) / (1024*1024):.2f} MB")
        print(f"Tamaño del archivo Parquet: {os.path.getsize(parquet_path) / (1024*1024):.2f} MB")
        
        return True, df
    except Exception as e:
        print(f"Error al convertir Excel a Parquet: {e}")
        return False, None

def create_sqlite_database(df, db_path):
    """
    Crea una base de datos SQLite a partir de un DataFrame
    """
    print(f"Iniciando creación de base de datos SQLite...")
    start_time = time.time()
    
    try:
        # Verificar tipos de datos para columnas específicas antes de guardar
        # Asegurarnos que Nacionalidad y Posición sean texto
        if 'Nacionalidad' in df.columns:
            df['Nacionalidad'] = df['Nacionalidad'].astype(str)
            df['Nacionalidad'] = df['Nacionalidad'].replace(['0', '0.0', 'nan', 'None'], '')
            
        if 'Posición' in df.columns:
            df['Posición'] = df['Posición'].astype(str)
            df['Posición'] = df['Posición'].replace(['0', '0.0', 'nan', 'None'], '')
            
        # Verificar tipos de datos antes de guardar
        print("Tipos de datos en el DataFrame:")
        for col, dtype in df.dtypes.items():
            print(f"{col}: {dtype}")
            
        # Crear conexión SQLite
        print(f"Creando conexión a SQLite en {db_path}...")
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Guardar a SQLite - usar método to_sql con tipos específicos si es necesario
        print("Guardando datos en tabla 'players_data'...")
        df.to_sql('players_data', engine, if_exists='replace', index=False)
        
        # Verificar que se guardó correctamente
        print("Verificando datos guardados en SQLite...")
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar columnas
        cursor.execute("PRAGMA table_info(players_data)")
        columns_info = cursor.fetchall()
        print("Columnas en la tabla SQLite:")
        for col_info in columns_info:
            print(f"{col_info[1]}: {col_info[2]}")
        
        # Verificar algunos datos
        if 'Nacionalidad' in df.columns:
            cursor.execute("SELECT DISTINCT Nacionalidad FROM players_data LIMIT 5")
            nacionalidades = cursor.fetchall()
            print(f"Muestra de nacionalidades: {nacionalidades}")
            
        if 'Posición' in df.columns:
            cursor.execute("SELECT DISTINCT Posición FROM players_data LIMIT 5")
            posiciones = cursor.fetchall()
            print(f"Muestra de posiciones: {posiciones}")
            
        conn.close()
        
        end_time = time.time()
        print(f"Base de datos SQLite creada con éxito en {end_time - start_time:.2f} segundos!")
        print(f"Tamaño de la base de datos: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
        
        return True
    except Exception as e:
        print(f"Error al crear base de datos SQLite: {e}")
        return False

if __name__ == "__main__":
    # Definir rutas
    excel_path = os.path.join('data', 'jugadores_formateados.xlsx')
    parquet_path = os.path.join('data', 'fbref_data.parquet')
    db_path = os.path.join('data', 'fbref_data.db')
    
    # Verificar si existe el archivo Excel
    if not os.path.exists(excel_path):
        print(f"ERROR: No se encontró el archivo {excel_path}")
        print("Por favor, coloca el archivo jugadores_formateados.xlsx en la carpeta 'data'")
        exit(1)
    
    # Preguntar si desea eliminar archivos existentes
    overwrite = input("¿Desea eliminar los archivos existentes y forzar una conversión limpia? (s/n): ")
    
    if overwrite.lower() == 's':
        # Eliminar los archivos existentes para forzar una conversión limpia
        if os.path.exists(parquet_path):
            os.remove(parquet_path)
            print(f"Archivo parquet existente eliminado: {parquet_path}")
        
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Archivo de base de datos existente eliminado: {db_path}")
    
    # Convertir Excel a Parquet
    success, df = convert_excel_to_parquet(excel_path, parquet_path)
    if not success:
        print("ERROR: No se pudo convertir el archivo Excel a Parquet")
        exit(1)
    
    # Crear base de datos SQLite
    success = create_sqlite_database(df, db_path)
    if not success:
        print("ERROR: No se pudo crear la base de datos SQLite")
        exit(1)
    
    print("\n¡CONVERSIÓN COMPLETADA EXITOSAMENTE!")
    print("Ahora puedes ejecutar la aplicación con 'streamlit run app.py'")