"""
Cliente Python para que agentes IA accedan al sistema Anclora RAG
"""

import requests
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

class AncloraRAGClient:
    """
    Cliente para interactuar con el sistema Anclora RAG desde agentes IA
    """
    
    def __init__(self, base_url: str = "http://localhost:8081", api_key: str = "your-api-key-here"):
        """
        Inicializar cliente RAG
        
        Args:
            base_url (str): URL base del sistema RAG
            api_key (str): Clave de API para autenticación
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del sistema RAG
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en health check: {e}")
            return {"status": "error", "message": str(e)}
    
    def query(self, message: str, max_length: int = 1000) -> Dict[str, Any]:
        """
        Realizar consulta al sistema RAG
        
        Args:
            message (str): Pregunta o consulta
            max_length (int): Longitud máxima del mensaje
            
        Returns:
            Dict con la respuesta del RAG
        """
        try:
            payload = {
                "message": message,
                "max_length": max_length
            }
            
            response = self.session.post(f"{self.base_url}/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Consulta exitosa: {message[:50]}...")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en consulta: {e}")
            return {"status": "error", "message": str(e)}
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """
        Subir documento al sistema RAG
        
        Args:
            file_path (str): Ruta al archivo a subir
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"status": "error", "message": "Archivo no encontrado"}
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                # Remover Content-Type header para multipart
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Documento subido: {file_path.name}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al subir documento: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_documents(self) -> Dict[str, Any]:
        """
        Listar documentos en la base de conocimiento
        
        Returns:
            Dict con lista de documentos
        """
        try:
            response = self.session.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al listar documentos: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Eliminar documento de la base de conocimiento
        
        Args:
            filename (str): Nombre del archivo a eliminar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            response = self.session.delete(f"{self.base_url}/documents/{filename}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Documento eliminado: {filename}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al eliminar documento: {e}")
            return {"status": "error", "message": str(e)}
    
    def batch_query(self, messages: List[str]) -> List[Dict[str, Any]]:
        """
        Realizar múltiples consultas en lote
        
        Args:
            messages (List[str]): Lista de mensajes/consultas
            
        Returns:
            Lista de respuestas
        """
        results = []
        for message in messages:
            result = self.query(message)
            results.append(result)
        return results


# Ejemplo de uso para agentes IA
class AIAgentRAGInterface:
    """
    Interfaz simplificada para agentes IA
    """
    
    def __init__(self, rag_url: str = "http://localhost:8081", api_key: str = "your-api-key-here"):
        self.client = AncloraRAGClient(rag_url, api_key)
        self.logger = logging.getLogger(__name__)
    
    def ask_question(self, question: str) -> str:
        """
        Hacer una pregunta simple al RAG
        
        Args:
            question (str): Pregunta
            
        Returns:
            str: Respuesta del RAG
        """
        result = self.client.query(question)
        if result.get("status") == "success":
            return result.get("response", "Sin respuesta")
        else:
            return f"Error: {result.get('message', 'Error desconocido')}"
    
    def add_knowledge(self, file_path: str) -> bool:
        """
        Agregar conocimiento al RAG
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            bool: True si fue exitoso
        """
        result = self.client.upload_document(file_path)
        return result.get("status") == "success"
    
    def get_available_documents(self) -> List[str]:
        """
        Obtener lista de documentos disponibles
        
        Returns:
            List[str]: Lista de nombres de documentos
        """
        result = self.client.list_documents()
        if result.get("status") == "success":
            return result.get("documents", [])
        return []
    
    def is_healthy(self) -> bool:
        """
        Verificar si el sistema está funcionando
        
        Returns:
            bool: True si está saludable
        """
        health = self.client.health_check()
        return health.get("status") == "healthy"


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear interfaz para agente IA
    ai_interface = AIAgentRAGInterface()
    
    # Verificar salud del sistema
    if ai_interface.is_healthy():
        print("✅ Sistema RAG disponible")
        
        # Hacer una consulta
        response = ai_interface.ask_question("¿Cuáles son los productos de PBC?")
        print(f"Respuesta: {response}")
        
        # Listar documentos
        docs = ai_interface.get_available_documents()
        print(f"Documentos disponibles: {docs}")
        
    else:
        print("❌ Sistema RAG no disponible")
