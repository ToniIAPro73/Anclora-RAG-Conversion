import os

def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1","true","yes","on"}

# Flags (DEV por defecto apagado)
SECURITY_ENABLED = _bool_env("ANCLORA_SECURITY_ENABLED", False)
SILENCE_SECURITY_WARNING = _bool_env("ANCLORA_SILENCE_SECURITY_WARNING", True)
