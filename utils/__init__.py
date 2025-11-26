"""
Módulo de utilidades para el sistema de inventario BAITEL
"""

from .supabase_client import get_supabase_client
from .distribuidores_db import (
    buscar_distribuidores,
    get_distribuidor_by_codigo,
    get_distribuidor_by_id,
    crear_distribuidor,
    actualizar_distribuidor,
    get_siguiente_codigo_bt,
    get_estadisticas_distribuidores,
    get_todos_distribuidores
)
from .envios_db import (
    capturar_envio_masivo,
    buscar_envios,
    get_envio_by_iccid,
    corregir_distribuidor_envio,
    reasignar_sim,
    get_estadisticas_envios,
    get_sims_por_distribuidor,
    cancelar_envio
)

__all__ = [
    'get_supabase_client',
    'buscar_distribuidores',
    'get_distribuidor_by_codigo',
    'get_distribuidor_by_id',
    'crear_distribuidor',
    'actualizar_distribuidor',
    'get_siguiente_codigo_bt',
    'get_estadisticas_distribuidores',
    'get_todos_distribuidores',
    'capturar_envio_masivo',
    'buscar_envios',
    'get_envio_by_iccid',
    'corregir_distribuidor_envio',
    'reasignar_sim',
    'get_estadisticas_envios',
    'get_sims_por_distribuidor',
    'cancelar_envio'
]
