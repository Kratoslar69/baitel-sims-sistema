"""
Página de Correcciones y Reasignaciones de SIMs
"""

import streamlit as st
import pandas as pd
from utils.envios_db import (
    get_envio_by_iccid,
    corregir_distribuidor_envio,
    reasignar_sim,
    buscar_envios
)
from utils.distribuidores_db import buscar_distribuidores, get_distribuidor_by_id

# Configuración de la página
st.set_page_config(
    page_title="Correcciones - BAITEL",
    page_icon="🔄",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
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
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔄 Correcciones y Reasignaciones")
st.markdown("---")

# Tabs para los dos escenarios
tab1, tab2 = st.tabs(["✏️ Corrección Simple", "🔄 Reasignación con Historial"])

# TAB 1: CORRECCIÓN SIMPLE
with tab1:
    st.subheader("Corregir Error de Captura")
    
    st.markdown("""
    <div class="info-box">
        <strong>📋 Escenario:</strong> El almacenista se equivocó de distribuidor hace minutos<br>
        <strong>🎯 Acción:</strong> Cambiar el distribuidor asignado (sin mantener historial)<br>
        <strong>⚡ Uso:</strong> Frecuente - Errores de captura recientes
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Paso 1: Buscar ICCIDs (MASIVO)
    st.markdown("### 🔍 Paso 1: Buscar ICCIDs a Corregir")
    
    st.info("💡 **Captura Masiva:** Puedes pegar múltiples ICCIDs separados por saltos de línea, comas o espacios")
    
    iccids_corregir_text = st.text_area(
        "ICCIDs a corregir (uno por línea o separados por comas)",
        placeholder="8952140063703946403\n8952140063703946404\n8952140063703946405",
        help="Pega todos los ICCIDs que fueron asignados incorrectamente",
        height=150,
        key="iccids_corregir"
    )
    
    if iccids_corregir_text:
        # Procesar ICCIDs (limpiar y separar)
        import re
        iccids_list = re.split(r'[,\s\n]+', iccids_corregir_text.strip())
        iccids_list = [iccid.strip() for iccid in iccids_list if iccid.strip()]
        
        st.info(f"📊 Total de ICCIDs a procesar: **{len(iccids_list)}**")
        
        if st.button("🔍 Buscar ICCIDs", type="secondary"):
            with st.spinner("Buscando ICCIDs..."):
                resultados = []
                for iccid in iccids_list:
                    envio = get_envio_by_iccid(iccid)
                    if envio:
                        resultados.append({
                            'iccid': iccid,
                            'encontrado': True,
                            'codigo_bt': envio['codigo_bt'],
                            'nombre_distribuidor': envio['nombre_distribuidor'],
                            'estatus': envio['estatus'],
                            'distribuidor_id': envio['distribuidor_id']
                        })
                    else:
                        resultados.append({
                            'iccid': iccid,
                            'encontrado': False,
                            'codigo_bt': 'N/A',
                            'nombre_distribuidor': 'N/A',
                            'estatus': 'NO ENCONTRADO',
                            'distribuidor_id': None
                        })
                
                # Guardar en session_state
                st.session_state['iccids_correccion'] = resultados
        
        # Mostrar resultados si existen
        if 'iccids_correccion' in st.session_state:
            resultados = st.session_state['iccids_correccion']
            df_resultados = pd.DataFrame(resultados)
            
            # Estadísticas
            encontrados = df_resultados['encontrado'].sum()
            no_encontrados = len(df_resultados) - encontrados
            activos = len(df_resultados[df_resultados['estatus'] == 'ACTIVO'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Encontrados", encontrados)
            with col2:
                st.metric("❌ No Encontrados", no_encontrados)
            with col3:
                st.metric("🟢 Activos (Corregibles)", activos)
            
            # Mostrar tabla
            st.markdown("### 📋 ICCIDs Encontrados")
            df_display = df_resultados[['iccid', 'codigo_bt', 'nombre_distribuidor', 'estatus']].copy()
            df_display.columns = ['ICCID', 'Código BT Actual', 'Distribuidor Actual', 'Estatus']
            
            # Colorear por estatus
            def highlight_status(row):
                if row['Estatus'] == 'ACTIVO':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Estatus'] == 'NO ENCONTRADO':
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return ['background-color: #fff3cd'] * len(row)
            
            st.dataframe(
                df_display.style.apply(highlight_status, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            if activos > 0:
                st.markdown("---")
                
                # Paso 2: Seleccionar nuevo distribuidor
                st.markdown("### 🎯 Paso 2: Seleccionar Distribuidor Correcto (Para Todos)")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    query_nuevo = st.text_input(
                        "Buscar distribuidor correcto",
                        placeholder="Código, nombre o plaza",
                        key="query_nuevo_correccion"
                    )
                
                with col2:
                    filtro_nuevo = st.selectbox(
                        "Estatus",
                        ["ACTIVO", "TODOS", "SUSPENDIDO", "BAJA"],
                        key="filtro_nuevo_correccion"
                    )
                
                if query_nuevo:
                    estatus_filtro = None if filtro_nuevo == "TODOS" else filtro_nuevo
                    distribuidores = buscar_distribuidores(query=query_nuevo, estatus=estatus_filtro, limit=20)
                    
                    if distribuidores:
                        df_dist = pd.DataFrame(distribuidores)
                        
                        # Mostrar tabla
                        df_display = df_dist[['codigo_bt', 'nombre', 'plaza', 'estatus']].copy()
                        df_display.columns = ['Código BT', 'Nombre', 'Plaza', 'Estatus']
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                        
                        # Seleccionar
                        codigo_nuevo = st.selectbox(
                            "Seleccionar distribuidor correcto",
                            df_dist['codigo_bt'].tolist(),
                            format_func=lambda x: f"{x} - {df_dist[df_dist['codigo_bt']==x]['nombre'].values[0]}",
                            key="codigo_nuevo_correccion"
                        )
                        
                        dist_nuevo = df_dist[df_dist['codigo_bt'] == codigo_nuevo].iloc[0].to_dict()
                        
                        motivo = st.text_input(
                            "Motivo de la corrección",
                            placeholder="Ej: Error de captura masiva, se confundió de distribuidor",
                            key="motivo_correccion"
                        )
                        
                        # Confirmar corrección
                        st.markdown("---")
                        st.markdown("### ✅ Confirmar Corrección Masiva")
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <strong>✅ Distribuidor Correcto:</strong><br>
                            {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}<br><br>
                            <strong>📊 Se corregirán {activos} ICCIDs ACTIVOS</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("💾 Aplicar Corrección Masiva", type="primary", use_container_width=True):
                            if not motivo:
                                st.error("❌ Por favor indica el motivo de la corrección")
                            else:
                                try:
                                    exitosos = 0
                                    errores = 0
                                    
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    iccids_activos = [r for r in resultados if r['estatus'] == 'ACTIVO']
                                    
                                    for idx, resultado in enumerate(iccids_activos):
                                        try:
                                            status_text.text(f"Procesando {idx+1}/{len(iccids_activos)}: {resultado['iccid']}")
                                            
                                            corregir_distribuidor_envio(
                                                iccid=resultado['iccid'],
                                                nuevo_distribuidor_id=dist_nuevo['id'],
                                                nuevo_codigo_bt=dist_nuevo['codigo_bt'],
                                                nuevo_nombre=dist_nuevo['nombre'],
                                                motivo=motivo,
                                                usuario="Almacén BAITEL"
                                            )
                                            exitosos += 1
                                        except Exception as e:
                                            errores += 1
                                            st.warning(f"⚠️ Error en {resultado['iccid']}: {str(e)}")
                                        
                                        progress_bar.progress((idx + 1) / len(iccids_activos))
                                    
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.success(f"✅ Corrección masiva completada: {exitosos} exitosos, {errores} errores")
                                    st.balloons()
                                    
                                    st.markdown(f"""
                                    <div class="success-box">
                                        <h4>✅ Corrección Masiva Completada</h4>
                                        <p><strong>ICCIDs Corregidos:</strong> {exitosos}<br>
                                        <strong>Errores:</strong> {errores}<br>
                                        <strong>Nuevo Distribuidor:</strong> {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}<br>
                                        <strong>Motivo:</strong> {motivo}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Limpiar session_state
                                    del st.session_state['iccids_correccion']
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al aplicar corrección masiva: {str(e)}")
                    else:
                        st.warning("⚠️ No se encontraron distribuidores")
            else:
                st.warning("⚠️ No hay ICCIDs ACTIVOS para corregir")

# TAB 2: REASIGNACIÓN CON HISTORIAL
with tab2:
    st.subheader("Reasignar SIM con Historial")
    
    st.markdown("""
    <div class="warning-box">
        <strong>📋 Escenario:</strong> Paquete devuelto por mensajería o SIM recuperada<br>
        <strong>🎯 Acción:</strong> Reasignar a nuevo distribuidor manteniendo historial completo<br>
        <strong>⚡ Uso:</strong> Raro - Devoluciones o recuperaciones
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Paso 1: Buscar ICCIDs (MASIVO)
    st.markdown("### 🔍 Paso 1: Buscar ICCIDs a Reasignar")
    
    st.info("💡 **Captura Masiva:** Puedes pegar múltiples ICCIDs separados por saltos de línea, comas o espacios")
    
    iccids_reasignar_text = st.text_area(
        "ICCIDs a reasignar (uno por línea o separados por comas)",
        placeholder="8952140063703946403\n8952140063703946404\n8952140063703946405",
        help="Pega todos los ICCIDs que serán reasignados",
        height=150,
        key="iccids_reasignar"
    )
    
    if iccids_reasignar_text:
        # Procesar ICCIDs
        import re
        iccids_list = re.split(r'[,\s\n]+', iccids_reasignar_text.strip())
        iccids_list = [iccid.strip() for iccid in iccids_list if iccid.strip()]
        
        st.info(f"📊 Total de ICCIDs a procesar: **{len(iccids_list)}**")
        
        if st.button("🔍 Buscar ICCIDs", type="secondary", key="buscar_reasignar"):
            with st.spinner("Buscando ICCIDs..."):
                resultados = []
                for iccid in iccids_list:
                    envio = get_envio_by_iccid(iccid)
                    if envio:
                        resultados.append({
                            'iccid': iccid,
                            'encontrado': True,
                            'codigo_bt': envio['codigo_bt'],
                            'nombre_distribuidor': envio['nombre_distribuidor'],
                            'estatus': envio['estatus'],
                            'distribuidor_id': envio['distribuidor_id']
                        })
                    else:
                        resultados.append({
                            'iccid': iccid,
                            'encontrado': False,
                            'codigo_bt': 'N/A',
                            'nombre_distribuidor': 'N/A',
                            'estatus': 'NO ENCONTRADO',
                            'distribuidor_id': None
                        })
                
                st.session_state['iccids_reasignacion'] = resultados
        
        # Mostrar resultados
        if 'iccids_reasignacion' in st.session_state:
            resultados = st.session_state['iccids_reasignacion']
            df_resultados = pd.DataFrame(resultados)
            
            # Estadísticas
            encontrados = df_resultados['encontrado'].sum()
            no_encontrados = len(df_resultados) - encontrados
            activos = len(df_resultados[df_resultados['estatus'] == 'ACTIVO'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Encontrados", encontrados)
            with col2:
                st.metric("❌ No Encontrados", no_encontrados)
            with col3:
                st.metric("🟢 Activos (Reasignables)", activos)
            
            # Mostrar tabla
            st.markdown("### 📋 ICCIDs Encontrados")
            df_display = df_resultados[['iccid', 'codigo_bt', 'nombre_distribuidor', 'estatus']].copy()
            df_display.columns = ['ICCID', 'Código BT Actual', 'Distribuidor Actual', 'Estatus']
            
            def highlight_status(row):
                if row['Estatus'] == 'ACTIVO':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Estatus'] == 'NO ENCONTRADO':
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return ['background-color: #fff3cd'] * len(row)
            
            st.dataframe(
                df_display.style.apply(highlight_status, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            if activos > 0:
                st.markdown("---")
                
                # Paso 2: Seleccionar nuevo distribuidor
                st.markdown("### 🎯 Paso 2: Seleccionar Nuevo Distribuidor (Para Todos)")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    query_nuevo = st.text_input(
                        "Buscar nuevo distribuidor",
                        placeholder="Código, nombre o plaza",
                        key="query_nuevo_reasignacion"
                    )
                
                with col2:
                    filtro_nuevo = st.selectbox(
                        "Estatus",
                        ["ACTIVO", "TODOS", "SUSPENDIDO", "BAJA"],
                        key="filtro_nuevo_reasignacion"
                    )
                
                if query_nuevo:
                    estatus_filtro = None if filtro_nuevo == "TODOS" else filtro_nuevo
                    distribuidores = buscar_distribuidores(query=query_nuevo, estatus=estatus_filtro, limit=20)
                    
                    if distribuidores:
                        df_dist = pd.DataFrame(distribuidores)
                        
                        df_display = df_dist[['codigo_bt', 'nombre', 'plaza', 'estatus']].copy()
                        df_display.columns = ['Código BT', 'Nombre', 'Plaza', 'Estatus']
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                        
                        codigo_nuevo = st.selectbox(
                            "Seleccionar nuevo distribuidor",
                            df_dist['codigo_bt'].tolist(),
                            format_func=lambda x: f"{x} - {df_dist[df_dist['codigo_bt']==x]['nombre'].values[0]}",
                            key="codigo_nuevo_reasignacion"
                        )
                        
                        dist_nuevo = df_dist[df_dist['codigo_bt'] == codigo_nuevo].iloc[0].to_dict()
                        
                        motivo = st.text_input(
                            "Motivo de la reasignación",
                            placeholder="Ej: Devolución por mensajería, paquete recuperado",
                            key="motivo_reasignacion"
                        )
                        
                        st.markdown("---")
                        st.markdown("### ✅ Confirmar Reasignación Masiva")
                        
                        st.markdown(f"""
                        <div class="warning-box">
                            <strong>🔄 Nuevo Distribuidor:</strong><br>
                            {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}<br><br>
                            <strong>📊 Se reasignarán {activos} ICCIDs ACTIVOS</strong><br>
                            <strong>📝 Se mantendrá el historial completo</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("💾 Aplicar Reasignación Masiva", type="primary", use_container_width=True, key="aplicar_reasignacion"):
                            if not motivo:
                                st.error("❌ Por favor indica el motivo de la reasignación")
                            else:
                                try:
                                    exitosos = 0
                                    errores = 0
                                    
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    iccids_activos = [r for r in resultados if r['estatus'] == 'ACTIVO']
                                    
                                    for idx, resultado in enumerate(iccids_activos):
                                        try:
                                            status_text.text(f"Procesando {idx+1}/{len(iccids_activos)}: {resultado['iccid']}")
                                            
                                            reasignar_sim(
                                                iccid=resultado['iccid'],
                                                nuevo_distribuidor_id=dist_nuevo['id'],
                                                nuevo_codigo_bt=dist_nuevo['codigo_bt'],
                                                nuevo_nombre=dist_nuevo['nombre'],
                                                motivo=motivo,
                                                usuario="Almacén BAITEL"
                                            )
                                            exitosos += 1
                                        except Exception as e:
                                            errores += 1
                                            st.warning(f"⚠️ Error en {resultado['iccid']}: {str(e)}")
                                        
                                        progress_bar.progress((idx + 1) / len(iccids_activos))
                                    
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.success(f"✅ Reasignación masiva completada: {exitosos} exitosos, {errores} errores")
                                    st.balloons()
                                    
                                    st.markdown(f"""
                                    <div class="success-box">
                                        <h4>✅ Reasignación Masiva Completada</h4>
                                        <p><strong>ICCIDs Reasignados:</strong> {exitosos}<br>
                                        <strong>Errores:</strong> {errores}<br>
                                        <strong>Nuevo Distribuidor:</strong> {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}<br>
                                        <strong>Motivo:</strong> {motivo}<br>
                                        <strong>Historial:</strong> Mantenido ✅</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    del st.session_state['iccids_reasignacion']
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al aplicar reasignación masiva: {str(e)}")
                    else:
                        st.warning("⚠️ No se encontraron distribuidores")
            else:
                st.warning("⚠️ No hay ICCIDs ACTIVOS para reasignar")
