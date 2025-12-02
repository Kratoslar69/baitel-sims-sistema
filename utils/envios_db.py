"""
Funciones CRUD para la tabla envios
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from .supabase_client import get_supabase_client


def capturar_envio_masivo(
    iccids: List[str],
    distribuidor_id: str,
    codigo_bt: str,
    nombre_distribuidor: str,
    fecha: Optional[date] = None,
    observaciones: Optional[str] = None,
    usuario_captura: str = "Sistema"
) -> Dict:
    """
    Capturar múltiples ICCIDs en un solo envío
    
    Args:
        iccids: Lista de ICCIDs a registrar
        distribuidor_id: UUID del distribuidor
        codigo_bt: Código BT del distribuidor
        nombre_distribuidor: Nombre del distribuidor
        fecha: Fecha del envío (default: hoy)
        observaciones: Observaciones opcionales
        usuario_captura: Usuario que captura (default: Sistema)
    
    Returns:
        Dict con resultado (exitosos, duplicados, errores)
    """
    supabase = get_supabase_client()
    
    if fecha is None:
        fecha = date.today()
    
    # Normalizar ICCIDs
    iccids_limpios = [iccid.strip().upper() for iccid in iccids if iccid.strip()]
    
    # Verificar duplicados en la base de datos
    iccids_existentes = []
    if iccids_limpios:
        # Buscar en lotes de 100 para evitar URLs muy largas
        for i in range(0, len(iccids_limpios), 100):
            lote = iccids_limpios[i:i+100]
            result = supabase.table('envios')\
                .select('iccid')\
                .in_('iccid', lote)\
                .execute()
            iccids_existentes.extend([r['iccid'] for r in result.data])
    
    # Filtrar ICCIDs nuevos
    iccids_nuevos = [iccid for iccid in iccids_limpios if iccid not in iccids_existentes]
    
    # Preparar datos para inserción
    registros = []
    for iccid in iccids_nuevos:
        registros.append({
            'fecha': fecha.isoformat(),
            'iccid': iccid,
            'distribuidor_id': distribuidor_id,
            'codigo_bt': codigo_bt.upper().strip(),
            'nombre_distribuidor': nombre_distribuidor.upper().strip(),
            'estatus': 'ACTIVO',
            'observaciones': observaciones,
            'usuario_captura': usuario_captura
        })
    
    # Insertar en lotes de 1000 (límite de Supabase)
    exitosos = 0
    errores = []
    
    for i in range(0, len(registros), 1000):
        lote = registros[i:i+1000]
        try:
            result = supabase.table('envios').insert(lote).execute()
            exitosos += len(result.data)
        except Exception as e:
            errores.append(str(e))
    
    return {
        'exitosos': exitosos,
        'duplicados': len(iccids_existentes),
        'errores': errores,
        'total_procesados': len(iccids_limpios)
    }


def buscar_envios(
    iccid: Optional[str] = None,
    codigo_bt: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estatus: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Buscar envíos con filtros
    
    Args:
        iccid: ICCID a buscar (búsqueda parcial)
        codigo_bt: Código BT del distribuidor
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final
        estatus: Filtrar por estatus
        limit: Límite de resultados
    
    Returns:
        Lista de envíos encontrados
    """
    supabase = get_supabase_client()
    
    query = supabase.table('envios').select('*')
    
    if iccid:
        query = query.ilike('iccid', f'%{iccid.strip()}%')
    
    if codigo_bt:
        query = query.eq('codigo_bt', codigo_bt.upper().strip())
    
    if fecha_desde:
        query = query.gte('fecha_envio', fecha_desde.isoformat())
    
    if fecha_hasta:
        query = query.lte('fecha_envio', fecha_hasta.isoformat())
    
    if estatus:
        query = query.eq('estatus', estatus.upper().strip())
    
    query = query.order('created_at', desc=True).limit(limit)
    
    result = query.execute()
    return result.data


def get_envio_by_iccid(iccid: str) -> Optional[Dict]:
    """
    Obtener envío por ICCID
    
    Args:
        iccid: ICCID a buscar
    
    Returns:
        Envío encontrado o None
    """
    supabase = get_supabase_client()
    
    result = supabase.table('envios')\
        .select('*')\
        .eq('iccid', iccid.strip().upper())\
        .order('created_at', desc=True)\
        .limit(1)\
        .execute()
    
    return result.data[0] if result.data else None


def corregir_distribuidor_envio(
    iccid: str,
    nuevo_distribuidor_id: str,
    nuevo_codigo_bt: str,
    nuevo_nombre: str,
    motivo: Optional[str] = None,
    usuario: str = "Sistema"
) -> Dict:
    """
    Corregir error de captura (cambiar distribuidor sin historial)
    
    Args:
        iccid: ICCID a corregir
        nuevo_distribuidor_id: UUID del distribuidor correcto
        nuevo_codigo_bt: Código BT correcto
        nuevo_nombre: Nombre correcto
        motivo: Motivo de la corrección
        usuario: Usuario que corrige
    
    Returns:
        Envío actualizado
    """
    supabase = get_supabase_client()
    
    # Actualizar envío
    data = {
        'distribuidor_id': nuevo_distribuidor_id,
        'codigo_bt': nuevo_codigo_bt.upper().strip(),
        'nombre_distribuidor': nuevo_nombre.upper().strip(),
        'observaciones': f"CORREGIDO: {motivo}" if motivo else "CORREGIDO",
        'updated_at': datetime.now().isoformat()
    }
    
    result = supabase.table('envios')\
        .update(data)\
        .eq('iccid', iccid.strip().upper())\
        .execute()
    
    return result.data[0] if result.data else None


def reasignar_sim(
    iccid: str,
    nuevo_distribuidor_id: str,
    nuevo_codigo_bt: str,
    nuevo_nombre: str,
    motivo: str,
    usuario: str = "Sistema"
) -> Dict:
    """
    Reasignar SIM a otro distribuidor (con historial completo)
    
    Args:
        iccid: ICCID a reasignar
        nuevo_distribuidor_id: UUID del nuevo distribuidor
        nuevo_codigo_bt: Código BT del nuevo distribuidor
        nuevo_nombre: Nombre del nuevo distribuidor
        motivo: Motivo de la reasignación
        usuario: Usuario que reasigna
    
    Returns:
        Dict con resultado de la operación
    """
    supabase = get_supabase_client()
    
    # Obtener envío actual
    envio_actual = get_envio_by_iccid(iccid)
    if not envio_actual:
        raise ValueError(f"ICCID {iccid} no encontrado")
    
    # Marcar envío actual como REASIGNADO
    supabase.table('envios')\
        .update({
            'estatus': 'REASIGNADO',
            'updated_at': datetime.now().isoformat()
        })\
        .eq('id', envio_actual['id'])\
        .execute()
    
    # Registrar en historial
    historial = {
        'envio_id': envio_actual['id'],
        'tipo_cambio': 'REASIGNACION',
        'distribuidor_anterior_id': envio_actual['distribuidor_id'],
        'distribuidor_nuevo_id': nuevo_distribuidor_id,
        'codigo_bt_anterior': envio_actual['codigo_bt'],
        'codigo_bt_nuevo': nuevo_codigo_bt.upper().strip(),
        'motivo': motivo,
        'usuario': usuario
    }
    
    supabase.table('historial_cambios').insert(historial).execute()
    
    # Crear nuevo envío ACTIVO
    nuevo_envio = {
        'fecha': date.today().isoformat(),
        'iccid': iccid.strip().upper(),
        'distribuidor_id': nuevo_distribuidor_id,
        'codigo_bt': nuevo_codigo_bt.upper().strip(),
        'nombre_distribuidor': nuevo_nombre.upper().strip(),
        'estatus': 'ACTIVO',
        'observaciones': f"REASIGNADO: {motivo}",
        'usuario_captura': usuario
    }
    
    result = supabase.table('envios').insert(nuevo_envio).execute()
    
    return {
        'envio_anterior': envio_actual,
        'envio_nuevo': result.data[0],
        'historial': historial
    }


def get_estadisticas_envios() -> Dict:
    """
    Obtener estadísticas de envíos
    
    Returns:
        Dict con estadísticas
    """
    supabase = get_supabase_client()
    
    # Total
    total = supabase.table('envios')\
        .select('*', count='exact')\
        .execute()
    
    # Activos
    activos = supabase.table('envios')\
        .select('*', count='exact')\
        .eq('estatus', 'ACTIVO')\
        .execute()
    
    # Reasignados
    reasignados = supabase.table('envios')\
        .select('*', count='exact')\
        .eq('estatus', 'REASIGNADO')\
        .execute()
    
    # Cancelados
    cancelados = supabase.table('envios')\
        .select('*', count='exact')\
        .eq('estatus', 'CANCELADO')\
        .execute()
    
    return {
        'total': total.count,
        'activos': activos.count,
        'reasignados': reasignados.count,
        'cancelados': cancelados.count
    }


def get_sims_por_distribuidor(codigo_bt: str, estatus: str = 'ACTIVO') -> List[Dict]:
    """
    Obtener SIMs de un distribuidor específico
    
    Args:
        codigo_bt: Código BT del distribuidor
        estatus: Filtrar por estatus (default: ACTIVO)
    
    Returns:
        Lista de SIMs del distribuidor
    """
    supabase = get_supabase_client()
    
    result = supabase.table('envios')\
        .select('*')\
        .eq('codigo_bt', codigo_bt.upper().strip())\
        .eq('estatus', estatus.upper().strip())\
        .order('fecha_envio', desc=True)\
        .execute()
    
    return result.data


def cancelar_envio(iccid: str, motivo: str, usuario: str = "Sistema") -> Dict:
    """
    Cancelar un envío
    
    Args:
        iccid: ICCID a cancelar
        motivo: Motivo de la cancelación
        usuario: Usuario que cancela
    
    Returns:
        Envío cancelado
    """
    supabase = get_supabase_client()
    
    data = {
        'estatus': 'CANCELADO',
        'observaciones': f"CANCELADO: {motivo}",
        'updated_at': datetime.now().isoformat()
    }
    
    result = supabase.table('envios')\
        .update(data)\
        .eq('iccid', iccid.strip().upper())\
        .execute()
    
    return result.data[0] if result.data else None
