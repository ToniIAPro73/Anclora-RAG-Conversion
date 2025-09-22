"""Sistema de seguridad avanzado para el RAG con detección de amenazas."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import ipaddress
from collections import defaultdict, deque


class ThreatLevel(Enum):
    """Niveles de amenaza."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Tipos de eventos de seguridad."""
    SUSPICIOUS_QUERY = "suspicious_query"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INJECTION_ATTEMPT = "injection_attempt"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


@dataclass
class SecurityEvent:
    """Evento de seguridad detectado."""
    
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    source_ip: str
    user_agent: Optional[str]
    query: Optional[str]
    description: str
    indicators: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class SecurityPolicy:
    """Política de seguridad configurable."""
    
    max_queries_per_minute: int = 60
    max_queries_per_hour: int = 1000
    max_query_length: int = 2000
    blocked_patterns: List[str] = None
    suspicious_keywords: List[str] = None
    rate_limit_whitelist: Set[str] = None
    enable_content_filtering: bool = True
    enable_anomaly_detection: bool = True
    quarantine_threshold: int = 5


class AdvancedSecurityManager:
    """Gestor de seguridad avanzado con detección de amenazas en tiempo real."""

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self.security_events: deque = deque(maxlen=10000)
        self.rate_limit_tracker: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.user_behavior_profiles: Dict[str, Dict[str, Any]] = {}
        self.quarantined_ips: Dict[str, datetime] = {}
        self.threat_intelligence: Dict[str, Any] = self._load_threat_intelligence()
        
        # Patrones de seguridad por defecto
        if not self.policy.blocked_patterns:
            self.policy.blocked_patterns = [
                r"(?i)(union\s+select|drop\s+table|delete\s+from)",  # SQL injection
                r"(?i)(<script|javascript:|vbscript:)",  # XSS
                r"(?i)(\.\.\/|\.\.\\)",  # Path traversal
                r"(?i)(exec\s*\(|eval\s*\(|system\s*\()",  # Code injection
            ]
        
        if not self.policy.suspicious_keywords:
            self.policy.suspicious_keywords = [
                "password", "token", "secret", "key", "admin", "root",
                "database", "config", "backup", "dump", "export"
            ]

    def validate_request(self, source_ip: str, query: str, user_agent: Optional[str] = None,
                        user_id: Optional[str] = None) -> Tuple[bool, Optional[SecurityEvent]]:
        """Valida una solicitud y detecta amenazas."""
        
        # Verificar IP en cuarentena
        if self._is_ip_quarantined(source_ip):
            event = self._create_security_event(
                SecurityEventType.UNAUTHORIZED_ACCESS,
                ThreatLevel.HIGH,
                source_ip,
                user_agent,
                query,
                "IP en cuarentena intentando acceso",
                ["quarantined_ip"]
            )
            return False, event
        
        # Verificar rate limiting
        if not self._check_rate_limits(source_ip):
            event = self._create_security_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                ThreatLevel.MEDIUM,
                source_ip,
                user_agent,
                query,
                "Límite de velocidad excedido",
                ["rate_limit"]
            )
            self._handle_rate_limit_violation(source_ip)
            return False, event
        
        # Detectar patrones maliciosos
        threat_indicators = self._detect_malicious_patterns(query)
        if threat_indicators:
            event = self._create_security_event(
                SecurityEventType.INJECTION_ATTEMPT,
                ThreatLevel.HIGH,
                source_ip,
                user_agent,
                query,
                "Patrones maliciosos detectados en la consulta",
                threat_indicators
            )
            self._handle_security_violation(source_ip, event)
            return False, event
        
        # Detectar consultas sospechosas
        suspicious_indicators = self._detect_suspicious_content(query)
        if suspicious_indicators:
            event = self._create_security_event(
                SecurityEventType.SUSPICIOUS_QUERY,
                ThreatLevel.MEDIUM,
                source_ip,
                user_agent,
                query,
                "Contenido sospechoso en la consulta",
                suspicious_indicators
            )
            self._log_security_event(event)
            # No bloquear, solo registrar
        
        # Detectar comportamiento anómalo
        if user_id and self.policy.enable_anomaly_detection:
            anomaly_score = self._detect_anomalous_behavior(user_id, query, source_ip)
            if anomaly_score > 0.8:
                event = self._create_security_event(
                    SecurityEventType.ANOMALOUS_BEHAVIOR,
                    ThreatLevel.MEDIUM,
                    source_ip,
                    user_agent,
                    query,
                    f"Comportamiento anómalo detectado (score: {anomaly_score:.2f})",
                    ["behavioral_anomaly"]
                )
                self._log_security_event(event)
        
        # Actualizar perfil de comportamiento
        if user_id:
            self._update_user_behavior_profile(user_id, query, source_ip)
        
        # Registrar acceso exitoso
        self._record_successful_access(source_ip)
        
        return True, None

    def _is_ip_quarantined(self, ip: str) -> bool:
        """Verifica si una IP está en cuarentena."""
        
        if ip in self.quarantined_ips:
            quarantine_time = self.quarantined_ips[ip]
            if datetime.now() - quarantine_time < timedelta(hours=24):
                return True
            else:
                # Remover de cuarentena si ha pasado el tiempo
                del self.quarantined_ips[ip]
        
        return False

    def _check_rate_limits(self, ip: str) -> bool:
        """Verifica límites de velocidad."""
        
        if self.policy.rate_limit_whitelist and ip in self.policy.rate_limit_whitelist:
            return True
        
        now = datetime.now()
        ip_requests = self.rate_limit_tracker[ip]
        
        # Limpiar requests antiguos
        while ip_requests and now - ip_requests[0] > timedelta(hours=1):
            ip_requests.popleft()
        
        # Verificar límite por minuto
        recent_requests = [req for req in ip_requests if now - req < timedelta(minutes=1)]
        if len(recent_requests) >= self.policy.max_queries_per_minute:
            return False
        
        # Verificar límite por hora
        if len(ip_requests) >= self.policy.max_queries_per_hour:
            return False
        
        return True

    def _detect_malicious_patterns(self, query: str) -> List[str]:
        """Detecta patrones maliciosos en la consulta."""
        
        indicators = []
        
        for pattern in self.policy.blocked_patterns:
            if re.search(pattern, query):
                indicators.append(f"malicious_pattern: {pattern}")
        
        # Verificar longitud excesiva
        if len(query) > self.policy.max_query_length:
            indicators.append("excessive_length")
        
        # Detectar caracteres sospechosos
        suspicious_chars = ['<', '>', '"', "'", ';', '|', '&', '$']
        char_count = sum(query.count(char) for char in suspicious_chars)
        if char_count > 10:
            indicators.append("suspicious_characters")
        
        return indicators

    def _detect_suspicious_content(self, query: str) -> List[str]:
        """Detecta contenido sospechoso en la consulta."""
        
        indicators = []
        query_lower = query.lower()
        
        # Verificar palabras clave sospechosas
        for keyword in self.policy.suspicious_keywords:
            if keyword in query_lower:
                indicators.append(f"suspicious_keyword: {keyword}")
        
        # Detectar intentos de exfiltración de datos
        data_exfil_patterns = [
            r"(?i)(show\s+tables|describe\s+|information_schema)",
            r"(?i)(list\s+files|directory\s+listing|ls\s+)",
            r"(?i)(dump\s+|export\s+|backup\s+)"
        ]
        
        for pattern in data_exfil_patterns:
            if re.search(pattern, query):
                indicators.append("data_exfiltration_attempt")
        
        return indicators

    def _detect_anomalous_behavior(self, user_id: str, query: str, ip: str) -> float:
        """Detecta comportamiento anómalo del usuario."""
        
        if user_id not in self.user_behavior_profiles:
            return 0.0  # Usuario nuevo, no hay baseline
        
        profile = self.user_behavior_profiles[user_id]
        anomaly_score = 0.0
        
        # Verificar cambio de IP
        if "typical_ips" in profile:
            if ip not in profile["typical_ips"]:
                anomaly_score += 0.3
        
        # Verificar longitud de consulta atípica
        if "avg_query_length" in profile:
            length_diff = abs(len(query) - profile["avg_query_length"])
            if length_diff > profile["avg_query_length"] * 2:
                anomaly_score += 0.2
        
        # Verificar frecuencia de consultas
        if "typical_frequency" in profile:
            current_time = datetime.now()
            recent_queries = [
                event for event in self.security_events
                if event.metadata.get("user_id") == user_id and
                current_time - event.timestamp < timedelta(minutes=10)
            ]
            
            if len(recent_queries) > profile["typical_frequency"] * 3:
                anomaly_score += 0.4
        
        # Verificar patrones de consulta
        if "typical_topics" in profile:
            query_words = set(query.lower().split())
            topic_overlap = len(query_words.intersection(profile["typical_topics"]))
            if topic_overlap == 0 and len(profile["typical_topics"]) > 5:
                anomaly_score += 0.2
        
        return min(1.0, anomaly_score)

    def _update_user_behavior_profile(self, user_id: str, query: str, ip: str) -> None:
        """Actualiza el perfil de comportamiento del usuario."""
        
        if user_id not in self.user_behavior_profiles:
            self.user_behavior_profiles[user_id] = {
                "typical_ips": set(),
                "query_lengths": [],
                "typical_topics": set(),
                "access_times": [],
                "total_queries": 0
            }
        
        profile = self.user_behavior_profiles[user_id]
        
        # Actualizar IPs típicas
        profile["typical_ips"].add(ip)
        if len(profile["typical_ips"]) > 10:  # Mantener solo las 10 más recientes
            profile["typical_ips"] = set(list(profile["typical_ips"])[-10:])
        
        # Actualizar longitudes de consulta
        profile["query_lengths"].append(len(query))
        if len(profile["query_lengths"]) > 100:
            profile["query_lengths"] = profile["query_lengths"][-100:]
        profile["avg_query_length"] = sum(profile["query_lengths"]) / len(profile["query_lengths"])
        
        # Actualizar temas típicos
        query_words = set(word.lower() for word in query.split() if len(word) > 3)
        profile["typical_topics"].update(query_words)
        if len(profile["typical_topics"]) > 50:
            # Mantener solo las palabras más frecuentes
            word_freq = defaultdict(int)
            for event in self.security_events:
                if event.metadata.get("user_id") == user_id and event.query:
                    for word in event.query.split():
                        if len(word) > 3:
                            word_freq[word.lower()] += 1
            
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
            profile["typical_topics"] = set(word for word, freq in top_words)
        
        # Actualizar tiempos de acceso
        profile["access_times"].append(datetime.now())
        if len(profile["access_times"]) > 100:
            profile["access_times"] = profile["access_times"][-100:]
        
        profile["total_queries"] += 1

    def _record_successful_access(self, ip: str) -> None:
        """Registra un acceso exitoso."""
        
        self.rate_limit_tracker[ip].append(datetime.now())

    def _handle_rate_limit_violation(self, ip: str) -> None:
        """Maneja violaciones de límite de velocidad."""
        
        # Contar violaciones recientes
        recent_violations = [
            event for event in self.security_events
            if event.source_ip == ip and
            event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED and
            datetime.now() - event.timestamp < timedelta(hours=1)
        ]
        
        if len(recent_violations) >= 3:
            self._quarantine_ip(ip, "Múltiples violaciones de rate limit")

    def _handle_security_violation(self, ip: str, event: SecurityEvent) -> None:
        """Maneja violaciones de seguridad."""
        
        self._log_security_event(event)
        
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self._quarantine_ip(ip, f"Amenaza {event.threat_level.value}: {event.description}")

    def _quarantine_ip(self, ip: str, reason: str) -> None:
        """Pone una IP en cuarentena."""
        
        self.quarantined_ips[ip] = datetime.now()
        
        quarantine_event = self._create_security_event(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            ThreatLevel.HIGH,
            ip,
            None,
            None,
            f"IP puesta en cuarentena: {reason}",
            ["ip_quarantined"]
        )
        self._log_security_event(quarantine_event)

    def _create_security_event(self, event_type: SecurityEventType, threat_level: ThreatLevel,
                             source_ip: str, user_agent: Optional[str], query: Optional[str],
                             description: str, indicators: List[str]) -> SecurityEvent:
        """Crea un evento de seguridad."""
        
        event_id = hashlib.md5(
            f"{source_ip}{datetime.now().isoformat()}{description}".encode()
        ).hexdigest()[:16]
        
        return SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            threat_level=threat_level,
            source_ip=source_ip,
            user_agent=user_agent,
            query=query,
            description=description,
            indicators=indicators,
            timestamp=datetime.now(),
            metadata={
                "query_length": len(query) if query else 0,
                "ip_reputation": self._get_ip_reputation(source_ip)
            }
        )

    def _log_security_event(self, event: SecurityEvent) -> None:
        """Registra un evento de seguridad."""
        
        self.security_events.append(event)
        
        # Log crítico para eventos de alta amenaza
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            print(f"SECURITY ALERT: {event.description} from {event.source_ip}")

    def _get_ip_reputation(self, ip: str) -> str:
        """Obtiene la reputación de una IP."""
        
        # En implementación real, esto consultaría servicios de threat intelligence
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return "private"
            elif ip_obj.is_loopback:
                return "loopback"
            else:
                return "public"
        except ValueError:
            return "unknown"

    def _load_threat_intelligence(self) -> Dict[str, Any]:
        """Carga inteligencia de amenazas."""
        
        # En implementación real, esto cargaría feeds de threat intelligence
        return {
            "malicious_ips": set(),
            "suspicious_domains": set(),
            "known_attack_patterns": []
        }

    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene un resumen de seguridad."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event for event in self.security_events
            if event.timestamp > cutoff_time
        ]
        
        event_counts = defaultdict(int)
        threat_counts = defaultdict(int)
        
        for event in recent_events:
            event_counts[event.event_type.value] += 1
            threat_counts[event.threat_level.value] += 1
        
        return {
            "total_events": len(recent_events),
            "events_by_type": dict(event_counts),
            "events_by_threat_level": dict(threat_counts),
            "quarantined_ips": len(self.quarantined_ips),
            "active_user_profiles": len(self.user_behavior_profiles),
            "top_threat_sources": self._get_top_threat_sources(recent_events)
        }

    def _get_top_threat_sources(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Obtiene las principales fuentes de amenazas."""
        
        ip_counts = defaultdict(int)
        for event in events:
            if event.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                ip_counts[event.source_ip] += 1
        
        top_sources = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {"ip": ip, "threat_count": count, "reputation": self._get_ip_reputation(ip)}
            for ip, count in top_sources
        ]
