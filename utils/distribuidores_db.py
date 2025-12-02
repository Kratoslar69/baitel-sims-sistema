"""
Funciones CRUD para la tabla distribuidores
"""

from typing import List, Dict, Optional
from datetime import datetime
from .supabase_client import get_supabase_client


def buscar_distribuidores(query: str = "", estatus: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Buscar distribuidores por código, nombre o plaza
    
    Args:
        query: Texto a buscar (código, nombre o plaza)
        estatus: Filtrar por estatus (ACTIVO, BAJA, SUSPENDIDO)
        limit: Límite de resultados
    
    Returns:
        Lista de distribuidores encontrados
    """
    supabase = get_supabase_client()
    
    # Construir query base
    db_query = supabase.table('distribuidores').select('*')
    
    # Filtrar por estatus si se especifica
    if estatus:
        db_query = db_query.eq('estatus', estatus)
    
    # Buscar por texto si se especifica
    if query:
        query_upper = query.upper().strip()
        # Buscar en código_bt, nombre o plaza
        db_query = db_query.or_(
            f'codigo_bt.ilike.%{query_upper}%,'
            f'nombre.ilike.%{query_upper}%,'
            f'plaza.ilike.%{query_upper}%'
        )
    
    # Ordenar y limitar
    db_query = db_query.order('codigo_bt').limit(limit)
    
    result = db_query.execute()
    return result.data


def get_distribuidor_by_codigo(codigo_bt: str) -> Optional[Dict]:
    """
    Obtener distribuidor por código BT
    
    Args:
        codigo_bt: Código BT del distribuidor
    
    Returns:
        Distribuidor encontrado o None
    """
    supabase = get_supabase_client()
    
    result = supabase.table('distribuidores')\
        .select('*')\
        .eq('codigo_bt', codigo_bt.upper().strip())\
        .execute()
    
    return result.data[0] if result.data else None


def get_distribuidor_by_id(id: str) -> Optional[Dict]:
    """
    Obtener distribuidor por ID
    
    Args:
        id: UUID del distribuidor
    
    Returns:
        Distribuidor encontrado o None
    """
    supabase = get_supabase_client()
    
    result = supabase.table('distribuidores')\
        .select('*')\
        .eq('id', id)\
        .execute()
    
    return result.data[0] if result.data else None


def crear_distribuidor(
    codigo_bt: str,
    nombre: str,
    plaza: str,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    estatus: str = "ACTIVO"
) -> Dict:
    """
    Crear nuevo distribuidor
    
    Args:
        codigo_bt: Código BT único
        nombre: Nombre del distribuidor
        plaza: Plaza/ciudad
        telefono: Teléfono de contacto
        email: Email de contacto
        estatus: Estatus inicial (default: ACTIVO)
    
    Returns:
        Distribuidor creado
    """
    supabase = get_supabase_client()
    
    # Normalizar datos
    data = {
        'codigo_bt': codigo_bt.upper().strip(),
        'nombre': nombre.upper().strip(),
        'plaza': plaza.upper().strip(),
        'estatus': estatus.upper().strip(),
        'fecha_alta': datetime.now().isoformat()
    }
    
    # Agregar campos opcionales si existen
    if telefono:
        data['telefono'] = telefono.strip()
    if email:
        data['email'] = email.lower().strip()
    
    result = supabase.table('distribuidores').insert(data).execute()
    return result.data[0]


def actualizar_distribuidor(id: str, **campos) -> Dict:
    """
    Actualizar campos de un distribuidor
    
    Args:
        id: UUID del distribuidor
        **campos: Campos a actualizar (nombre, plaza, telefono, email, estatus)
    
    Returns:
        Distribuidor actualizado
    """
    supabase = get_supabase_client()
    
    # Normalizar datos
    data = {}
    if 'codigo_bt' in campos:
        data['codigo_bt'] = campos['codigo_bt'].upper().strip()
    if 'nombre' in campos:
        data['nombre'] = campos['nombre'].upper().strip()
    if 'plaza' in campos:
        data['plaza'] = campos['plaza'].upper().strip()
    if 'estatus' in campos:
        data['estatus'] = campos['estatus'].upper().strip()
    if 'telefono' in campos:
        data['telefono'] = campos['telefono'].strip() if campos['telefono'] else None
    if 'email' in campos:
        data['email'] = campos['email'].lower().strip() if campos['email'] else None
    
    data['fecha_modificacion'] = datetime.now().isoformat()
    
    result = supabase.table('distribuidores')\
        .update(data)\
        .eq('id', id)\
        .execute()
    
    return result.data[0]


def get_siguiente_codigo_bt() -> str:
    """
    Obtener sugerencia de siguiente código BT consecutivo
    
    Returns:
        Código BT sugerido (ej: BT650-)
    """
    supabase = get_supabase_client()
    
    # Obtener el último código BT
    result = supabase.table('distribuidores')\
        .select('codigo_bt')\
        .order('codigo_bt', desc=True)\
        .limit(1)\
        .execute()
    
    if not result.data:
        return "BT001-"
    
    ultimo_codigo = result.data[0]['codigo_bt']
    
    # Extraer número del código (ej: BT649-SAYULA -> 649)
    try:
        # Buscar patrón BT###
        import re
        match = re.search(r'BT(\d+)', ultimo_codigo)
        if match:
            numero = int(match.group(1))
            siguiente = numero + 1
            return f"BT{siguiente:03d}-"
    except:
        pass
    
    return "BT001-"


def get_estadisticas_distribuidores() -> Dict:
    """
    Obtener estadísticas de distribuidores
    
    Returns:
        Dict con estadísticas (total, activos, baja, suspendidos)
    """
    supabase = get_supabase_client()
    
    # Total
    total = supabase.table('distribuidores')\
        .select('*', count='exact')\
        .execute()
    
    # Por estatus
    activos = supabase.table('distribuidores')\
        .select('*', count='exact')\
        .eq('estatus', 'ACTIVO')\
        .execute()
    
    baja = supabase.table('distribuidores')\
        .select('*', count='exact')\
        .eq('estatus', 'BAJA')\
        .execute()
    
    suspendidos = supabase.table('distribuidores')\
        .select('*', count='exact')\
        .eq('estatus', 'SUSPENDIDO')\
        .execute()
    
    return {
        'total': total.count,
        'activos': activos.count,
        'baja': baja.count,
        'suspendidos': suspendidos.count
    }


def get_todos_distribuidores() -> List[Dict]:
    """
    Obtener todos los distribuidores (sin límite)
    
    Returns:
        Lista completa de distribuidores
    """
    supabase = get_supabase_client()
    
    result = supabase.table('distribuidores')\
        .select('*')\
        .order('codigo_bt')\
        .execute()
    
    return result.data


def eliminar_distribuidor(id: str) -> Dict:
    """
    Eliminar un distribuidor por su ID
    
    Args:
        id: UUID del distribuidor
    
    Returns:
        Distribuidor eliminado
    """
    supabase = get_supabase_client()
    
    result = supabase.table('distribuidores')\
        .delete()\
        .eq('id', id)\
        .execute()
    
    return result.data[0] if result.data else None
