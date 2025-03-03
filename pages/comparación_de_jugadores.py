import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import tempfile
import os
from common.functions import create_radar_chart_unified, export_to_pdf, get_pdf_download_link

def show_player_comparison(df, metrics):
    """
    Muestra la página de comparación de jugadores
    """
    # Título de la página
    st.title("COMPARACIÓN DE JUGADORES")
    
    # Crear 4 columnas para los jugadores
    col1, col2, col3, col4 = st.columns(4)
    
    # Lista para almacenar los jugadores seleccionados
    selected_players = []
    
    # Verificar si la columna 'Posición' existe
    posicion_column = None
    for col in df.columns:
        if col == 'Posición' or col == 'posición' or col == 'Posicion' or col == 'posicion':
            posicion_column = col
            # Asegurarse de que la columna de posición se trate como texto
            df[posicion_column] = df[posicion_column].astype(str)
            # Reemplazar los valores '0' o '0.0' con valores vacíos
            df[posicion_column] = df[posicion_column].replace(['0', '0.0', 'nan', 'None', 'NaN'], '')
            break
    
    # JUGADOR 1
    with col1:
        st.markdown("LIGA:")
        ligas1 = ['Seleccione Liga']
        if 'liga' in df.columns:
            ligas1 += sorted(df['liga'].dropna().unique().tolist())
        selected_liga1 = st.selectbox("", options=ligas1, key="liga_1", label_visibility="collapsed")
        
        # Filtrar por liga seleccionada
        filtered_df1 = df.copy()
        if selected_liga1 != 'Seleccione Liga' and 'liga' in df.columns:
            filtered_df1 = filtered_df1[filtered_df1['liga'] == selected_liga1]
        
        st.markdown("EQUIPO:")
        equipos1 = ['Seleccione Equipo']
        if 'equipo' in filtered_df1.columns:
            equipos1 += sorted(filtered_df1['equipo'].dropna().unique().tolist())
        selected_equipo1 = st.selectbox("", options=equipos1, key="equipo_1", label_visibility="collapsed")
        
        # Filtrar por equipo seleccionado
        if selected_equipo1 != 'Seleccione Equipo' and 'equipo' in filtered_df1.columns:
            filtered_df1 = filtered_df1[filtered_df1['equipo'] == selected_equipo1]
        
        st.markdown("POSICIÓN:")
        if posicion_column:
            # Filtrar posiciones vacías y valores únicos
            posiciones1 = ['Seleccione Posición']
            pos_values = filtered_df1[posicion_column].dropna().unique().tolist()
            pos_values = [p for p in pos_values if p and p.strip() and p != '0' and p != '0.0' and p.lower() != 'nan']
            if pos_values:
                posiciones1 += sorted(pos_values)
            selected_posicion1 = st.selectbox("", options=posiciones1, key="posicion_1", label_visibility="collapsed")
            
            # Filtrar por posición seleccionada
            if selected_posicion1 != 'Seleccione Posición':
                filtered_df1 = filtered_df1[filtered_df1[posicion_column] == selected_posicion1]
        else:
            st.selectbox("", options=['Posición no disponible'], key="posicion_1_na", label_visibility="collapsed")
        
        st.markdown("JUGADOR:")
        players_list1 = ['Seleccione Jugador']
        if 'player_name' in filtered_df1.columns:
            players_list1 += filtered_df1['player_name'].sort_values().unique().tolist()
        player1 = st.selectbox("", options=players_list1, key="player_1", label_visibility="collapsed")
        
        # Añadir el jugador seleccionado
        if player1 != 'Seleccione Jugador':
            selected_players.append(player1)
    
    # JUGADOR 2
    with col2:
        st.markdown("LIGA:")
        ligas2 = ['Seleccione Liga']
        if 'liga' in df.columns:
            ligas2 += sorted(df['liga'].dropna().unique().tolist())
        selected_liga2 = st.selectbox("", options=ligas2, key="liga_2", label_visibility="collapsed")
        
        # Filtrar por liga seleccionada
        filtered_df2 = df.copy()
        if selected_liga2 != 'Seleccione Liga' and 'liga' in df.columns:
            filtered_df2 = filtered_df2[filtered_df2['liga'] == selected_liga2]
        
        st.markdown("EQUIPO:")
        equipos2 = ['Seleccione Equipo']
        if 'equipo' in filtered_df2.columns:
            equipos2 += sorted(filtered_df2['equipo'].dropna().unique().tolist())
        selected_equipo2 = st.selectbox("", options=equipos2, key="equipo_2", label_visibility="collapsed")
        
        # Filtrar por equipo seleccionado
        if selected_equipo2 != 'Seleccione Equipo' and 'equipo' in filtered_df2.columns:
            filtered_df2 = filtered_df2[filtered_df2['equipo'] == selected_equipo2]
        
        st.markdown("POSICIÓN:")
        if posicion_column:
            # Filtrar posiciones vacías y valores únicos
            posiciones2 = ['Seleccione Posición']
            pos_values = filtered_df2[posicion_column].dropna().unique().tolist()
            pos_values = [p for p in pos_values if p and p.strip() and p != '0' and p != '0.0' and p.lower() != 'nan']
            if pos_values:
                posiciones2 += sorted(pos_values)
            selected_posicion2 = st.selectbox("", options=posiciones2, key="posicion_2", label_visibility="collapsed")
            
            # Filtrar por posición seleccionada
            if selected_posicion2 != 'Seleccione Posición':
                filtered_df2 = filtered_df2[filtered_df2[posicion_column] == selected_posicion2]
        else:
            st.selectbox("", options=['Posición no disponible'], key="posicion_2_na", label_visibility="collapsed")
        
        st.markdown("JUGADOR:")
        players_list2 = ['Seleccione Jugador']
        if 'player_name' in filtered_df2.columns:
            players_list2 += filtered_df2['player_name'].sort_values().unique().tolist()
        player2 = st.selectbox("", options=players_list2, key="player_2", label_visibility="collapsed")
        
        # Añadir el jugador seleccionado
        if player2 != 'Seleccione Jugador':
            selected_players.append(player2)
    
    # JUGADOR 3
    with col3:
        st.markdown("LIGA:")
        ligas3 = ['Seleccione Liga']
        if 'liga' in df.columns:
            ligas3 += sorted(df['liga'].dropna().unique().tolist())
        selected_liga3 = st.selectbox("", options=ligas3, key="liga_3", label_visibility="collapsed")
        
        # Filtrar por liga seleccionada
        filtered_df3 = df.copy()
        if selected_liga3 != 'Seleccione Liga' and 'liga' in df.columns:
            filtered_df3 = filtered_df3[filtered_df3['liga'] == selected_liga3]
        
        st.markdown("EQUIPO:")
        equipos3 = ['Seleccione Equipo']
        if 'equipo' in filtered_df3.columns:
            equipos3 += sorted(filtered_df3['equipo'].dropna().unique().tolist())
        selected_equipo3 = st.selectbox("", options=equipos3, key="equipo_3", label_visibility="collapsed")
        
        # Filtrar por equipo seleccionado
        if selected_equipo3 != 'Seleccione Equipo' and 'equipo' in filtered_df3.columns:
            filtered_df3 = filtered_df3[filtered_df3['equipo'] == selected_equipo3]
        
        st.markdown("POSICIÓN:")
        if posicion_column:
            # Filtrar posiciones vacías y valores únicos
            posiciones3 = ['Seleccione Posición']
            pos_values = filtered_df3[posicion_column].dropna().unique().tolist()
            pos_values = [p for p in pos_values if p and p.strip() and p != '0' and p != '0.0' and p.lower() != 'nan']
            if pos_values:
                posiciones3 += sorted(pos_values)
            selected_posicion3 = st.selectbox("", options=posiciones3, key="posicion_3", label_visibility="collapsed")
            
            # Filtrar por posición seleccionada
            if selected_posicion3 != 'Seleccione Posición':
                filtered_df3 = filtered_df3[filtered_df3[posicion_column] == selected_posicion3]
        else:
            st.selectbox("", options=['Posición no disponible'], key="posicion_3_na", label_visibility="collapsed")
        
        st.markdown("JUGADOR:")
        players_list3 = ['Seleccione Jugador']
        if 'player_name' in filtered_df3.columns:
            players_list3 += filtered_df3['player_name'].sort_values().unique().tolist()
        player3 = st.selectbox("", options=players_list3, key="player_3", label_visibility="collapsed")
        
        # Añadir el jugador seleccionado
        if player3 != 'Seleccione Jugador':
            selected_players.append(player3)
    
    # JUGADOR 4
    with col4:
        st.markdown("LIGA:")
        ligas4 = ['Seleccione Liga']
        if 'liga' in df.columns:
            ligas4 += sorted(df['liga'].dropna().unique().tolist())
        selected_liga4 = st.selectbox("", options=ligas4, key="liga_4", label_visibility="collapsed")
        
        # Filtrar por liga seleccionada
        filtered_df4 = df.copy()
        if selected_liga4 != 'Seleccione Liga' and 'liga' in df.columns:
            filtered_df4 = filtered_df4[filtered_df4['liga'] == selected_liga4]
        
        st.markdown("EQUIPO:")
        equipos4 = ['Seleccione Equipo']
        if 'equipo' in filtered_df4.columns:
            equipos4 += sorted(filtered_df4['equipo'].dropna().unique().tolist())
        selected_equipo4 = st.selectbox("", options=equipos4, key="equipo_4", label_visibility="collapsed")
        
        # Filtrar por equipo seleccionado
        if selected_equipo4 != 'Seleccione Equipo' and 'equipo' in filtered_df4.columns:
            filtered_df4 = filtered_df4[filtered_df4['equipo'] == selected_equipo4]
        
        st.markdown("POSICIÓN:")
        if posicion_column:
            # Filtrar posiciones vacías y valores únicos
            posiciones4 = ['Seleccione Posición']
            pos_values = filtered_df4[posicion_column].dropna().unique().tolist()
            pos_values = [p for p in pos_values if p and p.strip() and p != '0' and p != '0.0' and p.lower() != 'nan']
            if pos_values:
                posiciones4 += sorted(pos_values)
            selected_posicion4 = st.selectbox("", options=posiciones4, key="posicion_4", label_visibility="collapsed")
            
            # Filtrar por posición seleccionada
            if selected_posicion4 != 'Seleccione Posición':
                filtered_df4 = filtered_df4[filtered_df4[posicion_column] == selected_posicion4]
        else:
            st.selectbox("", options=['Posición no disponible'], key="posicion_4_na", label_visibility="collapsed")
        
        st.markdown("JUGADOR:")
        players_list4 = ['Seleccione Jugador']
        if 'player_name' in filtered_df4.columns:
            players_list4 += filtered_df4['player_name'].sort_values().unique().tolist()
        player4 = st.selectbox("", options=players_list4, key="player_4", label_visibility="collapsed")
        
        # Añadir el jugador seleccionado
        if player4 != 'Seleccione Jugador':
            selected_players.append(player4)
    
    # Segunda sección: Instrucciones y métricas
    left_col, right_col = st.columns(2)
    
    # Columna izquierda: Instrucciones
    with left_col:
        st.header("INSTRUCCIONES")
        st.markdown("1. Seleccione liga, equipo y posición para cada jugador")
        st.markdown("2. Seleccione hasta 4 jugadores para comparar")
        st.markdown("3. Elija las métricas que desea analizar")
        st.markdown("4. Visualice el gráfico radar y los datos detallados")
    
    # Columna derecha: Métricas
    with right_col:
        st.header("MÉTRICAS")
        
        # Filtrar solo métricas numéricas y excluir las no deseadas
        exclude_metrics = ['posición', 'año nacimiento', 'minutos jugados', 'posicion', 
                          'año', 'nacimiento', 'minutos', 'jugados', 'player_name', 
                          'pais', 'liga', 'equipo', 'nacionalidad']
        
        # Filtrar métricas válidas
        numeric_metrics = []
        for m in metrics:
            if not any(exclude in m.lower() for exclude in exclude_metrics):
                numeric_metrics.append(m)
        
        # Selección de métricas
        selected_metrics = st.multiselect(
            "Seleccionar métricas para comparar:",
            options=numeric_metrics,
            default=numeric_metrics[:5] if len(numeric_metrics) > 5 else numeric_metrics
        )
    
    # Sección para el gráfico radar
    if selected_players and selected_metrics:
        st.header("GRÁFICO RADAR")
        
        # Colores base para el radar - se utilizarán contornos fuertes y rellenos transparentes
        colors = [
            'rgb(255,0,0)',      # rojo
            'rgb(0,0,255)',      # azul
            'rgb(255,255,0)',    # amarillo
            'rgb(100,100,100)'   # gris
        ]
        
        # Crear y mostrar el gráfico radar personalizado
        fig = create_radar_chart_unified(df, selected_players, selected_metrics)
        st.plotly_chart(fig, use_container_width=True)
        
        # Estilo CSS para los botones
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
        .button-container {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Dividir el ancho en 3 partes y usar las últimas 2 para los botones
        _, btn_col1, btn_col2 = st.columns([2, 1, 1])
        
        # Botón de imprimir en la penúltima columna
        with btn_col1:
            if st.button("IMPRIMIR PÁGINA"):
                # Versión simplificada que debería funcionar mejor
                st.markdown("""
                <script>
                    window.print();
                </script>
                """, unsafe_allow_html=True)
                st.success("Haz clic en Ctrl+P o Cmd+P para imprimir esta página")
        
        # Botón de exportar en la última columna
        with btn_col2:
            if st.button("EXPORTAR A PDF"):
                try:
                    # Mostrar mensaje de carga
                    with st.spinner("Generando PDF..."):
                        # Generar imagen de alta calidad del gráfico
                        img_buffer = io.BytesIO()
                
                        # Configurar la figura con mayor calidad y tamaño para PDF
                        fig.update_layout(
                            width=1000,  # Mayor ancho para mejor calidad
                            height=800,  # Mayor altura para mejor calidad
                            margin=dict(l=50, r=50, t=80, b=50),  # Márgenes adecuados
                            title_text="Comparación de Jugadores",  # Título para el gráfico
                            title_x=0.5  # Centrar título
                        )
                
                        # Usar formato 'png' con alta resolución
                        fig.write_image(img_buffer, format='png', scale=2)  # scale=2 duplica la resolución
                        img_buffer.seek(0)
                
                        # Crear datos para el PDF
                        player_data = {}
                        for i, player in enumerate(selected_players):
                            player_data[f"Jugador {i+1}"] = player
                    
                            # Añadir métricas del jugador
                            player_df = df[df['player_name'] == player]
                            for metric in selected_metrics:
                                if not player_df.empty and metric in player_df.columns:
                                    value = player_df[metric].values[0]
                                    player_data[f"{player} - {metric}"] = f"{value:.2f}"
                
                        # Generar PDF mejorado incluyendo dataframe para tabla
                        # Pasamos nombre corto para el título - los jugadores se generarán automáticamente
                        pdf_bytes = export_to_pdf(
                            player_data, 
                            img_buffer, 
                            "Comparación de Jugadores",  # Título simplificado
                            df,  # Pasar el dataframe completo
                            selected_players,  # Pasar jugadores seleccionados
                            selected_metrics  # Pasar métricas seleccionadas
                        )
                
                        # Mostrar enlace de descarga
                        st.success("PDF generado con éxito!")
                        st.markdown(
                            get_pdf_download_link(
                                pdf_bytes,
                                "comparacion_jugadores.pdf",
                                "📥 Descargar PDF"
                            ),
                            unsafe_allow_html=True
                        )
        
                except Exception as e:
                    # Capturar y mostrar errores generales
                    st.error(f"Error al exportar a PDF: {e}")
                    st.info("Para resolver este error, ejecuta: pip install -U kaleido")
        
        # Mostrar tabla con datos detallados
        st.header("DATOS DETALLADOS")
        
        comparison_df = df[df['player_name'].isin(selected_players)].copy()
        display_cols = ['player_name'] + selected_metrics
        
        # Formatear tabla
        formatted_df = comparison_df[display_cols].set_index('player_name')
        
        # Mostrar tabla con colores para máximos y mínimos (verde oscuro y rojo oscuro)
        st.dataframe(
            formatted_df.style.highlight_max(axis=0, color='#006400').highlight_min(axis=0, color='#8B0000'),
            use_container_width=True
        )
        
        # Sección para conexión a múltiples fuentes de datos
        st.markdown("---")
        with st.expander("Fuentes de datos utilizadas", expanded=False):
            col1, col2 = st.columns(2)
        
            with col1:
                st.subheader("Datos desde Parquet")
                st.info("Los datos principales de jugadores son cargados desde un archivo Parquet")
                # Mostramos una pequeña muestra de los datos de Parquet que ya tenemos cargados
                st.dataframe(df[['player_name', 'equipo', 'liga']].head(3))
        
            with col2:
                st.subheader("Datos desde SQLite")
                st.info("Consultas complementarias desde base de datos SQLite")
                # Realizamos una consulta a SQLite para mostrar datos adicionales
                from common.cache import query_database
                try:
                    query = "SELECT * FROM players_data LIMIT 3"
                    sqlite_data = query_database(query)
                    if sqlite_data is not None and not sqlite_data.empty:
                        st.dataframe(sqlite_data)
                    else:
                        st.warning("No se pudieron cargar datos desde SQLite. Usando datos de respaldo.")
                        # Datos de respaldo para mostrar como ejemplo
                        backup_data = pd.DataFrame({
                            'player_id': [1, 2, 3],
                            'player_name': ['Ejemplo 1', 'Ejemplo 2', 'Ejemplo 3'],
                            'team': ['Equipo A', 'Equipo B', 'Equipo C']
                        })
                        st.dataframe(backup_data)
                except Exception as e:
                    st.error(f"Error al consultar SQLite: {e}")
                    # Mostrar datos de respaldo en caso de error
                    backup_data = pd.DataFrame({
                        'player_id': [1, 2, 3],
                        'player_name': ['Ejemplo 1', 'Ejemplo 2', 'Ejemplo 3'],
                        'team': ['Equipo A', 'Equipo B', 'Equipo C']
                    })
                    st.dataframe(backup_data)
                    