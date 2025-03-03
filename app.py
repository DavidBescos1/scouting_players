import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu
from common.cache import get_data, prepare_player_data, get_metrics_list
import base64

# Configuración de la página con 'translate=no' para evitar traducción automática
st.set_page_config(
    page_title="Scouting Players",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Añadir metadatos para evitar traducción automática
st.markdown("""
<head>
    <meta name="google" content="notranslate">
</head>
<style>
    [translate="no"] {
        translate: no;
    }
    /* Asegurar que los términos deportivos no se traduzcan */
    .notranslate {
        translate: no;
    }
</style>
""", unsafe_allow_html=True)

# Función para autenticación
def authenticate(username, password):
    # Credenciales válidas
    return username == "admin" and password == "admin"

# Función para cargar imagen de fondo
def set_background():
    # Crear un fondo para la aplicación
    try:
        background_img_path = os.path.join('assets', 'background.jpg')
        if os.path.exists(background_img_path):
            with open(background_img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url(data:image/jpg;base64,{encoded_string});
                    background-size: cover;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        # Si hay error, usar un fondo de color sólido
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #f0f2f6;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

# Inicialización de la sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Estilos para hacer la interfaz más compacta
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
    div.stButton > button {
        padding: 0.25rem 1rem;
    }
    div.row-widget.stButton {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .leagues-section {
        margin-top: 0.5rem;
    }
    input {
        padding: 0.25rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    /* Para hacer el título más grande */
    .title-large {
        font-size: 2.5rem !important;
        font-weight: bold !important;
        margin: 0.75rem 0 !important;
    }
    /* Para centrar los logos horizontalmente */
    [data-testid="column"] {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Si está autenticado, ocultar el menú automático gris
if st.session_state.authenticated:
    st.markdown("""
    <style>
    /* Ocultar el menú gris automático después del login */
    [data-testid="stSidebarNavItems"] {
        display: none;
    }
    
    /* Hacer que el logo y el menú personalizado estén más arriba */
    .sidebar .sidebar-content {
        margin-top: -20px;
    }
    
    /* Más espacio para el contenido principal */
    .main .block-container {
        margin-top: -30px;
    }
    </style>
    """, unsafe_allow_html=True)

# Pantalla de login si no está autenticado
if not st.session_state.authenticated:
    set_background()
    
    # Mostrar logo en el sidebar
    try:
        logo_path = os.path.join('assets', 'logo.png')
        if os.path.exists(logo_path):
            st.sidebar.image(logo_path, width=200)
        else:
            st.sidebar.warning("Logo no encontrado")
    except Exception as e:
        st.sidebar.error(f"Error al cargar el logo: {e}")
    
    # Título más grande
    st.markdown("<h1 class='title-large' style='text-align: center; color: white;'>Scouting Players - Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white; font-size: 14px; margin: 0.5rem 0;'>Bienvenido a <b>Scouting Players</b>, tu plataforma profesional para análisis de rendimiento de jugadores.</p>", unsafe_allow_html=True)
    
    # Formulario más compacto
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h4 style='text-align: center; color: white; margin: 0.25rem 0;'>Iniciar Sesión</h4>", unsafe_allow_html=True)
        username = st.text_input("Usuario", label_visibility="collapsed", placeholder="Usuario")
        password = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="Contraseña")
        
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuario/contraseña incorrectos. Use 'admin'/'admin'")
    
    # Sección de escudos centrada horizontalmente
    st.markdown("<h4 style='text-align: center; color: white; margin: 0.5rem 0;'>Ligas Disponibles</h4>", unsafe_allow_html=True)
    
    # Usar columnas para forzar la distribución horizontal
    logo_cols = st.columns(5)
    ligas = ['españa', 'inglaterra', 'alemania', 'francia', 'italia']
    
    # Cargar cada logo en su columna centrada
    for i, liga in enumerate(ligas):
        with logo_cols[i]:
            logo_path = os.path.join('assets', f'{liga}.png')
            if os.path.exists(logo_path):
                st.image(logo_path, width=60)
    
    # Pie de página actualizado
    st.markdown("<div style='text-align: center; color: #ccc; font-size: 10px; margin-top: 0.25rem;'>© 2024 Scouting Players | Desarrollado para el Máster de Python Avanzado</div>", unsafe_allow_html=True)

# Si está autenticado, mostrar la aplicación principal
else:
    # Configurar la interfaz principal
    st.sidebar.image(os.path.join('assets', 'logo.png'), width=200)
    
    # Menú de navegación
    with st.sidebar:
        selected = option_menu(
            menu_title="Navegación",
            options=["Comparación de Jugadores", "Jugadores Similares"],
            icons=["people", "search"],
            menu_icon="cast",
            default_index=0,
        )
    
    # Carga de datos
    with st.spinner("Cargando datos..."):
        # Cargar y preparar datos
        df_raw = get_data()
        if df_raw is not None:
            df = prepare_player_data(df_raw)
            metrics = get_metrics_list(df)
        else:
            st.error("No se pudieron cargar los datos. Verifica que el archivo de datos esté disponible.")
            st.stop()
    
    # Páginas
    if selected == "Comparación de Jugadores":
        # Importar y mostrar la página de comparación
        from pages.comparación_de_jugadores import show_player_comparison
        show_player_comparison(df, metrics)
        
    elif selected == "Jugadores Similares":
        # Importar y mostrar la página de jugadores similares
        from pages.jugadores_similares import show_similar_players
        show_similar_players(df, metrics)

# Pie de página versión autenticada
if st.session_state.authenticated:
    st.markdown("---")
    st.markdown("© 2024 Scouting Players | Desarrollado para el Máster de Python Avanzado")
    