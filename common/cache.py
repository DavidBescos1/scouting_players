import streamlit as st
import pandas as pd
import os
import sqlite3
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join('models', '.env'))

# Función cacheada para cargar datos desde Parquet
@st.cache_data(ttl=3600)
def get_data():
    """
    Carga los datos del archivo Parquet o crea el archivo si no existe
    """
    excel_path = os.path.join('data', 'jugadores_formateados.xlsx')
    parquet_path = os.path.join('data', 'fbref_data.parquet')
    db_path = os.path.join('data', 'fbref_data.db')
    
    # Verificar si existe el archivo parquet
    if not os.path.exists(parquet_path):
        # Si no existe el parquet pero sí el Excel, convertirlo
        if os.path.exists(excel_path):
            from common.functions import convert_excel_to_parquet
            success = convert_excel_to_parquet(excel_path, parquet_path)
            if not success:
                st.error("No se pudo convertir el archivo Excel a Parquet.")
                return None
        else:
            st.error("No se encontró el archivo de datos. Por favor, sube un archivo Excel.")
            return None
    
    # Cargar desde parquet
    try:
        df = pd.read_parquet(parquet_path)
        
        # Asegurarse de que Nacionalidad y Posición sean tratados como texto
        text_columns = ['Nacionalidad', 'Posición', 'Posicion']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
                # Reemplazar valores numéricos o vacíos con cadena vacía
                df[col] = df[col].replace(['0', '0.0', 'nan', 'None'], '')
        
        return df
    except Exception as e:
        st.error(f"Error al cargar datos desde Parquet: {e}")
        return None

# Función cacheada para obtener conexión a base de datos
@st.cache_resource
def get_db_connection():
    """
    Obtiene una conexión a la base de datos SQLite, creándola si no existe
    """
    db_path = os.path.join('data', 'wyscout_data.db')
    excel_path = os.path.join('data', 'DATOS_WYSCOUT.xlsx')
    
    # Verificar si existe la base de datos
    if not os.path.exists(db_path):
        # Si no existe la DB pero sí el Excel, crearla
        if os.path.exists(excel_path):
            from common.functions import create_sqlite_database
            success = create_sqlite_database(excel_path, db_path)
            if not success:
                st.error("No se pudo crear la base de datos SQLite.")
                return None
        else:
            st.error("No se encontró el archivo de datos. Por favor, sube un archivo Excel.")
            return None
    
    # Conectar a la base de datos
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        return engine
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Función cacheada para consultar datos específicos de la base de datos
@st.cache_data(ttl=3600)
def query_database(sql_query):
    """
    Ejecuta una consulta SQL en la base de datos y devuelve los resultados
    """
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        df = pd.read_sql(sql_query, engine)
        return df
    except Exception as e:
        st.error(f"Error al ejecutar consulta: {e}")
        return None

# Función para limpiar y preparar datos
@st.cache_data
def prepare_player_data(df):
    """
    Limpia y prepara los datos de jugadores
    """
    # Asegurarse de que tenemos los datos correctos
    if df is None or df.empty:
        return None
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()
    
    # Mapear nombres de columnas comunes
    column_mapping = {
        'jugador': 'player_name',
        'equipo': 'equipo',
        'nombre_de_equipo': 'equipo',
        'team': 'equipo',
        'team_name': 'equipo',
        'pais': 'pais',
        'country': 'pais',
        'liga': 'liga',
        'league': 'liga',
        'nacionalidad': 'nacionalidad',
        'nationality': 'nacionalidad',
        'posición': 'posicion',
        'position': 'posicion'
    }
    
    # Renombrar columnas según el mapeo
    for original, new_name in column_mapping.items():
        if original in df.columns:
            df = df.rename(columns={original: new_name})
    
    # Si no existe player_name, crear una alternativa
    if 'player_name' not in df.columns:
        # Crear una columna con nombres genéricos
        df['player_name'] = [f'Jugador {i}' for i in range(len(df))]
    
    # Eliminar duplicados
    df = df.drop_duplicates(subset=['player_name'])
    
    # Tratar columnas de texto específicas
    text_columns = ['nacionalidad', 'posicion']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
            # Reemplazar valores numéricos o vacíos con cadena vacía
            df[col] = df[col].replace(['0', '0.0', 'nan', 'None'], '')
    
    # Reemplazar valores nulos por 0 en columnas numéricas
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

# Función para obtener lista de métricas disponibles
@st.cache_data
def get_metrics_list(df):
    """
    Devuelve la lista de métricas numéricas disponibles en el DataFrame
    """
    # Obtener columnas numéricas
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Excluir columnas que no son métricas (como ID, etc.)
    exclude_patterns = [
        'id', 'player_id', 'team_id', 'pais', 'liga', 'equipo', 'player_name',
        'jugador', 'posicion', 'posición', 'año nacimiento', 'minutos jugados',
        'año', 'nacimiento', 'minutos', 'jugados', 'nacionalidad'
    ]
    
    metrics = []
    for col in numeric_cols:
        # Verificar que la columna no incluye ninguno de los patrones a excluir
        if not any(pattern in col.lower() for pattern in exclude_patterns):
            metrics.append(col)
    
    return metrics
