"""
Página de Reportes y Análisis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from utils.envios_db import buscar_envios, get_estadisticas_envios, get_sims_por_distribuidor
from utils.distribuidores_db import buscar_distribuidores, get_todos_distribuidores
from utils.supabase_client import get_supabase_client
from utils.timezone_config import get_fecha_actual_mexico

# Configuración de la página
st.set_page_config(
    page_title="Reportes - BAITEL",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Reportes y Análisis")
st.markdown("---")

# Tabs para diferentes reportes
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Dashboard General",
    "🔍 Consulta Personalizada",
    "👥 Por Distribuidor",
    "📅 Análisis Temporal"
])

# TAB 1: DASHBOARD GENERAL
with tab1:
    st.subheader("Dashboard General de Operaciones")
    
    # Obtener estadísticas
    with st.spinner("Cargando estadísticas..."):
        stats_envios = get_estadisticas_envios()
        
        # Obtener datos de distribuidores
        supabase = get_supabase_client()
        dist_activos = supabase.table('distribuidores').select('*', count='exact').eq('estatus', 'ACTIVO').execute()
        
        # Actividad últimos 30 días
        hace_30_dias = (get_fecha_actual_mexico() - timedelta(days=30)).isoformat()
        envios_30d = supabase.table('envios')\
            .select('*', count='exact')\
            .gte('fecha_envio', hace_30_dias)\
            .eq('estatus', 'ACTIVO')\
            .execute()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📱 Total SIMs Registradas", f"{stats_envios['total']:,}")
    
    with col2:
        st.metric("✅ SIMs Activas", f"{stats_envios['activos']:,}")
    
    with col3:
        st.metric("👥 Distribuidores Activos", f"{dist_activos.count:,}")
    
    with col4:
        st.metric("📥 Asignaciones (30 días)", f"{envios_30d.count:,}")
    
    st.markdown("---")
    
    # Gráficas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución de SIMs por Estatus")
        
        fig_estatus = go.Figure(data=[go.Pie(
            labels=['Activas', 'Reasignadas', 'Canceladas'],
            values=[
                stats_envios['activos'],
                stats_envios['reasignados'],
                stats_envios['cancelados']
            ],
            hole=.4,
            marker=dict(colors=['#28a745', '#ffc107', '#dc3545'])
        )])
        
        fig_estatus.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_estatus, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top 10 Distribuidores")
        
        # Obtener top distribuidores
        top_dist = supabase.table('envios')\
            .select('codigo_bt, nombre_distribuidor')\
            .eq('estatus', 'ACTIVO')\
            .execute()
        
        if top_dist.data:
            df_top = pd.DataFrame(top_dist.data)
            top_10 = df_top.groupby(['codigo_bt', 'nombre_distribuidor']).size()\
                .reset_index(name='total')\
                .sort_values('total', ascending=False)\
                .head(10)
            
            fig_top = px.bar(
                top_10,
                x='total',
                y='codigo_bt',
                orientation='h',
                text='total',
                color='total',
                color_continuous_scale='Blues'
            )
            
            fig_top.update_layout(
                height=350,
                showlegend=False,
                xaxis_title="SIMs Asignadas",
                yaxis_title="",
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            fig_top.update_traces(textposition='outside')
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("Sin datos de envíos")
    
    st.markdown("---")
    
    # Actividad por día (últimos 30 días)
    st.subheader("📈 Actividad Diaria (Últimos 30 Días)")
    
    envios_recientes = supabase.table('envios')\
        .select('fecha_envio, iccid')\
        .gte('fecha_envio', hace_30_dias)\
        .eq('estatus', 'ACTIVO')\
        .execute()
    
    if envios_recientes.data:
        df_actividad = pd.DataFrame(envios_recientes.data)
        df_actividad['fecha_envio'] = pd.to_datetime(df_actividad['fecha_envio'])
        actividad_diaria = df_actividad.groupby('fecha_envio').size().reset_index(name='cantidad')
        
        fig_linea = px.line(
            actividad_diaria,
            x='fecha_envio',
            y='cantidad',
            labels={'fecha_envio': 'Fecha', 'cantidad': 'SIMs Asignadas'},
            markers=True
        )
        
        fig_linea.update_layout(
            height=300,
            hovermode='x unified',
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig_linea, use_container_width=True)
    else:
        st.info("Sin actividad en los últimos 30 días")

# TAB 2: CONSULTA PERSONALIZADA
with tab2:
    st.subheader("Consulta Personalizada de Envíos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        iccid_buscar = st.text_input(
            "ICCID (parcial)",
            placeholder="895214006370...",
            help="Buscar por ICCID completo o parcial"
        )
    
    with col2:
        codigo_bt_buscar = st.text_input(
            "Código BT",
            placeholder="BT032-SAYULA",
            help="Buscar por código de distribuidor"
        )
    
    with col3:
        estatus_buscar = st.selectbox(
            "Estatus",
            ["TODOS", "ACTIVO", "REASIGNADO", "CANCELADO"]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde",
            value=get_fecha_actual_mexico() - timedelta(days=30),
            help="Fecha inicial del rango (Zona horaria: México)"
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Fecha hasta",
            value=get_fecha_actual_mexico(),
            help="Fecha final del rango (Zona horaria: México)"
        )
    
    # Sin límite - obtener todos los registros que coincidan con los filtros
    st.info("ℹ️ El sistema traerá TODOS los registros que coincidan con los filtros, sin límites")
    
    if st.button("🔍 Buscar Envíos", type="primary"):
        with st.spinner("Buscando todos los registros que coincidan con los filtros..."):
            resultados = buscar_envios(
                iccid=iccid_buscar if iccid_buscar else None,
                codigo_bt=codigo_bt_buscar if codigo_bt_buscar else None,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                estatus=estatus_buscar if estatus_buscar != "TODOS" else None,
                limit=None  # Sin límite - obtener todos los registros
            )
        
        if resultados:
            st.success(f"✅ {len(resultados)} envío(s) encontrado(s)")
            
            # Mostrar tabla
            df = pd.DataFrame(resultados)
            df_display = df[['fecha_envio', 'iccid', 'codigo_bt', 'nombre_distribuidor', 'estatus']].copy()
            df_display.columns = ['Fecha', 'ICCID', 'Código BT', 'Distribuidor', 'Estatus']
            
            # Formatear fecha a DD/MM/YYYY
            df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Exportar
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"envios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("⚠️ No se encontraron envíos con esos criterios")

# TAB 3: POR DISTRIBUIDOR
with tab3:
    st.subheader("Consulta por Distribuidor")
    
    # Buscar distribuidor
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_dist = st.text_input(
            "Buscar distribuidor",
            placeholder="Código, nombre o plaza",
            key="query_dist_reporte"
        )
    
    with col2:
        filtro_dist = st.selectbox(
            "Estatus",
            ["ACTIVO", "TODOS", "BAJA", "SUSPENDIDO"],
            key="filtro_dist_reporte"
        )
    
    if query_dist:
        estatus_filtro = None if filtro_dist == "TODOS" else filtro_dist
        distribuidores = buscar_distribuidores(query=query_dist, estatus=estatus_filtro, limit=20)
        
        if distribuidores:
            df_dist = pd.DataFrame(distribuidores)
            
            # Seleccionar distribuidor
            codigo_seleccionado = st.selectbox(
                "Seleccionar distribuidor",
                df_dist['codigo_bt'].tolist(),
                format_func=lambda x: f"{x} - {df_dist[df_dist['codigo_bt']==x]['nombre'].values[0]}"
            )
            
            dist_info = df_dist[df_dist['codigo_bt'] == codigo_seleccionado].iloc[0]
            
            # Mostrar información del distribuidor
            st.markdown("---")
            st.markdown("### 📋 Información del Distribuidor")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Código BT", dist_info['codigo_bt'])
            with col2:
                st.metric("Nombre", dist_info['nombre'])
            with col3:
                st.metric("Plaza", dist_info['plaza'])
            with col4:
                st.metric("Estatus", dist_info['estatus'])
            
            # Obtener SIMs del distribuidor
            st.markdown("---")
            st.markdown("### 📱 SIMs Asignadas")
            
            sims_activas = get_sims_por_distribuidor(codigo_seleccionado, estatus='ACTIVO')
            sims_todas = get_sims_por_distribuidor(codigo_seleccionado, estatus='ACTIVO')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("SIMs Activas", len(sims_activas))
            
            with col2:
                # Calcular promedio mensual
                if sims_activas:
                    df_sims = pd.DataFrame(sims_activas)
                    df_sims['fecha_envio'] = pd.to_datetime(df_sims['fecha_envio'])
                    meses_activo = (datetime.now() - df_sims['fecha_envio'].min()).days / 30
                    promedio_mes = len(sims_activas) / max(meses_activo, 1)
                    st.metric("Promedio Mensual", f"{promedio_mes:.1f}")
            
            # Mostrar tabla de SIMs
            if sims_activas:
                df_sims_display = pd.DataFrame(sims_activas)
                df_sims_display = df_sims_display[['fecha_envio', 'iccid']].copy()
                df_sims_display.columns = ['Fecha', 'ICCID']
                
                st.dataframe(df_sims_display, use_container_width=True, hide_index=True)
                
                # Exportar
                csv = df_sims_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Descargar SIMs de {codigo_seleccionado}",
                    data=csv,
                    file_name=f"sims_{codigo_seleccionado}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Este distribuidor no tiene SIMs activas asignadas")
        else:
            st.warning("⚠️ No se encontraron distribuidores")

# TAB 4: ANÁLISIS TEMPORAL
with tab4:
    st.subheader("Análisis Temporal de Asignaciones")
    
    # Selector de vista
    vista = st.radio(
        "Tipo de análisis",
        ["📊 Análisis por Año/Mes", "📈 Análisis por Período"],
        horizontal=True
    )
    
    if vista == "📊 Análisis por Año/Mes":
        st.markdown("---")
        
        # Función con caché para cargar todos los datos con paginación
        @st.cache_data(ttl=3600)  # Cache por 1 hora
        def cargar_todos_envios():
            """Carga TODOS los registros de envíos usando paginación"""
            supabase = get_supabase_client()
            all_records = []
            offset = 0
            limit = 1000
            
            while True:
                response = supabase.table('envios')\
                    .select('fecha_envio, iccid, codigo_bt, nombre_distribuidor')\
                    .order('fecha_envio', desc=True)\
                    .limit(limit)\
                    .offset(offset)\
                    .execute()
                
                if not response.data:
                    break
                
                all_records.extend(response.data)
                offset += limit
                
                # Si obtenemos menos registros que el límite, es la última página
                if len(response.data) < limit:
                    break
            
            return all_records
        
        # Obtener todos los datos con caché
        with st.spinner("Cargando datos..."):
            datos_envios = cargar_todos_envios()
        
        # Mostrar mensaje de confirmación
        st.success(f"✅ Datos cargados: {len(datos_envios):,} registros")
        
        if datos_envios:
            df_all = pd.DataFrame(datos_envios)
            df_all['fecha_envio'] = pd.to_datetime(df_all['fecha_envio'])
            df_all['año'] = df_all['fecha_envio'].dt.year
            df_all['mes'] = df_all['fecha_envio'].dt.month
            df_all['mes_nombre'] = df_all['fecha_envio'].dt.strftime('%B')
            
            # Información de datos cargados
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.success(f"✅ Datos cargados: **{len(df_all):,} registros** de {len(df_all['codigo_bt'].unique())} distribuidores")
            with col2:
                st.info(f"📅 Período: {df_all['fecha_envio'].min().strftime('%Y-%m-%d')} a {df_all['fecha_envio'].max().strftime('%Y-%m-%d')}")
            with col3:
                if st.button("🔄 Recargar", help="Forzar recarga de datos desde la base de datos"):
                    st.cache_data.clear()
                    st.rerun()
            
            st.markdown("---")
            
            # Obtener años y distribuidores disponibles
            años_disponibles = sorted(df_all['año'].unique(), reverse=True)
            distribuidores_disponibles = sorted(df_all['codigo_bt'].unique())
            
            # Selectores mejorados
            st.markdown("""
            <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                <p style='margin: 0; color: #1976d2;'>
                    <strong>📈 Visualiza el surtido mensual de SIMs</strong><br>
                    <small>Selecciona un año para ver el surtido general, o filtra por distribuidor específico</small>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                año_seleccionado = st.selectbox(
                    "📅 Año",
                    años_disponibles,
                    key="año_selector",
                    help="Selecciona el año a analizar"
                )
            
            with col2:
                # Campo de búsqueda para filtrar distribuidores
                busqueda_dist = st.text_input(
                    "🔍 Buscar distribuidor",
                    placeholder="Escribe para filtrar (ej: BT120, TLALIXCOYAN, XALAPA...)",
                    key="busqueda_distribuidor",
                    help="Filtra la lista de distribuidores escribiendo parte del código o nombre"
                )
                
                # Filtrar distribuidores según búsqueda
                if busqueda_dist:
                    distribuidores_filtrados = [
                        d for d in distribuidores_disponibles 
                        if busqueda_dist.upper() in d.upper()
                    ]
                    if distribuidores_filtrados:
                        opciones_distribuidor = ["TODOS LOS DISTRIBUIDORES"] + distribuidores_filtrados
                    else:
                        opciones_distribuidor = ["TODOS LOS DISTRIBUIDORES"]
                        st.warning(f"⚠️ No se encontraron distribuidores con '{busqueda_dist}'")
                else:
                    opciones_distribuidor = ["TODOS LOS DISTRIBUIDORES"] + distribuidores_disponibles
                
                distribuidor_seleccionado = st.selectbox(
                    "👥 Distribuidor",
                    opciones_distribuidor,
                    key="distribuidor_selector",
                    help="Selecciona TODOS para ver el surtido general, o un distribuidor específico"
                )
            
            st.markdown("---")
            
            # Filtrar por año
            df_filtrado = df_all[df_all['año'] == año_seleccionado].copy()
            
            # Filtrar por distribuidor si no es TODOS
            if distribuidor_seleccionado != "TODOS LOS DISTRIBUIDORES":
                df_filtrado = df_filtrado[df_filtrado['codigo_bt'] == distribuidor_seleccionado].copy()
                titulo_grafica = f'📈 {distribuidor_seleccionado} - {año_seleccionado}'
            else:
                titulo_grafica = f'📈 Surtido General Mensual - {año_seleccionado}'
            
            # Agrupar por mes
            df_mensual = df_filtrado.groupby(['mes', 'mes_nombre']).size().reset_index(name='cantidad')
            df_mensual = df_mensual.sort_values('mes')
            
            # Crear gráfica de barras
            fig_barras = px.bar(
                df_mensual,
                x='mes_nombre',
                y='cantidad',
                text='cantidad',
                labels={'mes_nombre': 'Mes', 'cantidad': 'SIMs Surtidos'},
                title=titulo_grafica,
                color='cantidad',
                color_continuous_scale='Blues'
            )
            
            fig_barras.update_layout(
                height=500,
                showlegend=False,
                xaxis_title="Mes",
                yaxis_title="Cantidad de SIMs",
                hovermode='x unified'
            )
            
            fig_barras.update_traces(
                textposition='outside',
                texttemplate='%{text:,}'
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
            
            # Métricas del año
            st.markdown("---")
            if distribuidor_seleccionado != "TODOS LOS DISTRIBUIDORES":
                st.markdown(f"### 📊 Estadísticas {distribuidor_seleccionado} - {año_seleccionado}")
            else:
                st.markdown(f"### 📊 Estadísticas Generales {año_seleccionado}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_periodo = df_filtrado.shape[0]
                st.metric("Total SIMs", f"{total_periodo:,}")
            
            with col2:
                if len(df_mensual) > 0:
                    promedio_mes = total_periodo / len(df_mensual)
                    st.metric("Promedio/Mes", f"{promedio_mes:,.0f}")
                else:
                    st.metric("Promedio/Mes", "0")
            
            with col3:
                if len(df_mensual) > 0:
                    mes_max = df_mensual.loc[df_mensual['cantidad'].idxmax()]
                    st.metric("Mes Máximo", f"{mes_max['mes_nombre']}")
                else:
                    st.metric("Mes Máximo", "N/A")
            
            with col4:
                if len(df_mensual) > 0:
                    st.metric("Cantidad Máxima", f"{mes_max['cantidad']:,}")
                else:
                    st.metric("Cantidad Máxima", "0")
            
            # Tabla de datos
            st.markdown("---")
            st.markdown("### 📋 Detalle Mensual")
            
            df_tabla = df_mensual[['mes_nombre', 'cantidad']].copy()
            df_tabla.columns = ['Mes', 'SIMs Surtidos']
            df_tabla['SIMs Surtidos'] = df_tabla['SIMs Surtidos'].apply(lambda x: f"{x:,}")
            
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            
            # Exportar relación completa de ICCIDs
            st.markdown("---")
            st.markdown("📄 **Exportar Datos**")
            
            # Preparar datos para exportación con información detallada
            df_exportar = df_filtrado[['iccid', 'codigo_bt', 'nombre_distribuidor', 'fecha_envio']].copy()
            df_exportar['fecha_envio'] = df_exportar['fecha_envio'].dt.strftime('%Y-%m-%d')
            df_exportar.columns = ['ICCID', 'Código BT', 'Nombre Distribuidor', 'Fecha de Envío']
            
            # Crear CSV
            csv = df_exportar.to_csv(index=False).encode('utf-8-sig')  # utf-8-sig para Excel
            
            # Nombre de archivo dinámico
            if distribuidor_seleccionado != "TODOS LOS DISTRIBUIDORES":
                nombre_archivo = f"iccids_{distribuidor_seleccionado.replace(' ', '_')}_{año_seleccionado}.csv"
                label_boton = f"📅 Descargar ICCIDs de {distribuidor_seleccionado} ({total_periodo:,} registros)"
            else:
                nombre_archivo = f"iccids_todos_{año_seleccionado}.csv"
                label_boton = f"📅 Descargar Todos los ICCIDs de {año_seleccionado} ({total_periodo:,} registros)"
            
            st.download_button(
                label=label_boton,
                data=csv,
                file_name=nombre_archivo,
                mime="text/csv",
                help="Descarga la relación completa de ICCIDs con detalles de distribuidor y fecha"
            )
        else:
            st.warning("⚠️ No hay datos disponibles")
    
    else:
        # Análisis por período (código original)
        # Selector de período
        col1, col2 = st.columns(2)
        
        with col1:
            periodo = st.selectbox(
                "Período de análisis",
                ["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Último año", "Personalizado"]
            )
        
        with col2:
            if periodo == "Personalizado":
                fecha_inicio = st.date_input(
                    "Fecha inicio",
                    value=get_fecha_actual_mexico() - timedelta(days=30)
                )
                fecha_fin = st.date_input(
                    "Fecha fin",
                    value=get_fecha_actual_mexico()
                )
            else:
                dias = {"Últimos 7 días": 7, "Últimos 30 días": 30, "Últimos 90 días": 90, "Último año": 365}[periodo]
                fecha_inicio = get_fecha_actual_mexico() - timedelta(days=dias)
                fecha_fin = get_fecha_actual_mexico()
        
        if st.button("📊 Generar Análisis", type="primary"):
            with st.spinner("Generando análisis..."):
                supabase = get_supabase_client()
                
                # Obtener datos del período
                envios_periodo = supabase.table('envios')\
                    .select('fecha_envio, codigo_bt, iccid, estatus')\
                    .gte('fecha_envio', fecha_inicio.isoformat())\
                    .lte('fecha_envio', fecha_fin.isoformat())\
                    .execute()
                
                if envios_periodo.data:
                    df = pd.DataFrame(envios_periodo.data)
                    df['fecha_envio'] = pd.to_datetime(df['fecha_envio'])
                    
                    # Métricas del período
                    st.markdown("### 📊 Resumen del Período")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Asignaciones", len(df))
                    
                    with col2:
                        activas = len(df[df['estatus'] == 'ACTIVO'])
                        st.metric("Activas", activas)
                    
                    with col3:
                        distribuidores_unicos = df['codigo_bt'].nunique()
                        st.metric("Distribuidores", distribuidores_unicos)
                    
                    with col4:
                        promedio_dia = len(df) / max((fecha_fin - fecha_inicio).days, 1)
                        st.metric("Promedio/Día", f"{promedio_dia:.1f}")
                    
                    st.markdown("---")
                    
                    # Gráfica de tendencia
                    st.markdown("### 📈 Tendencia de Asignaciones")
                    
                    df_diario = df.groupby('fecha_envio').size().reset_index(name='cantidad')
                    
                    fig = px.area(
                        df_diario,
                        x='fecha_envio',
                        y='cantidad',
                        labels={'fecha_envio': 'Fecha', 'cantidad': 'Asignaciones'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    
                    fig.update_layout(height=400, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Top distribuidores del período
                    st.markdown("### 🏆 Top Distribuidores del Período")
                    
                    top_periodo = df.groupby('codigo_bt').size()\
                        .reset_index(name='asignaciones')\
                        .sort_values('asignaciones', ascending=False)\
                        .head(15)
                    
                    fig_top = px.bar(
                        top_periodo,
                        x='asignaciones',
                        y='codigo_bt',
                        orientation='h',
                        text='asignaciones',
                        color='asignaciones',
                        color_continuous_scale='Viridis'
                    )
                    
                    fig_top.update_layout(
                        height=500,
                        showlegend=False,
                        xaxis_title="Asignaciones",
                        yaxis_title="",
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    fig_top.update_traces(textposition='outside')
                    st.plotly_chart(fig_top, use_container_width=True)
                    
                    # Exportar análisis
                    st.markdown("---")
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Datos Completos",
                        data=csv,
                        file_name=f"analisis_{fecha_inicio}_{fecha_fin}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No hay datos en el período seleccionado")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>💡 Tip: Exporta los reportes a CSV para análisis más profundos en Excel</small>
</div>
""", unsafe_allow_html=True)
