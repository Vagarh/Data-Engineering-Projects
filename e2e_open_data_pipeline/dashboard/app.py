import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine

# Configuración de página
st.set_page_config(
    page_title="Dashboard Accidentes de Tránsito", 
    page_icon="🚦",
    layout="wide"
)

# Estilado CSS (Dark Theme Moderno opcional, apoyado en el config nativo)
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .kpi-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚦 Análisis de Incidentes Viales (E2E Open Data)")
st.markdown("Bienvenido al proyecto analítico de Portafolio: Pipeline robusto con **Airflow** ➔ **PostgreSQL** ➔ **Streamlit**.")

@st.cache_resource
def init_connection():
    db_user = os.getenv("DB_USER", "airflow")
    db_pass = os.getenv("DB_PASS", "airflow")
    db_host = os.getenv("DB_HOST", "postgres") # localhost si es fuera de docker
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "dw_portafolio")
    
    engine = create_engine(f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')
    return engine

try:
    engine = init_connection()
    # Cargamos datos de la base de datos
    query = "SELECT * FROM public.accidentes_transito"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        st.warning("⚠️ La base de datos está activa, pero no tiene registros aún. Esto es normal en el primer inicio. ¡Ejecuta el pipeline (DAG) en la UI de Airflow primero!")
    else:
        st.sidebar.header("Filtros")
        
        # Filtro comuna
        comunas_disponibles = sorted(df['comuna'].dropna().unique().tolist())
        comunas = ["Todas"] + comunas_disponibles
        comuna_sel = st.sidebar.selectbox("Filtrar por Comuna", comunas)
        
        # Filtro Gravedad
        gravedades = ["Todas"] + df['gravedad_accidente'].dropna().unique().tolist()
        gravedad_sel = st.sidebar.selectbox("Filtrar por Gravedad", gravedades)
        
        # Aplicamos Filtros
        df_filtered = df.copy()
        if comuna_sel != "Todas":
            df_filtered = df_filtered[df_filtered['comuna'] == comuna_sel]
        if gravedad_sel != "Todas":
            df_filtered = df_filtered[df_filtered['gravedad_accidente'] == gravedad_sel]
        
        st.write(f"Mostrando **{len(df_filtered)}** incidentes filtrados.")
        
        # Sección KPIs (Métricas principales)
        st.subheader("Métricas Principales")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.markdown(f"<div class='kpi-card'><h4>Total Analizado</h4><h2>{len(df_filtered)}</h2></div>", unsafe_allow_html=True)
        
        comuna_mas_afectada = df_filtered['comuna'].mode()[0] if not df_filtered.empty else "N/A"
        col2.markdown(f"<div class='kpi-card'><h4>Zoná Crítica</h4><h2>{comuna_mas_afectada}</h2></div>", unsafe_allow_html=True)
        
        clase_mas_comun = df_filtered['clase_accidente'].mode()[0] if not df_filtered.empty else "N/A"
        col3.markdown(f"<div class='kpi-card'><h4>Clase más Común</h4><h2>{clase_mas_comun}</h2></div>", unsafe_allow_html=True)
        
        # Opcional si hay hora en formato string
        try:
            df_filtered['hora_str'] = df_filtered['hora_accidente'].astype(str)
            hora_freq = df_filtered['hora_str'].apply(lambda x: x[:2]).mode()[0] + ":00" if not df_filtered.empty else "N/A"
        except:
            hora_freq = "N/A"
        col4.markdown(f"<div class='kpi-card'><h4>Hora Pico</h4><h2>{hora_freq}</h2></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Dividir layout
        map_col, chart_col = st.columns([1.5, 1])
        
        with map_col:
            st.subheader("🌍 Mapa de Calor de Incidentes")
            map_df = df_filtered.dropna(subset=['latitud', 'longitud']).copy()
            # Streamlit map necesita obligatoriamente ['lat','lon']
            map_df = map_df.rename(columns={'latitud': 'lat', 'longitud': 'lon'})
            
            # Mapbox (Scattermapbox es mejor visualmente)
            if not map_df.empty:
                fig_map = px.scatter_mapbox(map_df, lat="lat", lon="lon", 
                                          hover_name="clase_accidente", 
                                          hover_data=["fecha_accidente", "barrio"],
                                          color_discrete_sequence=["#e74c3c"], zoom=11)
                fig_map.update_layout(mapbox_style="carto-darkmatter") # Tema oscuro moderno
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("No hay coordenadas válidas para mostrar en el mapa.")
                
        with chart_col:
            st.subheader("📊 Tipos de Gravedad")
            gravedad_counts = df_filtered['gravedad_accidente'].value_counts().reset_index()
            gravedad_counts.columns = ['Gravedad', 'Incidentes']
            
            fig_pie = px.pie(gravedad_counts, values='Incidentes', names='Gravedad',
                             hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            st.subheader("📈 Clases de Accidentes")
            clase_counts = df_filtered['clase_accidente'].value_counts().reset_index().head(5)
            clase_counts.columns = ['Clase', 'Cantidad']
            fig_bar = px.bar(clase_counts, x='Cantidad', y='Clase', orientation='h', color='Clase', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.divider()
        st.subheader("🔍 Explorador de Registros (Base de datos)")
        st.dataframe(df_filtered.head(100), use_container_width=True)

except Exception as e:
    st.error(f"❌ Ocurrió un error en la conexión a la base de datos: {str(e)}")
    st.info("Asegúrate de que PostgreSQL está corriendo en Docker y las variables (.env) son correctas.")
