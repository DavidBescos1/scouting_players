import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
import tempfile
import os
from common.functions import find_similar_players, create_radar_chart_unified, export_to_pdf, get_pdf_download_link

def show_similar_players(df, metrics):
    """
    Muestra la página para encontrar jugadores similares
    """
    # Título de la página
    st.title("Búsqueda de Jugadores Similares")
    
    # Asegurarnos que las columnas de texto se traten correctamente
    posicion_column = None
    for col in df.columns:
        if col == 'Posición' or col == 'posición' or col == 'Posicion' or col == 'posicion':
            posicion_column = col
            # Asegurarse de que la columna de posición se trate como texto
            df[posicion_column] = df[posicion_column].astype(str)
            # Reemplazar los valores '0' o '0.0' con valores vacíos
            df[posicion_column] = df[posicion_column].replace(['0', '0.0', 'nan', 'None', 'NaN'], '')
            break
    
    # Estilo CSS para reducir el espaciado entre los filtros
    st.markdown("""
    <style>
    /* Reducir el espacio entre los filtros */
    div[data-testid="stExpander"] div.stMarkdown p {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        line-height: 1.0 !important;
    }
    
    /* Reducir el espacio alrededor de los selectboxes */
    div[data-testid="stExpander"] div.stSelectbox {
        margin-top: 0px !important;
        margin-bottom: 4px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* Estilo para subheaders más compactos */
    div.stExpander h2 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.2rem !important;
    }
    
    /* Compactar el espacio dentro del expander */
    div[data-testid="stExpander"] div.streamlit-expanderContent {
        padding-top: 0px !important;
    }
    
    /* Reducir espacio entre secciones */
    div.block-container > div > div {
        margin-bottom: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if 'nacionalidad' in df.columns:
        df['nacionalidad'] = df['nacionalidad'].astype(str)
        df['nacionalidad'] = df['nacionalidad'].replace(['0', '0.0', 'nan', 'None', 'NaN'], '')
    
    # Crear columnas para la interfaz
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Seleccionar Jugador Base")
        
        with st.expander("Filtros de Jugador Base", expanded=True):
            # Filtro por liga
            st.markdown("Liga:")
            ligas = ['Todas']
            if 'liga' in df.columns:
                ligas += sorted(df['liga'].dropna().unique().tolist())
            
            selected_liga = st.selectbox("", options=ligas, key="similar_liga", label_visibility="collapsed")
            
            # Aplicar filtro de liga
            filtered_df = df.copy()
            if selected_liga != 'Todas' and 'liga' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['liga'] == selected_liga]
            
            # Filtro por equipo
            st.markdown("Equipo:")
            equipos = ['Todos']
            if 'equipo' in filtered_df.columns:
                equipos += sorted(filtered_df['equipo'].dropna().unique().tolist())
            
            selected_equipo = st.selectbox("", options=equipos, key="similar_equipo", label_visibility="collapsed")
            
            # Aplicar filtro de equipo
            if selected_equipo != 'Todos' and 'equipo' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['equipo'] == selected_equipo]
            
            # Filtro por posición con mismo formato que los otros
            st.markdown("Posición:")
            posiciones = ['Seleccione Posición']
            if posicion_column:
                pos_values = filtered_df[posicion_column].dropna().unique().tolist()
                pos_values = [p for p in pos_values if p and p.strip() and p != '0' and p != '0.0' and p.lower() != 'nan']
                if pos_values:
                    posiciones += sorted(pos_values)
                selected_posicion = st.selectbox("", options=posiciones, key="similar_posicion", label_visibility="collapsed")
                
                # Filtrar por posición seleccionada
                if selected_posicion != 'Seleccione Posición':
                    filtered_df = filtered_df[filtered_df[posicion_column] == selected_posicion]
            else:
                st.selectbox("", options=['Posición no disponible'], key="similar_posicion_na", label_visibility="collapsed")
            
            # Lista de jugadores disponibles después de filtrar
            st.markdown("Seleccionar jugador base:")
            players_list = []
            if 'player_name' in filtered_df.columns:
                players_list = filtered_df['player_name'].sort_values().unique().tolist()
            
            # Selección del jugador base
            if players_list:
                selected_player = st.selectbox(
                    "",
                    options=players_list,
                    key="similar_player",
                    label_visibility="collapsed"
                )
            else:
                st.warning("No hay jugadores disponibles con los filtros seleccionados.")
                selected_player = None
        
        st.subheader("Configuración de Similitud")
        
        # Filtrar solo métricas numéricas y excluir columnas de identificación
        numeric_metrics = [m for m in metrics if m not in ['player_name', 'pais', 'liga', 'equipo']]
        
        # Selección de métricas para la comparación
        default_metrics = numeric_metrics[:5] if len(numeric_metrics) > 5 else numeric_metrics
        selected_metrics = st.multiselect(
            "Seleccionar métricas para la comparación:",
            options=numeric_metrics,
            default=default_metrics,
            key="similar_metrics"
        )
        
        # Número de jugadores similares a mostrar
        num_similar = st.slider(
            "Número de jugadores similares:",
            min_value=1,
            max_value=10,
            value=5
        )
        
        # Filtro por año de nacimiento
        st.subheader("Filtro por Año de Nacimiento")
        birth_year_column = None

        # Buscar la columna de año de nacimiento
        for col in df.columns:
            if 'año nacimiento' in col.lower() or 'nacimiento' in col.lower() or 'birth' in col.lower():
                birth_year_column = col
                break

        if birth_year_column:
            # Rango de años predefinido para scouting
            min_year = 1980
            max_year = 2010
            
            # Valores por defecto más comunes para scouting
            default_min = 1990
            default_max = 2005
            
            # Slider para filtrar por rango de años de nacimiento
            birth_year_range = st.slider(
                "Rango de años de nacimiento:",
                min_value=min_year,
                max_value=max_year,
                value=(default_min, default_max),
                key="birth_year_filter"
            )
            
            # Añadir filtro por año de nacimiento
            birth_min, birth_max = birth_year_range
            st.write(f"Buscando jugadores nacidos entre {birth_min} y {birth_max}")
        else:
            st.info("No se encontró columna de año de nacimiento en los datos")
        
        # Estilo CSS para los botones (rojo)
        st.markdown("""
        <style>
        div.stButton > button {
            background-color: #FF4B4B;  /* Color rojo para botones */
            color: white;
            font-weight: bold;
            border: none;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Botones para acciones
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("IMPRIMIR PÁGINA", key="similar_print"):
                st.markdown(
                    """
                    <script>
                    function printPage() {
                        window.print()
                    }
                    </script>
                    <button onclick="printPage()">IMPRIMIR PÁGINA</button>
                    """,
                    unsafe_allow_html=True
                )
                st.success("Haz clic en Ctrl+P o Cmd+P para imprimir esta página")
        
        with col_btn2:
            if st.button("EXPORTAR A PDF", key="similar_export"):
                try:
                    with st.spinner("Generando PDF..."):
                        # Definir filtros para asegurar misma posición
                        similar_filters = {}
                        
                        # Si hay posición seleccionada, filtrar por la misma posición
                        if posicion_column and selected_posicion != 'Seleccione Posición':
                            player_position = df[df['player_name'] == selected_player][posicion_column].values[0]
                            similar_filters[posicion_column] = player_position
                        
                        # Añadir filtro por año de nacimiento si existe
                        if 'birth_year_filter' in st.session_state and birth_year_column:
                            birth_min, birth_max = st.session_state.birth_year_filter
                            similar_filters['birth_year_range'] = (birth_min, birth_max)
                        
                        # Encontrar jugadores similares
                        similar_players_df = find_similar_players(
                            df, 
                            selected_player, 
                            selected_metrics, 
                            top_n=num_similar,
                            filters=similar_filters
                        )
                        
                        # Lista completa de jugadores para el radar
                        players_to_compare = [selected_player] + similar_players_df['player_name'].tolist()[:3]
                        
                        # Configurar la figura con mayor calidad para PDF
                        fig = create_radar_chart_unified(df, players_to_compare, selected_metrics)
                        fig.update_layout(
                            width=1000,
                            height=800,
                            margin=dict(l=50, r=50, t=80, b=50),
                            title_text="Comparación de Jugadores",
                            title_x=0.5
                        )
                        
                        # Guardar figura en memoria
                        img_buffer = io.BytesIO()
                        fig.write_image(img_buffer, format='png', scale=2)
                        img_buffer.seek(0)
                        
                        # Crear datos para el PDF
                        player_data = {
                            "Jugador Base": selected_player,
                            "Métricas utilizadas": ", ".join(selected_metrics)
                        }
                        
                        # Añadir jugadores similares y su puntuación
                        for i, row in similar_players_df.iterrows():
                            if i < num_similar:
                                player_data[f"#{i+1} - {row['player_name']}"] = f"Similitud: {row['similarity_score']:.2f}"
                        
                        # Generar PDF
                        pdf_bytes = export_to_pdf(
                            player_data, 
                            img_buffer,
                            "Jugadores Similares",
                            df,
                            players_to_compare,
                            selected_metrics
                        )
                        
                        # Mostrar enlace de descarga
                        st.success("PDF generado con éxito!")
                        st.markdown(
                            get_pdf_download_link(
                                pdf_bytes,
                                "jugadores_similares.pdf",
                                "📥 Descargar PDF"
                            ),
                            unsafe_allow_html=True
                        )
                except Exception as e:
                    st.error(f"Error al exportar a PDF: {e}")
                    st.info("Para resolver este error, ejecuta: pip install -U kaleido")
    
    with col2:
        if selected_player and selected_metrics and len(selected_metrics) > 0:
            # Definir filtros para asegurar misma posición
            similar_filters = {}
            
            # Si hay posición seleccionada, filtrar por la misma posición
            if posicion_column and selected_posicion != 'Seleccione Posición':
                player_position = df[df['player_name'] == selected_player][posicion_column].values[0]
                similar_filters[posicion_column] = player_position
            
            # Añadir filtro por año de nacimiento si existe
            if 'birth_year_filter' in st.session_state and birth_year_column:
                birth_min, birth_max = st.session_state.birth_year_filter
                similar_filters['birth_year_range'] = (birth_min, birth_max)
            
            # Encontrar jugadores similares
            similar_players_df = find_similar_players(
                df, 
                selected_player, 
                selected_metrics, 
                top_n=num_similar,
                filters=similar_filters
            )
            
            # Mostrar tabla de jugadores similares
            st.subheader(f"Jugadores más similares a {selected_player}")
            
            if similar_players_df.empty:
                st.warning("No se encontraron jugadores similares que cumplan con los filtros.")
            else:
                # Formatear y mostrar tabla de similitud
                similarity_display = similar_players_df.copy()
                
                # Añadir información de equipo y liga si están disponibles
                if 'equipo' in df.columns:
                    jugador_info = {}
                    for player in similarity_display['player_name']:
                        player_data = df[df['player_name'] == player]
                        equipo = player_data['equipo'].values[0] if 'equipo' in player_data.columns else 'N/A'
                        liga = player_data['liga'].values[0] if 'liga' in player_data.columns else 'N/A'
                        jugador_info[player] = {'equipo': equipo, 'liga': liga}
                    
                    similarity_display['equipo'] = similarity_display['player_name'].map(lambda x: jugador_info[x]['equipo'])
                    similarity_display['liga'] = similarity_display['player_name'].map(lambda x: jugador_info[x]['liga'])
                
                # Formatear puntuación de similitud
                similarity_display['similarity_score'] = similarity_display['similarity_score'].apply(lambda x: f"{x:.2f}")
                
                # IMPORTANTE: Forzar a Streamlit a usar exactamente estas columnas en este orden
                display_cols = ['player_name', 'similarity_score']
                if 'equipo' in similarity_display.columns:
                    display_cols.extend(['equipo', 'liga'])
                
                # Aplicar filtro de columnas explícitamente
                similarity_display = similarity_display[display_cols].copy()
                
                # Renombrar columnas
                display_names = ['Jugador', 'Puntuación de Similitud']
                if 'equipo' in similarity_display.columns:
                    display_names.extend(['Equipo', 'Liga'])
                
                similarity_display.columns = display_names
                
                # CRÍTICO: Usar hide_index=True para eliminar la columna de números
                st.dataframe(
                    similarity_display,
                    use_container_width=True,
                    hide_index=True  # Forzar que no muestre índices/números
                )
                
                # Lista de jugadores para el radar (jugador base + top 3 similares)
                players_to_compare = [selected_player] + similar_players_df['player_name'].tolist()[:3]
                
                # Crear y mostrar el gráfico radar con estilo unificado
                st.subheader("Comparación visual")
                fig = create_radar_chart_unified(df, players_to_compare, selected_metrics)
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tabla con datos detallados
                st.subheader("Datos detallados")
                
                # Filtrar dataframe para jugadores seleccionados
                comparison_df = df[df['player_name'].isin(players_to_compare)].copy()
                display_cols = ['player_name'] + selected_metrics
                
                # Formatear tabla
                formatted_df = comparison_df[display_cols].set_index('player_name')
                
                # Mostrar tabla con colores para máximos y mínimos (verde oscuro y rojo oscuro)
                st.dataframe(
                    formatted_df.style.highlight_max(axis=0, color='#006400').highlight_min(axis=0, color='#8B0000'),
                    use_container_width=True
                )
                
                # Mostrar gráfico de barras para comparar métricas específicas
                st.subheader("Comparación de métricas clave")
                
                # Seleccionar métricas para comparar en barras
                if len(selected_metrics) > 2:
                    metrics_for_bars = selected_metrics[:3]  # Tomar las primeras 3 métricas
                    
                    # Preparar datos para el gráfico
                    bar_data = []
                    for player in players_to_compare:
                        player_row = df[df['player_name'] == player].iloc[0]
                        for metric in metrics_for_bars:
                            bar_data.append({
                                'Jugador': player,
                                'Métrica': metric,
                                'Valor': player_row[metric]
                            })
                    
                    bar_df = pd.DataFrame(bar_data)
                    
                    # Crear gráfico de barras con tema oscuro y colores personalizados
                    custom_colors = ['rgb(0,0,255)', 'rgb(255,0,0)', 'rgb(0,100,0)']  # Azul, Rojo, Verde oscuro
                    
                    fig = px.bar(
                        bar_df, 
                        x='Jugador', 
                        y='Valor', 
                        color='Métrica', 
                        barmode='group',
                        title='Comparación de métricas seleccionadas',
                        color_discrete_sequence=custom_colors
                    )
                    
                    # Configurar tema oscuro para el gráfico de barras
                    fig.update_layout(
                        height=500,
                        template="plotly_dark",  # Usar plantilla oscura
                        paper_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                        plot_bgcolor='rgba(0,0,0,0)',   # Fondo del gráfico transparente
                        font=dict(color='white')       # Color de texto blanco
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona un jugador base y métricas para encontrar jugadores similares.")
            
            # Mostrar información instructiva
            st.markdown("""
            ### Instrucciones
            1. Utiliza los filtros para encontrar el jugador base
            2. Selecciona las métricas que consideras más relevantes para la comparación
            3. Ajusta el número de jugadores similares a mostrar
            4. Visualiza los resultados y compara las estadísticas
            5. Exporta los resultados a PDF o imprime la página
            
            Esta herramienta utiliza algoritmos de similitud para encontrar jugadores
            con características estadísticas parecidas al jugador seleccionado.
            """)
            
            # Sección para mostrar conexión a múltiples fuentes de datos
            st.markdown("---")
            with st.expander("Fuentes de datos utilizadas", expanded=False):
                col1, col2 = st.columns(2)
        
                with col1:
                    st.subheader("Datos desde Parquet")
                    st.info("Los datos principales de jugadores para comparación son cargados desde un archivo Parquet")
                    # Mostramos una pequeña muestra de los datos de Parquet que ya tenemos cargados
                    st.dataframe(df[['player_name', 'equipo', 'posicion']].head(3))
        
                with col2:
                    st.subheader("Datos desde SQLite")
                    st.info("Información complementaria desde base de datos SQLite")
                    # Realizamos una consulta a SQLite para mostrar datos adicionales
                    from common.cache import query_database
                    try:
                        query = "SELECT player_name, equipo, liga FROM players_data LIMIT 3"
                        sqlite_data = query_database(query)
                        if sqlite_data is not None and not sqlite_data.empty:
                            st.dataframe(sqlite_data)
                        else:
                            st.warning("No se pudieron cargar datos desde SQLite. Usando datos de respaldo.")
                            # Datos de respaldo para mostrar como ejemplo
                            backup_data = pd.DataFrame({
                                'player_name': ['Ejemplo 1', 'Ejemplo 2'],
                                'stats_type': ['Ofensivas', 'Defensivas'],
                                'valor': [85, 78]
                            })
                            st.dataframe(backup_data)
                    except Exception as e:
                        st.error(f"Error al consultar SQLite: {e}")
                        # Mostrar datos de respaldo en caso de error
                        backup_data = pd.DataFrame({
                            'player_name': ['Ejemplo 1', 'Ejemplo 2'],
                            'stats_type': ['Ofensivas', 'Defensivas'],
                            'valor': [85, 78]
                        })
                        st.dataframe(backup_data)
                        