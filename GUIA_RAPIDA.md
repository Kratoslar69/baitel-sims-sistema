# 🚀 Guía Rápida de Inicio

## Ejecutar la Aplicación

### 1. Activar el entorno virtual

**En Linux/Mac:**
```bash
cd /home/ubuntu/baitel_sims_sistema
source ../baitel_env/bin/activate
```

**En Windows:**
```bash
cd C:\ruta\a\baitel_sims_sistema
..\baitel_env\Scripts\activate
```

### 2. Ejecutar Streamlit

```bash
streamlit run Home.py
```

La aplicación se abrirá automáticamente en: `http://localhost:8501`

### 3. Ejecutar en puerto específico (opcional)

```bash
streamlit run Home.py --server.port 8502
```

## 📋 Casos de Uso Frecuentes

### ✅ Capturar SIMs (Diario)

1. **📥 Captura de SIMs** → Buscar distribuidor → Pegar ICCIDs → Guardar
2. **Tiempo**: ~5 segundos para 100 ICCIDs

### ✅ Nuevo Distribuidor (Semanal)

1. **👥 Administrar Distribuidores** → Tab "Nuevo Distribuidor"
2. Usar código sugerido → Completar datos → Guardar

### ✅ Corregir Error (Ocasional)

1. **🔄 Correcciones** → Tab "Corrección Simple"
2. Ingresar ICCID → Buscar distribuidor correcto → Aplicar

### ✅ Generar Reporte (Mensual)

1. **📊 Reportes** → Tab "Análisis Temporal"
2. Seleccionar período → Generar → Descargar CSV

## 🔧 Comandos Útiles

### Ver logs en modo debug
```bash
streamlit run Home.py --logger.level=debug
```

### Limpiar cache de Streamlit
```bash
streamlit cache clear
```

### Verificar conexión a Supabase
```bash
python3 -c "from utils.supabase_client import get_supabase_client; print('✅ Conexión OK')"
```

## ⚠️ Solución de Problemas

### Error: "ModuleNotFoundError"
**Solución**: Asegúrate de tener el entorno virtual activado
```bash
source ../baitel_env/bin/activate
pip install -r requirements.txt
```

### Error: "SUPABASE_URL not found"
**Solución**: Verifica que el archivo `.env` esté en la carpeta raíz
```bash
ls -la .env
cat .env
```

### La aplicación no carga datos
**Solución**: Verifica la conexión a internet y las credenciales de Supabase

### Conflictos de dependencias
**Solución**: Reinstalar dependencias
```bash
pip install --force-reinstall -r requirements.txt
```

## 📞 Contacto

Para soporte técnico, contactar a Jose (Gerente de Red).

---

**💡 Tip**: Mantén esta guía a mano para consultas rápidas.
