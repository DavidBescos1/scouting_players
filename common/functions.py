import pandas as pd
import numpy as np
import streamlit as st
import os
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import base64
from common.cache import get_data, get_db_connection
try:
    # Imports para PDF mejorado
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from PIL import Image as PILImage
    import tempfile
except ImportError:
    # Si reportlab no está disponible, se usará el método básico con FPDF
    pass

def truncate_text(text, max_length=15):
    """
    Trunca un texto a una longitud máxima añadiendo puntos suspensivos
    """
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

# Función para convertir Excel a parquet
def convert_excel_to_parquet(excel_path, parquet_path):
    """
    Convierte un archivo Excel a formato Parquet para reducir tamaño y mejorar rendimiento
    """
    try:
        # Leer Excel - para archivos grandes usamos chunks
        print(f"Leyendo archivo Excel desde {excel_path}...")
        
        # Primero leemos solo para obtener los nombres de las columnas
        df_cols = pd.read_excel(excel_path, engine='openpyxl', nrows=0)
        columns = df_cols.columns.tolist()
        print(f"Columnas en el archivo: {columns}")
        
        # Crear diccionario de tipos para forzar que ciertas columnas sean texto
        dtype_dict = {}
        for col in columns:
            # Si la columna parece contener texto, la forzamos a string
            if any(keyword in col.lower() for keyword in ['jugador', 'equipo', 'liga', 'país', 'pais', 'player', 'team', 'league', 'country', 'name', 'nombre']):
                dtype_dict[col] = 'str'
        
        # Leer el Excel completo con los tipos especificados
        df = pd.read_excel(excel_path, engine='openpyxl', dtype=dtype_dict)
        
        # Preservar las columnas importantes
        text_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['jugador', 'equipo', 'liga', 'país', 'pais', 'player', 'team', 'league', 'country', 'name', 'nombre'])]
        
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
        df.to_parquet(parquet_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error al convertir Excel a Parquet: {e}")
        return False

# Función para convertir Excel a SQLite
def create_sqlite_database(excel_path, db_path):
    """
    Crea una base de datos SQLite a partir de un archivo Excel
    """
    try:
        import sqlite3
        from sqlalchemy import create_engine
        
        # Leer Excel con tipos específicos
        print(f"Leyendo archivo Excel desde {excel_path}...")
        
        # Primero leemos solo para obtener los nombres de las columnas
        df_cols = pd.read_excel(excel_path, engine='openpyxl', nrows=0)
        columns = df_cols.columns.tolist()
        
        # Crear diccionario de tipos para forzar que ciertas columnas sean texto
        dtype_dict = {}
        for col in columns:
            # Si la columna parece contener texto, la forzamos a string
            if any(keyword in col.lower() for keyword in ['jugador', 'equipo', 'liga', 'país', 'pais', 'player', 'team', 'league', 'country', 'name', 'nombre']):
                dtype_dict[col] = 'str'
        
        # Leer el Excel completo con los tipos especificados
        df = pd.read_excel(excel_path, engine='openpyxl', dtype=dtype_dict)
        
        # Preservar las columnas importantes
        text_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['jugador', 'equipo', 'liga', 'país', 'pais', 'player', 'team', 'league', 'country', 'name', 'nombre'])]
        
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
        
        # Crear conexión SQLite
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Guardar DataFrame en SQLite
        df.to_sql('players_data', engine, if_exists='replace', index=False)
        
        return True
    except Exception as e:
        st.error(f"Error al crear base de datos SQLite: {e}")
        return False

# Función para generar gráfico radar para comparar jugadores
def create_radar_chart(df, players, metrics):
    """
    Crea un gráfico radar para comparar jugadores basado en métricas seleccionadas
    """
    # Filtrar datos
    filtered_df = df[df['player_name'].isin(players)]
    
    # Preparar datos para el radar
    categories = metrics
    fig = go.Figure()
    
    # Crear escala para normalizar valores
    scaler = MinMaxScaler()
    
    # Preparar datos para escalar
    scale_data = df[metrics].copy()
    scaled_values = scaler.fit_transform(scale_data)
    scaled_df = pd.DataFrame(scaled_values, columns=metrics)
    
    # Añadir información del jugador
    scaled_df['player_name'] = df['player_name'].values
    
    # Añadir cada jugador al radar
    for player in players:
        player_data = scaled_df[scaled_df['player_name'] == player]
        if not player_data.empty:
            values = player_data[metrics].values.flatten().tolist()
            # Cerrar el polígono repitiendo el primer valor
            values.append(values[0])
            categories_with_first = categories + [categories[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories_with_first,
                fill='toself',
                name=player
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Comparación de Jugadores",
        height=600,
        width=800
    )
    
    return fig

# Función para encontrar jugadores similares
def find_similar_players(df, player_name, metrics, top_n=10, filters=None):
    """
    Encuentra jugadores similares basados en métricas seleccionadas
    
    Parámetros:
    - df: DataFrame con datos de jugadores
    - player_name: Nombre del jugador base
    - metrics: Lista de métricas para comparar
    - top_n: Número de jugadores similares a devolver
    - filters: Diccionario con filtros adicionales (opcional)
      Soporta: liga, equipo, posición y birth_year_range como tupla (min_year, max_year)
    """
    # Filtrar métricas relevantes
    features_df = df[metrics].copy()
    
    # Normalizar datos
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features_df)
    
    # Calcular similitud de coseno
    similarity_matrix = cosine_similarity(scaled_features)
    
    # Obtener índice del jugador
    player_index = df[df['player_name'] == player_name].index[0]
    
    # Obtener similitudes con el jugador seleccionado
    player_similarities = similarity_matrix[player_index]
    
    # Crear DataFrame con similitudes
    similarity_df = pd.DataFrame({
        'player_name': df['player_name'],
        'similarity_score': player_similarities
    })
    
    # Aplicar filtros adicionales si se proporcionan
    filtered_df = similarity_df.copy()
    
    if filters is not None:
        for col, value in filters.items():
            # Filtro para rango de año de nacimiento
            if col == 'birth_year_range':
                birth_min, birth_max = value
                
                # Buscar la columna de año de nacimiento
                birth_column = None
                for potential_col in df.columns:
                    if 'año nacimiento' in potential_col.lower() or 'nacimiento' in potential_col.lower() or 'birth' in potential_col.lower():
                        birth_column = potential_col
                        break
                
                if birth_column:
                    # Obtener jugadores dentro del rango de años de nacimiento
                    valid_players = df[(df[birth_column] >= birth_min) & 
                                     (df[birth_column] <= birth_max)]['player_name'].tolist()
                    # Filtrar el dataframe de similitud
                    filtered_df = filtered_df[filtered_df['player_name'].isin(valid_players)]
            
            # Filtros regulares (liga, equipo, posición, etc.)
            elif col in df.columns:
                # Obtener jugadores que cumplen con el filtro
                valid_players = df[df[col] == value]['player_name'].tolist()
                # Filtrar el dataframe de similitud
                filtered_df = filtered_df[filtered_df['player_name'].isin(valid_players)]
    
    # Excluir al jugador seleccionado y ordenar por similitud
    similar_players = filtered_df[filtered_df['player_name'] != player_name].sort_values(
        'similarity_score', ascending=False
    ).head(top_n)
    
    return similar_players

# Función para exportar a PDF
def export_to_pdf(player_data, chart_img=None, title="Informe de Jugador", df=None, selected_players=None, selected_metrics=None):
    """
    Exporta datos de jugadores a un archivo PDF con tema oscuro
    """
    # Crear un objeto FPDF para el tema oscuro
    class PDF(FPDF):
        def header(self):
            # Establecer color de fondo de página (negro)
            self.set_fill_color(13, 17, 23)  # Color oscuro (#0E1117)
            self.rect(0, 0, 210, 297, 'F')  # Rectángulo de fondo para toda la página
            
        def footer(self):
            # Pie de página
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(200, 200, 200)  # Texto gris claro
            self.cell(0, 10, '© 2024 Scouting Players | Desarrollado para el Máster en Big Data Deportivo', 0, 0, 'C')
    
    # Inicializar el PDF con tema oscuro
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Título en dos líneas si hay muchos jugadores
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)  # Texto blanco
    
    if selected_players and len(selected_players) > 2:
        # Primera línea del título
        title_line1 = "Comparación de Jugadores"
        pdf.cell(0, 10, txt=title_line1, ln=True, align="C")
        
        # Segunda línea: nombres de jugadores (hasta 60 caracteres)
        players_text = ", ".join(selected_players)
        if len(players_text) > 60:
            players_text = players_text[:57] + "..."
            
        # Limpiar el texto para evitar caracteres problemáticos
        players_text = players_text.replace("ó", "o").replace("á", "a").replace("é", "e").replace("í", "i").replace("ú", "u")
        players_text = players_text.replace("Ó", "O").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ú", "U")
        
        pdf.cell(0, 10, txt=players_text, ln=True, align="C")
    else:
        # Título en una sola línea para pocos jugadores
        title_safe = title.replace("ó", "o").replace("á", "a").replace("é", "e").replace("í", "i").replace("ú", "u")
        title_safe = title_safe.replace("Ó", "O").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ú", "U")
        pdf.cell(0, 15, txt=title_safe, ln=True, align="C")
    
    # Añadir imagen del gráfico
    if chart_img:
        try:
            # Guardar el BytesIO a un archivo temporal
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_file_name = temp_file.name
            temp_file.write(chart_img.getvalue())
            temp_file.close()
            
            # Añadir la imagen centrada
            pdf.image(temp_file_name, x=10, y=pdf.get_y() + 5, w=190)
            
            # Espacio para la imagen
            pdf.ln(160)
            
            # Eliminar el archivo temporal
            import os
            os.unlink(temp_file_name)
        except Exception as e:
            # Si hay un error con la imagen, mostrar mensaje
            pdf.set_font("Arial", 'I', 10)
            pdf.set_text_color(255, 75, 75)  # Texto rojo claro para errores
            pdf.cell(0, 10, txt=f"Error al incluir grafico: {str(e)}", ln=True)
            pdf.ln(5)
    
    # Encabezado para los datos
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(255, 75, 75)  # Color rojo para encabezados
    pdf.cell(0, 15, txt="DATOS DEL ANALISIS", ln=True, align="L")
    pdf.ln(5)
    
    # Datos detallados de cada jugador
    current_player = None
    
    # Preparar datos para la tabla
    headers = ["Jugador"]
    
    # Texto de datos en blanco
    pdf.set_text_color(255, 255, 255)  # Texto blanco
    
    for key, value in player_data.items():
        # Si es un nuevo jugador
        if key.startswith("Jugador"):
            if current_player:
                pdf.ln(5)  # Espacio entre jugadores
                
            current_player = value
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt=f"{key}: {value}", ln=True)
        else:
            # Es una métrica
            pdf.set_font("Arial", '', 10)
            # Añadir sangría para identificar que pertenece al jugador
            pdf.cell(15)  # Sangría
            
            # Dividir la clave para extraer solo la métrica
            parts = key.split(" - ")
            if len(parts) > 1:
                metric = parts[1]
                metric_truncated = truncate_text(metric, 25)
                pdf.cell(0, 6, txt=f"{metric_truncated}: {value}", ln=True)
                
                # Añadir a datos para la tabla de comparación
                if not metric in headers:
                    headers.append(metric)
    
    # Añadir espacio antes de la tabla
    pdf.ln(15)
    
    # Añadir una tabla de comparación justo después de los datos si tenemos lo necesario
    if df is not None and selected_players and selected_metrics:
        try:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(255, 75, 75)  # Color rojo para encabezados
            pdf.cell(0, 10, txt="TABLA COMPARATIVA", ln=True, align="C")
            pdf.ln(5)
            
            # Filtrar solo los jugadores seleccionados
            comparison_df = df[df['player_name'].isin(selected_players)]
            
            # Preparar los datos para la tabla
            table_data = []
            # Encabezados
            headers = ['player_name'] + selected_metrics
            display_headers = ['Jugador'] + [truncate_text(m, 15) for m in selected_metrics]
            table_data.append(display_headers)
            
            # Filas con datos de cada jugador
            for player in selected_players:
                player_df = comparison_df[comparison_df['player_name'] == player]
                if not player_df.empty:
                    player_name_truncated = truncate_text(player, 20)
                    row = [player_name_truncated]
                    for metric in selected_metrics:
                        if metric in player_df.columns:
                            value = player_df[metric].values[0]
                            row.append(f"{value:.2f}")
                    table_data.append(row)
            
            # Calcular anchos de columnas
            col_width = 180 / len(headers)
            row_height = 10
            
            # Establecer colores para la tabla
            pdf.set_draw_color(100, 100, 100)  # Borde gris
            pdf.set_text_color(255, 255, 255)  # Texto blanco
            
            # Dibujar encabezados
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(40, 40, 40)  # Fondo gris oscuro para encabezados
            for i, header in enumerate(display_headers):
                pdf.cell(col_width, row_height, header, 1, 0, 'C', 1)
            pdf.ln(row_height)
            
            # Dibujar filas
            pdf.set_font("Arial", '', 10)
            pdf.set_fill_color(25, 25, 25)  # Fondo aún más oscuro para las filas
            
            for i, row in enumerate(table_data[1:]):  # Saltar los encabezados
                # Alternar colores de fondo para mejor legibilidad
                fill = (i % 2 == 0)
                for cell in row:
                    pdf.cell(col_width, row_height, str(cell), 1, 0, 'C', fill)
                pdf.ln(row_height)
        
        except Exception as e:
            pdf.set_font("Arial", 'I', 10)
            pdf.set_text_color(255, 75, 75)  # Texto rojo claro para errores
            pdf.cell(0, 10, txt=f"Error al generar tabla comparativa: {str(e)}", ln=True)
    
    # Devolver PDF como bytes
    return pdf.output(dest='S').encode('latin1')

# Función para mostrar imagen descargable
def get_image_download_link(img, filename, text):
    """
    Genera un enlace para descargar una imagen
    """
    buffered = io.BytesIO()
    img.savefig(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

# Función para obtener una descarga de PDF
def get_pdf_download_link(pdf_bytes, filename, text):
    """
    Genera un enlace para descargar un PDF con estilo mejorado
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;color:#3366ff;font-weight:bold;display:flex;align-items:center;justify-content:center;">{text}</a>'
    return href

def create_radar_chart_unified(df, players, metrics, colors=None):
    """
    Crea un gráfico radar con estilo unificado para toda la aplicación
    - Tema oscuro con fondo negro y líneas blancas
    - Colores consistentes para jugadores
    - Mayor contraste para mejor visualización
    """
    # Filtrar datos
    filtered_df = df[df['player_name'].isin(players)]
    
    # Preparar datos para el radar
    categories = metrics
    fig = go.Figure()
    
    # Definir colores específicos para todos los jugadores en la aplicación
    # Esto asegura consistencia en todos los gráficos
    app_colors = {
        'player1': 'rgb(255,0,0)',      # rojo
        'player2': 'rgb(0,0,255)',      # azul
        'player3': 'rgb(255,255,0)',    # amarillo
        'player4': 'rgb(255,128,0)',    # naranja
        'player5': 'rgb(0,255,0)',      # verde
        'player6': 'rgb(255,0,255)',    # magenta
        'player7': 'rgb(0,255,255)',    # cian
        'player8': 'rgb(192,192,192)'   # plateado
    }
    
    # Colores por defecto en orden para el gráfico radar
    default_colors = [
        'rgb(255,255,0)',    # amarillo
        'rgb(0,0,255)',      # azul
        'rgb(0,100,0)',      # verde oscuro
        'rgb(139,0,0)',      # rojo oscuro    
    ]
    
    # Calcular valores máximos para cada métrica considerando solo los jugadores seleccionados
    max_values = {}
    for metric in metrics:
        max_values[metric] = filtered_df[metric].max()
    
    # Añadir cada jugador al radar
    for i, player in enumerate(players):
        player_data = filtered_df[filtered_df['player_name'] == player]
        if not player_data.empty:
            # Normalizar valores en relación al máximo de cada métrica
            values = []
            for metric in metrics:
                player_value = player_data[metric].values[0]
                max_value = max_values[metric]
                # Evitar división por cero
                normalized_value = player_value / max_value if max_value > 0 else 0
                values.append(normalized_value)
            
            # Cerrar el polígono repitiendo el primer valor
            values.append(values[0])
            categories_with_first = categories + [categories[0]]
            
            # Seleccionar color para este jugador
            # Intentar asignar colores consistentes por posición en la lista
            player_color = default_colors[i % len(default_colors)]
            
            # Crear versión más transparente para el relleno
            fill_color = player_color.replace('rgb', 'rgba').replace(')', ',0.15)')
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories_with_first,
                fill='toself',
                name=player,
                line=dict(color=player_color, width=3),  # Línea más gruesa para el contorno
                fillcolor=fill_color                   # Relleno más transparente
            ))
    
    # Configurar tema oscuro
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                linecolor='white',          # Color de línea radial
                gridcolor='rgba(255,255,255,0.2)',  # Color de cuadrícula radial
                tickfont=dict(color='white')  # Color de texto en eje radial
            ),
            angularaxis=dict(
                linecolor='white',          # Color de línea angular
                gridcolor='rgba(255,255,255,0.2)',  # Color de cuadrícula angular
                tickfont=dict(color='white')  # Color de texto en eje angular
            ),
            bgcolor='rgba(0,0,0,0)'  # Fondo transparente para integrarse con el tema oscuro
        ),
        showlegend=True,
        title="Comparación de Jugadores",
        title_font_color='white',  # Color de título
        height=600,
        width=800,
        paper_bgcolor='rgba(0,0,0,0)',  # Fondo de papel transparente
        plot_bgcolor='rgba(0,0,0,0)',   # Fondo de gráfico transparente
        legend=dict(
            font=dict(color='white')  # Color de texto en leyenda
        )
    )
    
    return fig

