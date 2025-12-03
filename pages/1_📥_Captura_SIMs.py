"""
Página de Captura Masiva de SIMs
"""

import streamlit as st
import pandas as pd
from datetime import date
from utils.distribuidores_db import buscar_distribuidores, get_distribuidor_by_id
from utils.envios_db import capturar_envio_masivo
from utils.timezone_config import get_fecha_actual_mexico

# Configuración de la página
st.set_page_config(
    page_title="Captura de SIMs - BAITEL",
    page_icon="📥",
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
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📥 Captura Masiva de SIMs")
st.markdown("---")

# Inicializar estado de sesión
if 'distribuidor_seleccionado' not in st.session_state:
    st.session_state.distribuidor_seleccionado = None
if 'resultado_captura' not in st.session_state:
    st.session_state.resultado_captura = None

# Paso 1: Buscar y seleccionar distribuidor
st.subheader("🔍 Paso 1: Seleccionar Distribuidor")

col1, col2 = st.columns([3, 1])

with col1:
    query_busqueda = st.text_input(
        "Buscar distribuidor por código, nombre o plaza",
        placeholder="Ej: BT032, OCTAVIANO, SAYULA",
        help="Escribe cualquier parte del código, nombre o plaza del distribuidor"
    )

with col2:
    filtro_estatus = st.selectbox(
        "Filtrar por estatus",
        ["TODOS", "ACTIVO", "BAJA", "SUSPENDIDO"]
    )

# Buscar distribuidores
if query_busqueda:
    with st.spinner("Buscando distribuidores..."):
        estatus_filtro = None if filtro_estatus == "TODOS" else filtro_estatus
        distribuidores = buscar_distribuidores(
            query=query_busqueda,
            estatus=estatus_filtro,
            limit=50
        )
    
    if distribuidores:
        st.success(f"✅ Se encontraron {len(distribuidores)} distribuidor(es)")
        
        # Mostrar resultados en tabla
        df_distribuidores = pd.DataFrame(distribuidores)
        df_display = df_distribuidores[['codigo_bt', 'nombre', 'plaza', 'estatus']].copy()
        df_display.columns = ['Código BT', 'Nombre', 'Plaza', 'Estatus']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Seleccionar distribuidor
        codigos = df_distribuidores['codigo_bt'].tolist()
        codigo_seleccionado = st.selectbox(
            "Seleccionar distribuidor para captura",
            codigos,
            format_func=lambda x: f"{x} - {df_distribuidores[df_distribuidores['codigo_bt']==x]['nombre'].values[0]}"
        )
        
        if st.button("✅ Confirmar Distribuidor", type="primary"):
            distribuidor = df_distribuidores[df_distribuidores['codigo_bt'] == codigo_seleccionado].iloc[0]
            st.session_state.distribuidor_seleccionado = distribuidor.to_dict()
            st.rerun()
    else:
        st.warning("⚠️ No se encontraron distribuidores con ese criterio")
else:
    st.info("💡 Escribe en el campo de búsqueda para encontrar un distribuidor")

# Mostrar distribuidor seleccionado
if st.session_state.distribuidor_seleccionado:
    st.markdown("---")
    dist = st.session_state.distribuidor_seleccionado
    
    st.markdown(f"""
    <div class="success-box">
        <h4>✅ Distribuidor Seleccionado</h4>
        <p><strong>Código:</strong> {dist['codigo_bt']}<br>
        <strong>Nombre:</strong> {dist['nombre']}<br>
        <strong>Plaza:</strong> {dist['plaza']}<br>
        <strong>Estatus:</strong> {dist['estatus']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Cambiar Distribuidor"):
        st.session_state.distribuidor_seleccionado = None
        st.session_state.resultado_captura = None
        st.rerun()
    
    # Paso 2: Capturar ICCIDs
    st.markdown("---")
    st.subheader("📝 Paso 2: Capturar ICCIDs")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **💡 Instrucciones:**
        1. Copia los ICCIDs desde tu Excel (una columna completa)
        2. Pégalos en el campo de texto de abajo
        3. El sistema detectará automáticamente cada ICCID (por línea o coma)
        4. Haz clic en "Procesar y Guardar"
        """)
    
    with col2:
        fecha_envio = st.date_input(
            "Fecha del envío",
            value=get_fecha_actual_mexico(),
            help="Fecha en que se realizó el envío (Zona horaria: México)"
        )
    
    # Campo de texto para ICCIDs
    iccids_texto = st.text_area(
        "Pegar ICCIDs aquí (uno por línea o separados por comas)",
        height=200,
        placeholder="8952140063703946403\n8952140063703946404\n8952140063703946405\n...",
        help="Puedes pegar directamente desde Excel. El sistema limpiará automáticamente los datos."
    )
    
    observaciones = st.text_input(
        "Observaciones (opcional)",
        placeholder="Ej: Envío mensajería DHL, guía 123456"
    )
    
    # Procesar ICCIDs
    if iccids_texto:
        # Separar por líneas y comas
        iccids_raw = iccids_texto.replace(',', '\n').split('\n')
        iccids_limpios = [iccid.strip() for iccid in iccids_raw if iccid.strip()]
        
        # Mostrar preview
        st.markdown(f"**📊 Preview:** {len(iccids_limpios)} ICCIDs detectados")
        
        if len(iccids_limpios) > 0:
            with st.expander("Ver primeros 10 ICCIDs"):
                for i, iccid in enumerate(iccids_limpios[:10], 1):
                    st.text(f"{i}. {iccid}")
                if len(iccids_limpios) > 10:
                    st.text(f"... y {len(iccids_limpios) - 10} más")
            
            # Botón de captura
            if st.button("💾 Procesar y Guardar", type="primary", use_container_width=True):
                with st.spinner(f"Procesando {len(iccids_limpios)} ICCIDs..."):
                    try:
                        resultado = capturar_envio_masivo(
                            iccids=iccids_limpios,
                            distribuidor_id=dist['id'],
                            codigo_bt=dist['codigo_bt'],
                            nombre_distribuidor=dist['nombre'],
                            fecha=fecha_envio,
                            observaciones=observaciones,
                            usuario_captura="Almacén BAITEL"
                        )
                        
                        st.session_state.resultado_captura = resultado
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al procesar: {str(e)}")

# Mostrar resultado de captura
if st.session_state.resultado_captura:
    st.markdown("---")
    resultado = st.session_state.resultado_captura
    
    if resultado['exitosos'] > 0:
        st.markdown(f"""
        <div class="success-box">
            <h3>✅ Captura Exitosa</h3>
            <p><strong>ICCIDs guardados:</strong> {resultado['exitosos']}<br>
            <strong>Duplicados omitidos:</strong> {resultado['duplicados']}<br>
            <strong>Total procesados:</strong> {resultado['total_procesados']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if resultado['duplicados'] > 0:
        st.warning(f"⚠️ Se omitieron {resultado['duplicados']} ICCIDs duplicados (ya existían en la base de datos)")
    
    if resultado['errores']:
        st.error(f"❌ Errores encontrados: {', '.join(resultado['errores'])}")
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Nueva Captura (Mismo Distribuidor)", use_container_width=True):
            st.session_state.resultado_captura = None
            st.rerun()
    
    with col2:
        if st.button("🔄 Cambiar Distribuidor", use_container_width=True):
            st.session_state.distribuidor_seleccionado = None
            st.session_state.resultado_captura = None
            st.rerun()
    
    with col3:
        if st.button("🏠 Volver al Dashboard", use_container_width=True):
            st.switch_page("Home.py")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>💡 Tip: Puedes capturar hasta 10,000 ICCIDs en una sola operación</small>
</div>
""", unsafe_allow_html=True)
