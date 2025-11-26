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
    
    # Paso 1: Buscar ICCID
    st.markdown("### 🔍 Paso 1: Buscar ICCID a Corregir")
    
    iccid_corregir = st.text_input(
        "ICCID a corregir",
        placeholder="8952140063703946403",
        help="Ingresa el ICCID que fue asignado incorrectamente",
        key="iccid_corregir"
    )
    
    if iccid_corregir:
        with st.spinner("Buscando ICCID..."):
            envio_actual = get_envio_by_iccid(iccid_corregir)
        
        if envio_actual:
            if envio_actual['estatus'] != 'ACTIVO':
                st.warning(f"⚠️ Este ICCID tiene estatus: {envio_actual['estatus']}. Solo se pueden corregir SIMs ACTIVAS.")
            else:
                st.success("✅ ICCID encontrado")
                
                # Mostrar datos actuales
                st.markdown("### 📋 Datos Actuales")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("ICCID", envio_actual['iccid'])
                with col2:
                    st.metric("Código BT", envio_actual['codigo_bt'])
                with col3:
                    st.metric("Distribuidor", envio_actual['nombre_distribuidor'])
                
                st.markdown("---")
                
                # Paso 2: Seleccionar nuevo distribuidor
                st.markdown("### 🎯 Paso 2: Seleccionar Distribuidor Correcto")
                
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
                            placeholder="Ej: Error de captura, se confundió de distribuidor",
                            key="motivo_correccion"
                        )
                        
                        # Confirmar corrección
                        st.markdown("---")
                        st.markdown("### ✅ Confirmar Corrección")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="warning-box">
                                <strong>❌ Distribuidor Incorrecto:</strong><br>
                                {envio_actual['codigo_bt']} - {envio_actual['nombre_distribuidor']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>✅ Distribuidor Correcto:</strong><br>
                                {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if st.button("💾 Aplicar Corrección", type="primary", use_container_width=True):
                            if not motivo:
                                st.error("❌ Por favor indica el motivo de la corrección")
                            else:
                                try:
                                    with st.spinner("Aplicando corrección..."):
                                        resultado = corregir_distribuidor_envio(
                                            iccid=iccid_corregir,
                                            nuevo_distribuidor_id=dist_nuevo['id'],
                                            nuevo_codigo_bt=dist_nuevo['codigo_bt'],
                                            nuevo_nombre=dist_nuevo['nombre'],
                                            motivo=motivo,
                                            usuario="Almacén BAITEL"
                                        )
                                    
                                    st.success("✅ Corrección aplicada exitosamente")
                                    st.balloons()
                                    
                                    st.markdown(f"""
                                    <div class="success-box">
                                        <h4>✅ ICCID Corregido</h4>
                                        <p><strong>ICCID:</strong> {resultado['iccid']}<br>
                                        <strong>Nuevo Distribuidor:</strong> {resultado['codigo_bt']} - {resultado['nombre_distribuidor']}<br>
                                        <strong>Motivo:</strong> {motivo}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al aplicar corrección: {str(e)}")
                    else:
                        st.warning("⚠️ No se encontraron distribuidores")
        else:
            st.error("❌ ICCID no encontrado en la base de datos")

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
    
    # Paso 1: Buscar ICCID
    st.markdown("### 🔍 Paso 1: Buscar ICCID a Reasignar")
    
    iccid_reasignar = st.text_input(
        "ICCID a reasignar",
        placeholder="8952140063703946403",
        help="Ingresa el ICCID que será reasignado",
        key="iccid_reasignar"
    )
    
    if iccid_reasignar:
        with st.spinner("Buscando ICCID..."):
            envio_actual = get_envio_by_iccid(iccid_reasignar)
        
        if envio_actual:
            if envio_actual['estatus'] != 'ACTIVO':
                st.warning(f"⚠️ Este ICCID tiene estatus: {envio_actual['estatus']}. Solo se pueden reasignar SIMs ACTIVAS.")
            else:
                st.success("✅ ICCID encontrado")
                
                # Mostrar datos actuales
                st.markdown("### 📋 Distribuidor Original")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("ICCID", envio_actual['iccid'])
                with col2:
                    st.metric("Código BT", envio_actual['codigo_bt'])
                with col3:
                    st.metric("Distribuidor", envio_actual['nombre_distribuidor'])
                with col4:
                    st.metric("Fecha", envio_actual['fecha'])
                
                st.markdown("---")
                
                # Paso 2: Seleccionar nuevo distribuidor
                st.markdown("### 🎯 Paso 2: Seleccionar Nuevo Distribuidor")
                
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
                        
                        # Mostrar tabla
                        df_display = df_dist[['codigo_bt', 'nombre', 'plaza', 'estatus']].copy()
                        df_display.columns = ['Código BT', 'Nombre', 'Plaza', 'Estatus']
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                        
                        # Seleccionar
                        codigo_nuevo = st.selectbox(
                            "Seleccionar nuevo distribuidor",
                            df_dist['codigo_bt'].tolist(),
                            format_func=lambda x: f"{x} - {df_dist[df_dist['codigo_bt']==x]['nombre'].values[0]}",
                            key="codigo_nuevo_reasignacion"
                        )
                        
                        dist_nuevo = df_dist[df_dist['codigo_bt'] == codigo_nuevo].iloc[0].to_dict()
                        
                        motivo = st.text_area(
                            "Motivo de la reasignación *",
                            placeholder="Ej: Paquete devuelto por mensajería DHL, guía 123456. Se reasigna a nuevo distribuidor.",
                            help="Describe detalladamente el motivo de la reasignación",
                            key="motivo_reasignacion"
                        )
                        
                        # Confirmar reasignación
                        st.markdown("---")
                        st.markdown("### ✅ Confirmar Reasignación")
                        
                        st.warning("⚠️ **IMPORTANTE:** Esta operación creará un registro en el historial y marcará el envío original como REASIGNADO.")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="info-box">
                                <strong>📦 Distribuidor Original:</strong><br>
                                {envio_actual['codigo_bt']} - {envio_actual['nombre_distribuidor']}<br>
                                <small>Se marcará como REASIGNADO</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>🎯 Nuevo Distribuidor:</strong><br>
                                {dist_nuevo['codigo_bt']} - {dist_nuevo['nombre']}<br>
                                <small>Se creará nuevo envío ACTIVO</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if st.button("🔄 Aplicar Reasignación", type="primary", use_container_width=True):
                            if not motivo:
                                st.error("❌ Por favor indica el motivo de la reasignación")
                            else:
                                try:
                                    with st.spinner("Aplicando reasignación..."):
                                        resultado = reasignar_sim(
                                            iccid=iccid_reasignar,
                                            nuevo_distribuidor_id=dist_nuevo['id'],
                                            nuevo_codigo_bt=dist_nuevo['codigo_bt'],
                                            nuevo_nombre=dist_nuevo['nombre'],
                                            motivo=motivo,
                                            usuario="Almacén BAITEL"
                                        )
                                    
                                    st.success("✅ Reasignación completada exitosamente")
                                    st.balloons()
                                    
                                    st.markdown(f"""
                                    <div class="success-box">
                                        <h4>✅ SIM Reasignada</h4>
                                        <p><strong>ICCID:</strong> {resultado['envio_nuevo']['iccid']}<br>
                                        <strong>Distribuidor Original:</strong> {resultado['envio_anterior']['codigo_bt']} (REASIGNADO)<br>
                                        <strong>Nuevo Distribuidor:</strong> {resultado['envio_nuevo']['codigo_bt']} - {resultado['envio_nuevo']['nombre_distribuidor']}<br>
                                        <strong>Motivo:</strong> {motivo}<br>
                                        <strong>Historial:</strong> Registrado en tabla historial_cambios</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al aplicar reasignación: {str(e)}")
                    else:
                        st.warning("⚠️ No se encontraron distribuidores")
        else:
            st.error("❌ ICCID no encontrado en la base de datos")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>💡 <strong>Diferencia clave:</strong> Corrección = actualiza registro | Reasignación = crea historial + nuevo registro</small>
</div>
""", unsafe_allow_html=True)
