"""
Página de Administración de Distribuidores
"""

import streamlit as st
import pandas as pd
import time
from utils.distribuidores_db import (
    buscar_distribuidores,
    crear_distribuidor,
    actualizar_distribuidor,
    get_siguiente_codigo_bt,
    get_distribuidor_by_codigo
)

# Configuración de la página
st.set_page_config(
    page_title="Administrar Distribuidores - BAITEL",
    page_icon="👥",
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
st.title("👥 Administrar Distribuidores")
st.markdown("---")

# Tabs para diferentes funciones
tab1, tab2, tab3 = st.tabs(["➕ Nuevo Distribuidor", "✏️ Editar Distribuidor", "🔍 Buscar y Consultar"])

# TAB 1: NUEVO DISTRIBUIDOR
with tab1:
    st.subheader("Registrar Nuevo Distribuidor")
    
    # Inicializar contador de formularios para forzar limpieza
    if 'form_counter' not in st.session_state:
        st.session_state.form_counter = 0
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **💡 Instrucciones:**
        1. El sistema sugiere automáticamente el siguiente código BT consecutivo
        2. Puedes modificarlo si es necesario (ej: BT650-GUADALAJARA)
        3. Todos los campos son obligatorios excepto teléfono y email
        4. Los datos se normalizan automáticamente (MAYÚSCULAS, sin espacios extra)
        """)
    
    with col2:
        # Obtener sugerencia de código
        codigo_sugerido = get_siguiente_codigo_bt()
        st.markdown(f"""
        <div class="info-box">
            <strong>📋 Código Sugerido:</strong><br>
            <span style="font-size: 1.5rem; color: #17a2b8;">{codigo_sugerido}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Formulario de nuevo distribuidor (con key dinámica para forzar limpieza)
    with st.form(f"form_nuevo_distribuidor_{st.session_state.form_counter}"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo_bt = st.text_input(
                "Código BT *",
                value=codigo_sugerido,
                placeholder="BT650-GUADALAJARA",
                help="Formato: BT###-NOMBRE"
            )
            
            nombre = st.text_input(
                "Nombre del Distribuidor *",
                placeholder="JUAN PEREZ GARCIA",
                help="Nombre completo del distribuidor"
            )
            
            plaza = st.text_input(
                "Plaza/Ciudad *",
                placeholder="GUADALAJARA",
                help="Ciudad o plaza donde opera"
            )
        
        with col2:
            telefono = st.text_input(
                "Teléfono",
                placeholder="3312345678",
                help="Teléfono de contacto (opcional)"
            )
            
            email = st.text_input(
                "Email",
                placeholder="distribuidor@ejemplo.com",
                help="Email de contacto (opcional)"
            )
            
            estatus = st.selectbox(
                "Estatus Inicial *",
                ["ACTIVO", "SUSPENDIDO", "BAJA"],
                index=0,
                help="Estado inicial del distribuidor"
            )
        
        submitted = st.form_submit_button("💾 Guardar Distribuidor", type="primary", use_container_width=True)
        
        if submitted:
            # Validaciones
            if not codigo_bt or not nombre or not plaza:
                st.error("❌ Los campos marcados con * son obligatorios")
            else:
                # Verificar si el código ya existe
                existente = get_distribuidor_by_codigo(codigo_bt)
                if existente:
                    st.error(f"❌ El código {codigo_bt} ya existe. Por favor usa otro código.")
                else:
                    try:
                        with st.spinner("Guardando distribuidor..."):
                            nuevo_dist = crear_distribuidor(
                                codigo_bt=codigo_bt,
                                nombre=nombre,
                                plaza=plaza,
                                telefono=telefono if telefono else None,
                                email=email if email else None,
                                estatus=estatus
                            )
                        
                        st.success(f"✅ Distribuidor {codigo_bt} creado exitosamente")
                        st.balloons()
                        
                        # Mostrar resumen
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>✅ Distribuidor Registrado</h4>
                            <p><strong>Código:</strong> {nuevo_dist['codigo_bt']}<br>
                            <strong>Nombre:</strong> {nuevo_dist['nombre']}<br>
                            <strong>Plaza:</strong> {nuevo_dist['plaza']}<br>
                            <strong>Estatus:</strong> {nuevo_dist['estatus']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {str(e)}")
    
    # Botón para registrar otro distribuidor (fuera del formulario)
    if st.button("➕ Registrar Otro Distribuidor", type="primary", use_container_width=True, key="btn_registrar_otro"):
        # Incrementar contador para crear nuevo formulario limpio
        st.session_state.form_counter += 1
        st.rerun()

# TAB 2: EDITAR DISTRIBUIDOR
with tab2:
    st.subheader("Editar Distribuidor Existente")
    
    # Buscar distribuidor a editar
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_editar = st.text_input(
            "Buscar distribuidor a editar",
            placeholder="Código, nombre o plaza",
            key="query_editar"
        )
    
    with col2:
        filtro_editar = st.selectbox(
            "Filtrar",
            ["TODOS", "ACTIVO", "BAJA", "SUSPENDIDO"],
            key="filtro_editar"
        )
    
    if query_editar:
        estatus_filtro = None if filtro_editar == "TODOS" else filtro_editar
        distribuidores = buscar_distribuidores(query=query_editar, estatus=estatus_filtro, limit=50)
        
        if distribuidores:
            st.success(f"✅ {len(distribuidores)} distribuidor(es) encontrado(s)")
            
            # Seleccionar distribuidor
            df_dist = pd.DataFrame(distribuidores)
            codigos = df_dist['codigo_bt'].tolist()
            
            codigo_editar = st.selectbox(
                "Seleccionar distribuidor",
                codigos,
                format_func=lambda x: f"{x} - {df_dist[df_dist['codigo_bt']==x]['nombre'].values[0]}",
                key="codigo_editar"
            )
            
            dist_actual = df_dist[df_dist['codigo_bt'] == codigo_editar].iloc[0].to_dict()
            
            st.markdown("---")
            st.markdown("### Datos Actuales")
            
            # Formulario de edición
            with st.form("form_editar_distribuidor"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_codigo_bt = st.text_input(
                        "Código BT",
                        value=dist_actual['codigo_bt'],
                        help="Código BT del distribuidor (editable)"
                    )
                    
                    nuevo_nombre = st.text_input(
                        "Nombre",
                        value=dist_actual['nombre'],
                        help="Nombre del distribuidor"
                    )
                    
                    nueva_plaza = st.text_input(
                        "Plaza",
                        value=dist_actual['plaza'],
                        help="Plaza/ciudad"
                    )
                
                with col2:
                    nuevo_telefono = st.text_input(
                        "Teléfono",
                        value=dist_actual.get('telefono', '') or '',
                        help="Teléfono de contacto"
                    )
                    
                    nuevo_email = st.text_input(
                        "Email",
                        value=dist_actual.get('email', '') or '',
                        help="Email de contacto"
                    )
                    
                    nuevo_estatus = st.selectbox(
                        "Estatus",
                        ["ACTIVO", "SUSPENDIDO", "BAJA"],
                        index=["ACTIVO", "SUSPENDIDO", "BAJA"].index(dist_actual['estatus']),
                        help="Estado del distribuidor"
                    )
                
                submitted_edit = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
                
                if submitted_edit:
                    try:
                        with st.spinner("Actualizando distribuidor..."):
                            actualizado = actualizar_distribuidor(
                                id=dist_actual['id'],
                                codigo_bt=nuevo_codigo_bt,
                                nombre=nuevo_nombre,
                                plaza=nueva_plaza,
                                telefono=nuevo_telefono if nuevo_telefono else None,
                                email=nuevo_email if nuevo_email else None,
                                estatus=nuevo_estatus
                            )
                        
                        st.toast(f"✅ Distribuidor {nuevo_codigo_bt} actualizado exitosamente", icon="✅")
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al actualizar: {str(e)}")
            
            # Botón eliminar FUERA del formulario
            st.markdown("---")
            
            # Inicializar estado de confirmación
            if 'confirmar_eliminar' not in st.session_state:
                st.session_state.confirmar_eliminar = False
            
            if not st.session_state.confirmar_eliminar:
                if st.button("🗑️ Eliminar Distribuidor", type="secondary", use_container_width=True):
                    st.session_state.confirmar_eliminar = True
                    st.rerun()
            else:
                st.warning("⚠️ ¿Estás seguro de eliminar este distribuidor?")
                st.info(f"📋 {dist_actual['codigo_bt']} - {dist_actual['nombre']}")
                
                col_confirm1, col_confirm2 = st.columns(2)
                
                if col_confirm1.button("✅ Sí, eliminar", type="primary", use_container_width=True):
                    try:
                        from utils.distribuidores_db import eliminar_distribuidor
                        with st.spinner("Eliminando distribuidor..."):
                            eliminar_distribuidor(dist_actual['id'])
                        
                        st.session_state.confirmar_eliminar = False
                        st.toast(f"🗑️ Distribuidor {dist_actual['codigo_bt']} eliminado exitosamente", icon="🗑️")
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al eliminar: {str(e)}")
                        st.session_state.confirmar_eliminar = False
                
                if col_confirm2.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_eliminar = False
                    st.rerun()
        else:
            st.warning("⚠️ No se encontraron distribuidores")
    else:
        st.info("💡 Busca un distribuidor para editar sus datos")

# TAB 3: BUSCAR Y CONSULTAR
with tab3:
    st.subheader("Buscar y Consultar Distribuidores")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        query_buscar = st.text_input(
            "Buscar",
            placeholder="Código, nombre o plaza",
            key="query_buscar"
        )
    
    with col2:
        filtro_buscar = st.selectbox(
            "Estatus",
            ["TODOS", "ACTIVO", "BAJA", "SUSPENDIDO"],
            key="filtro_buscar"
        )
    
    with col3:
        limite = st.number_input(
            "Límite",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="limite_buscar"
        )
    
    if st.button("🔍 Buscar", type="primary"):
        with st.spinner("Buscando..."):
            estatus_filtro = None if filtro_buscar == "TODOS" else filtro_buscar
            distribuidores = buscar_distribuidores(
                query=query_buscar,
                estatus=estatus_filtro,
                limit=limite
            )
        
        if distribuidores:
            st.success(f"✅ {len(distribuidores)} distribuidor(es) encontrado(s)")
            
            # Mostrar tabla
            df = pd.DataFrame(distribuidores)
            df_display = df[['codigo_bt', 'nombre', 'plaza', 'telefono', 'email', 'estatus', 'fecha_alta']].copy()
            df_display.columns = ['Código BT', 'Nombre', 'Plaza', 'Teléfono', 'Email', 'Estatus', 'Fecha Alta']
            
            # Formatear fecha
            df_display['Fecha Alta'] = pd.to_datetime(df_display['Fecha Alta']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Opción de exportar
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"distribuidores_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No se encontraron distribuidores")
    else:
        st.info("💡 Haz clic en 'Buscar' para ver resultados (deja el campo vacío para ver todos)")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>💡 Tip: Los códigos BT son únicos y no se pueden modificar una vez creados</small>
</div>
""", unsafe_allow_html=True)
