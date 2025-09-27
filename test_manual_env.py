#!/usr/bin/env python3
"""
Prueba de la nueva implementacion manual de carga de .env
"""

import os
import sys

# Simular el ambiente exacto de Streamlit
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
os.chdir(app_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.dirname(app_dir))

print("=== PRUEBA DE CARGA MANUAL DE .ENV ===")
print(f"Directorio de trabajo: {os.getcwd()}")

# Implementar la misma funcion de carga manual que en la app
def load_env_file():
    """Cargar variables de entorno desde archivo .env manualmente"""
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        print(f"Buscando .env en: {env_path}")
        print(f"Archivo existe: {os.path.exists(env_path)}")
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines_processed = 0
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')

                        # Solo establecer variables ANCLORA
                        if key.startswith('ANCLORA'):
                            os.environ[key] = value
                            lines_processed += 1
                            print(f"  Cargada: {key}")

            print(f"Total de variables ANCLORA procesadas: {lines_processed}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error cargando .env manualmente: {e}")
        import traceback
        traceback.print_exc()
        return False

# Cargar .env manualmente
if load_env_file():
    print("[OK] Archivo .env cargado manualmente")
else:
    print("[ERROR] No se pudo cargar el archivo .env")
    sys.exit(1)

# Verificar que los tokens estén disponibles
print("\n=== VERIFICACION DE TOKENS ===")
api_token = os.getenv('ANCLORA_API_TOKEN')
default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')

print(f"ANCLORA_API_TOKEN: {'Configurado' if api_token else 'No encontrado'}")
print(f"ANCLORA_DEFAULT_API_TOKEN: {'Configurado' if default_token else 'No encontrado'}")

if api_token:
    print(f"Valor del token: {api_token[:20]}...")

if default_token:
    print(f"Valor del token por defecto: {default_token}")

# Simular la función _load_api_settings de la aplicación
def simulate_load_api_settings():
    """Simular exactamente la función _load_api_settings de la app"""
    def _get_env_or_secret(*keys):
        for key in keys:
            env_value = os.getenv(key)
            if env_value and env_value.strip():
                return env_value.strip()
        return None

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
settings = simulate_load_api_settings()
if settings['token']:
    print(f"[SUCCESS] Token de API encontrado: {settings['token'][:20]}...")
    print(f"[SUCCESS] Chat URL: {settings['chat_url']}")
    print("[SUCCESS] La aplicacion Streamlit deberia funcionar correctamente")
else:
    print("[ERROR] No se pudo encontrar un token de API valido")