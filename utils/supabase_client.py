"""
Cliente de Supabase con cache
"""

import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Cargar variables de entorno (solo para desarrollo local)
load_dotenv()

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Obtener cliente de Supabase con cache
    Prioriza secrets de Streamlit Cloud, luego variables de entorno
    
    Returns:
        Client: Cliente de Supabase
    """
    # Intentar obtener de Streamlit secrets primero (producción)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except (KeyError, FileNotFoundError):
        # Fallback a variables de entorno (desarrollo local)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en secrets o .env")
    
    return create_client(url, key)
