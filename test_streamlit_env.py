#!/usr/bin/env python3
"""
Script para probar la carga de .env en contexto de Streamlit
"""

import os
import sys

# Simular el ambiente de Streamlit
print("=== PRUEBA DE CARGA DE .ENV PARA STREAMLIT ===")

# Agregar el directorio actual al path (igual que hace la app)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"Directorio de trabajo: {current_dir}")

# Cargar variables de entorno (igual que en la app)
try:
    from dotenv import load_dotenv
    # Buscar .env en el directorio raíz del proyecto (igual que en la app)
    env_path = os.path.join(os.path.dirname(current_dir), '.env')
    print(f"Buscando .env en: {env_path}")
    load_dotenv(env_path)
    print("[OK] Archivo .env cargado correctamente")
except ImportError:
    print("[ERROR] python-dotenv no esta instalado")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error cargando .env: {e}")
    sys.exit(1)

# Verificar que los tokens estén disponibles
print("\n=== VERIFICACION DE TOKENS ===")
api_token = os.getenv('ANCLORA_API_TOKEN')
default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

print(f"ANCLORA_API_TOKEN: {api_token[:20] + '...' if api_token else 'None'}")
print(f"ANCLORA_DEFAULT_API_TOKEN: {default_token or 'None'}")

# Simular la función _load_api_settings de la aplicación
def test_load_api_settings():
    """Simular exactamente la función _load_api_settings de la app"""
    from app.Inicio import _get_env_or_secret

    token = _get_env_or_secret('api_token', 'API_TOKEN', 'ANCLORA_API_TOKEN')
    if not token:
        tokens_value = _get_env_or_secret('api_tokens', 'ANCLORA_API_TOKENS')
        if tokens_value:
            token_candidates = [tok.strip() for tok in tokens_value.replace(';', ',').split(',') if tok.strip()]
            if token_candidates:
                token = token_candidates[0]
    if not token:
        token = _get_env_or_secret('ANCLORA_DEFAULT_API_TOKEN')

    return {
        'chat_url': 'http://localhost:8081/chat',
        'token': token or '',
        'timeout': '60',
    }

print("\n=== PRUEBA DE _load_api_settings ===")
settings = test_load_api_settings()
print(f"Token encontrado: {'Si' if settings['token'] else 'No'}")
print(f"Token valor: {settings['token'][:20] + '...' if settings['token'] else 'Ninguno'}")

if settings['token']:
    print("[SUCCESS] La aplicacion deberia funcionar correctamente")
else:
    print("[ERROR] La aplicacion seguira fallando")
    print("\n=== DEBUG: Todas las variables ANCLORA ===")
    for key, value in os.environ.items():
        if 'ANCLORA' in key:
            print(f"  {key}: {value}")