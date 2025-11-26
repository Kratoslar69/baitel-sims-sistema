# Sistema de Inventario de SIMs - BAITEL

Sistema web desarrollado con Streamlit y Supabase para gestionar el inventario y distribución de tarjetas SIM a distribuidores de BAITEL.

## 📋 Características Principales

### ✅ Funcionalidades Implementadas

1. **Dashboard Principal**
   - Métricas en tiempo real (distribuidores activos, SIMs asignadas)
   - Gráficas de distribución y actividad
   - Top 10 distribuidores
   - Accesos rápidos a funciones principales

2. **Captura Masiva de SIMs**
   - Búsqueda rápida de distribuidores
   - Captura masiva por copiar/pegar desde Excel
   - Detección automática de duplicados
   - Procesamiento de hasta 10,000 ICCIDs por lote
   - Validación y normalización automática

3. **Administración de Distribuidores**
   - Alta de nuevos distribuidores
   - Sugerencia automática de código BT consecutivo
   - Edición de datos existentes
   - Búsqueda y consulta avanzada
   - Exportación a CSV

4. **Correcciones y Reasignaciones**
   - **Corrección Simple**: Para errores de captura recientes (sin historial)
   - **Reasignación con Historial**: Para devoluciones o recuperaciones (con auditoría completa)
   - Búsqueda de ICCIDs
   - Trazabilidad completa

5. **Reportes y Análisis**
   - Dashboard general de operaciones
   - Consultas personalizadas con múltiples filtros
   - Reportes por distribuidor
   - Análisis temporal (7, 30, 90 días, personalizado)
   - Exportación a CSV de todos los reportes
   - Gráficas interactivas

## 🗄️ Estructura de la Base de Datos

### Tablas Principales

#### `distribuidores`
- Catálogo maestro de distribuidores (636 registros)
- Campos: código_bt, nombre, plaza, teléfono, email, estatus
- Estatus: ACTIVO, SUSPENDIDO, BAJA

#### `envios`
- Registro de asignaciones de SIMs
- Campos: fecha, iccid, distribuidor_id, codigo_bt, nombre_distribuidor, estatus
- Estatus: ACTIVO, REASIGNADO, CANCELADO

#### `historial_cambios`
- Auditoría de reasignaciones
- Campos: tipo_cambio, distribuidor_anterior, distribuidor_nuevo, motivo

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.11+
- Cuenta de Supabase configurada
- Entorno virtual de Python

### Pasos de Instalación

1. **Crear entorno virtual**
```bash
python3 -m venv baitel_env
source baitel_env/bin/activate  # En Windows: baitel_env\Scripts\activate
```

2. **Instalar dependencias**
```bash
cd baitel_sims_sistema
pip install -r requirements.txt
```

3. **Configurar variables de entorno**

El archivo `.env` ya está incluido con las credenciales de Supabase:
```
SUPABASE_URL=https://ouqrskhtqqexuxpjoddx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

4. **Ejecutar la aplicación**
```bash
streamlit run Home.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📁 Estructura del Proyecto

```
baitel_sims_sistema/
├── .env                          # Variables de entorno (credenciales)
├── requirements.txt              # Dependencias Python
├── README.md                     # Este archivo
├── Home.py                       # Página principal / Dashboard
├── pages/                        # Páginas de la aplicación
│   ├── 1_📥_Captura_SIMs.py     # Captura masiva de ICCIDs
│   ├── 2_👥_Administrar_Distribuidores.py  # CRUD distribuidores
│   ├── 3_🔄_Correcciones.py     # Correcciones y reasignaciones
│   └── 4_📊_Reportes.py         # Reportes y análisis
├── utils/                        # Módulos de utilidades
│   ├── __init__.py              # Inicializador del paquete
│   ├── supabase_client.py       # Cliente de Supabase con cache
│   ├── distribuidores_db.py     # CRUD de distribuidores
│   └── envios_db.py             # CRUD de envíos
└── assets/                       # Recursos (imágenes, logos)
```

## 🔧 Uso del Sistema

### 1. Captura de SIMs (Flujo Principal)

**Escenario**: El almacén recibe un paquete de SIMs para un distribuidor

1. Ir a **📥 Captura de SIMs**
2. Buscar el distribuidor por código, nombre o plaza
3. Seleccionar el distribuidor correcto
4. Copiar los ICCIDs desde Excel (una columna completa)
5. Pegar en el campo de texto
6. Verificar el preview (cantidad detectada)
7. Hacer clic en **"Procesar y Guardar"**
8. El sistema muestra: exitosos, duplicados omitidos, errores

**Tiempo estimado**: 3-5 segundos para 100 ICCIDs

### 2. Alta de Nuevo Distribuidor

**Escenario**: Se incorpora un nuevo distribuidor a la red

1. Ir a **👥 Administrar Distribuidores** → Tab "Nuevo Distribuidor"
2. El sistema sugiere el siguiente código BT (ej: BT650-)
3. Completar: código, nombre, plaza, teléfono, email
4. Seleccionar estatus (normalmente ACTIVO)
5. Hacer clic en **"Guardar Distribuidor"**

### 3. Corrección de Error de Captura

**Escenario**: El almacenista se equivocó de distribuidor hace minutos

1. Ir a **🔄 Correcciones** → Tab "Corrección Simple"
2. Ingresar el ICCID a corregir
3. Buscar el distribuidor correcto
4. Indicar motivo de la corrección
5. Hacer clic en **"Aplicar Corrección"**

**Nota**: No mantiene historial, solo actualiza el registro

### 4. Reasignación con Historial

**Escenario**: Paquete devuelto por mensajería, se reasigna a otro distribuidor

1. Ir a **🔄 Correcciones** → Tab "Reasignación con Historial"
2. Ingresar el ICCID a reasignar
3. Buscar el nuevo distribuidor
4. Describir detalladamente el motivo
5. Hacer clic en **"Aplicar Reasignación"**

**Resultado**: 
- Envío original → REASIGNADO
- Nuevo envío → ACTIVO
- Registro en historial_cambios

### 5. Generar Reportes

**Escenario**: Necesitas analizar la actividad de los últimos 30 días

1. Ir a **📊 Reportes** → Tab "Análisis Temporal"
2. Seleccionar período (ej: "Últimos 30 días")
3. Hacer clic en **"Generar Análisis"**
4. Ver gráficas y métricas
5. Descargar CSV si es necesario

## 📊 Estado Actual del Proyecto

### Base de Datos
- ✅ 636 distribuidores registrados (368 ACTIVOS, 268 BAJA)
- ✅ 0 envíos (sistema listo para usar)
- ✅ Estructura completa implementada

### Aplicación
- ✅ Dashboard funcional
- ✅ Captura masiva operativa
- ✅ Administración de distribuidores completa
- ✅ Correcciones y reasignaciones implementadas
- ✅ Reportes y análisis funcionales

## 🔐 Seguridad

- Las credenciales están en el archivo `.env` (no compartir públicamente)
- La clave ANON de Supabase tiene permisos limitados
- Para producción, considera implementar autenticación de usuarios

## 🚀 Próximos Pasos (Opcional)

### Deploy a Producción

**Opción 1: Streamlit Cloud (Gratis)**
1. Subir el proyecto a GitHub
2. Conectar con Streamlit Cloud
3. Configurar secrets (variables de entorno)
4. Deploy automático

**Opción 2: Servidor Propio**
1. Configurar servidor Linux
2. Instalar dependencias
3. Configurar Nginx como proxy
4. Usar systemd para mantener el servicio activo

### Mejoras Futuras

1. **Autenticación de Usuarios**
   - Implementar Supabase Auth
   - Roles: Almacén, Admin, Consulta

2. **Notificaciones**
   - Email a distribuidor cuando recibe SIMs
   - Alertas de distribuidores sin actividad

3. **Integración WhatsApp**
   - Notificar envíos por WhatsApp
   - Usar Google Apps Script o Twilio

4. **Dashboard Ejecutivo**
   - KPIs avanzados
   - Proyecciones de crecimiento
   - Comparativas mes a mes

## 📞 Soporte

Para dudas o problemas:
- Revisar este README
- Verificar logs de Streamlit
- Consultar documentación de Supabase: https://supabase.com/docs

## 📝 Notas Técnicas

### Límites y Consideraciones

- **Límite de Supabase**: 1000 registros por inserción (el código ya maneja esto en lotes)
- **Cache de Streamlit**: Los datos se cachean por 60 segundos para mejor rendimiento
- **Normalización**: Todos los textos se normalizan a MAYÚSCULAS automáticamente
- **Duplicados**: El sistema detecta y omite ICCIDs duplicados automáticamente

### Desnormalización Intencional

Los campos `codigo_bt` y `nombre_distribuidor` están desnormalizados en la tabla `envios` para:
- Reportes más rápidos (sin JOINs costosos)
- Mantener datos históricos aunque el distribuidor cambie
- Trade-off aceptado: redundancia controlada vs performance

## 📄 Licencia

Sistema desarrollado para uso interno de BAITEL.

---

**Última actualización**: 25 de noviembre de 2025  
**Versión**: 1.0.0  
**Desarrollado por**: Jose (Gerente de Red de Distribuidores)
