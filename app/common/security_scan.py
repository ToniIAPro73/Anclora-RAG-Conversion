from dataclasses import dataclass
from typing import List, Optional
import os, os.path

@dataclass
class ScanResult:
    is_safe: bool
    threat_level: str = "none"   # none|low|medium|high
    threats_detected: List[str] = []
    quarantine_path: Optional[str] = None

def scan_file_for_conversion(path: str) -> ScanResult:
    threats = []

    # Regla 1: tamaño
    max_mb = float(os.getenv("ANCLORA_SECURITY_MAX_MB", "50"))
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > max_mb:
        return ScanResult(False, "medium", [f"file_too_large:{size_mb:.1f}MB>{max_mb}MB"])

    # Regla 2: MIME con python-magic-bin si está
    try:
        import magic  # python-magic-bin recomendado en Windows
        mime = magic.from_file(path, mime=True)
        allowed_prefixes = {"application", "text", "image", "audio", "video"}
        if not any(mime.startswith(p + "/") for p in allowed_prefixes):
            threats.append(f"suspicious_mime:{mime}")
    except Exception:
        # si no está magic, seguimos sin bloquear
        pass

    # Regla 3: extensión permitida
    _, ext = os.path.splitext(path.lower())
    allowed_exts = {
        ".pdf",".docx",".doc",".txt",".md",".html",
        ".xlsx",".xls",".csv",
        ".pptx",".ppt",
        ".json",".xml",".yaml",".yml",
        ".zip",".rar",
        ".png",".jpg",".jpeg",".gif",".svg",
    }
    if ext and ext not in allowed_exts:
        threats.append(f"disallowed_ext:{ext}")

    if threats:
        return ScanResult(False, "low", threats)

    return ScanResult(True, "none", [])
