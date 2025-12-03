"""
Configuración de zona horaria para México
"""

import os
from datetime import datetime, date
from zoneinfo import ZoneInfo

# Zona horaria de México
MEXICO_TZ = ZoneInfo("America/Mexico_City")

def get_fecha_actual_mexico() -> date:
    """
    Obtener la fecha actual en zona horaria de México
    
    Returns:
        Fecha actual en México
    """
    return datetime.now(MEXICO_TZ).date()

def get_datetime_actual_mexico() -> datetime:
    """
    Obtener la fecha y hora actual en zona horaria de México
    
    Returns:
        Datetime actual en México
    """
    return datetime.now(MEXICO_TZ)
