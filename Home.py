"""
Sistema de Inventario de SIMs - BAITEL
Página Principal / Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.supabase_client import get_supabase_client
from utils.distribuidores_db import get_estadisticas_distribuidores

# Configuración de la página
st.set_page_config(
    page_title="BAITEL - Sistema de Inventario SIMs",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .big-metric {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📱 Sistema de Inventario de SIMs - BAITEL")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/4472C4/FFFFFF?text=BAITEL", use_column_width=True)
    st.markdown("### 🔧 Navegación")
    st.info("""
    **Funciones disponibles:**
    - 📊 Dashboard (esta página)
    - 📥 Captura de SIMs
    - 👥 Administrar Distribuidores
    - 🔄 Correcciones
    - 📈 Reportes
    """)
    
    st.markdown("---")
    st.markdown(f"**Usuario:** Almacén BAITEL")
    st.markdown(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y')}")

# ⚡ ACCIONES RÁPIDAS (MOVIDO AL INICIO)
st.subheader("⚡ Acciones Rápidas")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Capturar SIMs", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📥_Captura_SIMs.py")

with col2:
    if st.button("👥 Nuevo Distribuidor", use_container_width=True):
        st.switch_page("pages/2_👥_Administrar_Distribuidores.py")

with col3:
    if st.button("📊 Ver Reportes", use_container_width=True):
        st.switch_page("pages/4_📊_Reportes.py")

st.markdown("---")

# Función para obtener datos del dashboard
@st.cache_data(ttl=60)
def get_dashboard_data():
    """Obtener datos para el dashboard"""
    try:
        supabase = get_supabase_client()
        
        # Estadísticas de distribuidores
        stats_dist = get_estadisticas_distribuidores()
        
        # Envíos totales
        envios_total = supabase.table('envios').select('*', count='exact').execute()
        
        # Envíos activos
        envios_activos = supabase.table('envios')\
            .select('*', count='exact')\
            .eq('estatus', 'ACTIVO')\
            .execute()
        
        # Actividad últimos 30 días
        hace_30_dias = (datetime.now() - timedelta(days=30)).date().isoformat()
        actividad_reciente = supabase.table('envios')\
            .select('fecha_envio, codigo_bt, iccid')\
            .gte('fecha_envio', hace_30_dias)\
            .eq('estatus', 'ACTIVO')\
            .execute()
        
        # Top 10 distribuidores
        top_distribuidores = supabase.table('envios')\
            .select('codigo_bt, nombre_distribuidor')\
            .eq('estatus', 'ACTIVO')\
            .execute()
        
        return {
            'stats_dist': stats_dist,
            'envios_total': envios_total.count,
            'envios_activos': envios_activos.count,
            'actividad_reciente': actividad_reciente.data,
            'top_distribuidores': top_distribuidores.data
        }
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

# Cargar datos
with st.spinner("Cargando dashboard..."):
    data = get_dashboard_data()

if data:
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Distribuidores Activos",
            value=data['stats_dist']['activos'],
            delta=f"Total: {data['stats_dist']['total']}"
        )
    
    with col2:
        st.metric(
            label="📱 SIMs Asignadas (Total)",
            value=f"{data['envios_total']:,}",
            delta="Histórico completo"
        )
    
    with col3:
        st.metric(
            label="✅ SIMs Activas",
            value=f"{data['envios_activos']:,}",
            delta="En circulación"
        )
    
    with col4:
        actividad_hoy = len([x for x in data['actividad_reciente'] 
                            if x.get('fecha_envio', '').startswith(datetime.now().date().isoformat())])
        st.metric(
            label="📥 Asignaciones Hoy",
            value=actividad_hoy,
            delta="Últimas 24h"
        )
    
    st.markdown("---")
    
    # Gráficas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución de Distribuidores")
        
        # Gráfica de pie
        fig_dist = go.Figure(data=[go.Pie(
            labels=['Activos', 'Baja', 'Suspendidos'],
            values=[
                data['stats_dist']['activos'],
                data['stats_dist']['baja'],
                data['stats_dist']['suspendidos']
            ],
            hole=.4,
            marker=dict(colors=['#28a745', '#dc3545', '#ffc107'])
        )])
        
        fig_dist.update_layout(
            showlegend=True,
            height=300,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        st.subheader("📈 Actividad Últimos 30 Días")
        
        if data['actividad_reciente']:
            # Agrupar por fecha
            df_actividad = pd.DataFrame(data['actividad_reciente'])
            df_actividad['fecha_envio'] = pd.to_datetime(df_actividad['fecha_envio'])
            actividad_por_dia = df_actividad.groupby('fecha_envio').size().reset_index(name='cantidad')
            actividad_por_dia.rename(columns={'fecha_envio': 'fecha'}, inplace=True)
            
            fig_actividad = px.line(
                actividad_por_dia,
                x='fecha',
                y='cantidad',
                labels={'fecha': 'Fecha', 'cantidad': 'SIMs Asignadas'},
                markers=True
            )
            
            fig_actividad.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=30, b=20),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_actividad, use_container_width=True)
        else:
            st.info("Sin actividad en los últimos 30 días")
    
    st.markdown("---")
    
    # Top distribuidores
    st.subheader("🏆 Top 10 Distribuidores (SIMs Activas)")
    
    if data['top_distribuidores']:
        df_top = pd.DataFrame(data['top_distribuidores'])
        top_10 = df_top.groupby(['codigo_bt', 'nombre_distribuidor']).size()\
            .reset_index(name='total_sims')\
            .sort_values('total_sims', ascending=False)\
            .head(10)
        
        fig_top = px.bar(
            top_10,
            x='total_sims',
            y='codigo_bt',
            orientation='h',
            text='total_sims',
            labels={'codigo_bt': 'Distribuidor', 'total_sims': 'SIMs Asignadas'},
            color='total_sims',
            color_continuous_scale='Blues'
        )
        
        fig_top.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Cantidad de SIMs",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'}
        )
        
        fig_top.update_traces(textposition='outside')
        
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("Sin datos de envíos aún")

else:
    st.error("Error al cargar los datos del dashboard")
    st.info("Verifica tu conexión a Supabase")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Sistema de Inventario de SIMs - BAITEL © 2025<br>
    Desarrollado para optimizar el control de distribución</small>
</div>
""", unsafe_allow_html=True)
