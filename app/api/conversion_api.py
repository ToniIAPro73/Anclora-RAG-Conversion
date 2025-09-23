"""
API de Conversión para MVP - Anclora RAG
Endpoint principal para iniciar conversiones desde el frontend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncio
import os
import tempfile
from datetime import datetime
import logging

# Importar el orquestador híbrido
from orchestration.hybrid_orchestrator import (
    HybridOrchestrator, 
    ConversionRequest, 
    ProcessingPriority
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Anclora RAG Conversion API",
    description="API para conversión inteligente de documentos",
    version="1.0.0"
)

# Inicializar orquestador
orchestrator = HybridOrchestrator()

# Modelos de datos
class ConversionRequestModel(BaseModel):
    user_id: str
    priority: str = "standard"  # realtime, standard, batch
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversionStatusResponse(BaseModel):
    request_id: str
    status: str
    processing_mode: Optional[str] = None
    progress: Optional[float] = None
    estimated_completion: Optional[str] = None
    result_url: Optional[str] = None

# Storage temporal para resultados
conversion_results = {}
conversion_status = {}

@app.post("/api/v1/conversions/start")
async def start_conversion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    priority: str = Form("standard"),
    callback_url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Inicia una nueva conversión de documento
    
    - **file**: Archivo a convertir
    - **user_id**: ID del usuario
    - **priority**: Prioridad (realtime, standard, batch)
    - **callback_url**: URL para callback cuando termine (opcional)
    - **metadata**: Metadatos adicionales en JSON (opcional)
    """
    
    try:
        # Generar ID único para la conversión
        request_id = str(uuid.uuid4())
        
        # Validar prioridad
        try:
            priority_enum = ProcessingPriority(priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Prioridad inválida: {priority}")
        
        # Procesar metadata si se proporciona
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Metadata debe ser JSON válido")
        
        # Guardar archivo temporalmente
        temp_file_path = await save_uploaded_file(file)
        
        # Analizar características del archivo
        document_data = await analyze_document(file, temp_file_path)
        
        # Crear request de conversión
        conversion_request = ConversionRequest(
            request_id=request_id,
            user_id=user_id,
            document_data=document_data,
            priority=priority_enum,
            callback_url=callback_url,
            metadata=metadata_dict
        )
        
        # Inicializar status
        conversion_status[request_id] = {
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "processing_mode": None,
            "progress": 0.0
        }
        
        # Procesar en background
        if priority == "realtime":
            # Para realtime, procesamos inmediatamente
            result = await orchestrator.process_conversion(conversion_request)
            
            # Guardar resultado
            conversion_results[request_id] = result
            conversion_status[request_id].update({
                "status": "completed" if result.success else "failed",
                "processing_mode": result.processing_mode.value,
                "progress": 100.0,
                "completed_at": datetime.now().isoformat()
            })
            
            return JSONResponse({
                "request_id": request_id,
                "status": "completed" if result.success else "failed",
                "processing_mode": result.processing_mode.value,
                "processing_time": result.processing_time,
                "result_url": f"/api/v1/conversions/{request_id}/result" if result.success else None,
                "download_url": f"/api/v1/conversions/{request_id}/download" if result.success else None,
                "learning_applied": result.learning_applied,
                "optimizations_used": result.optimizations_used,
                "errors": result.errors if not result.success else None
            })
        
        else:
            # Para standard y batch, procesamos en background
            background_tasks.add_task(process_conversion_background, conversion_request)
            
            return JSONResponse({
                "request_id": request_id,
                "status": "queued",
                "message": "Conversión iniciada, use /status para monitorear progreso",
                "status_url": f"/api/v1/conversions/{request_id}/status",
                "estimated_time": "30-60 segundos" if priority == "standard" else "2-5 minutos"
            })
    
    except Exception as e:
        logger.error(f"Error iniciando conversión: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/api/v1/conversions/{request_id}/status")
async def get_conversion_status(request_id: str):
    """
    Obtiene el estado actual de una conversión
    """
    
    if request_id not in conversion_status:
        raise HTTPException(status_code=404, detail="Conversión no encontrada")
    
    status_data = conversion_status[request_id].copy()
    
    # Agregar URLs si está completada
    if status_data["status"] == "completed":
        status_data["result_url"] = f"/api/v1/conversions/{request_id}/result"
        status_data["download_url"] = f"/api/v1/conversions/{request_id}/download"
    
    return JSONResponse(status_data)

@app.get("/api/v1/conversions/{request_id}/result")
async def get_conversion_result(request_id: str):
    """
    Obtiene el resultado detallado de una conversión
    """
    
    if request_id not in conversion_results:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    
    result = conversion_results[request_id]
    
    return JSONResponse({
        "request_id": result.request_id,
        "success": result.success,
        "processing_mode": result.processing_mode.value,
        "processing_time": result.processing_time,
        "learning_applied": result.learning_applied,
        "optimizations_used": result.optimizations_used,
        "result_data": result.result_data,
        "errors": result.errors,
        "download_url": f"/api/v1/conversions/{request_id}/download" if result.success else None
    })

@app.get("/api/v1/conversions/{request_id}/download")
async def download_conversion_result(request_id: str):
    """
    Descarga el archivo convertido
    """
    
    if request_id not in conversion_results:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    
    result = conversion_results[request_id]
    
    if not result.success:
        raise HTTPException(status_code=400, detail="Conversión falló, no hay archivo para descargar")
    
    # En producción, esto devolvería el archivo real
    # Por ahora simulamos con un archivo de ejemplo
    file_path = result.result_data.get('output_file_path')
    
    if not file_path or not os.path.exists(file_path):
        # Crear archivo de ejemplo
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_file.write(b"Archivo convertido exitosamente por Anclora RAG")
        temp_file.close()
        file_path = temp_file.name
    
    return FileResponse(
        file_path,
        filename=f"converted_{request_id}.txt",
        media_type='application/octet-stream'
    )

@app.get("/api/v1/conversions/stats")
async def get_conversion_stats():
    """
    Obtiene estadísticas del sistema de conversión
    """
    
    stats = orchestrator.get_processing_stats()
    
    return JSONResponse({
        "processing_stats": stats,
        "active_conversions": len([s for s in conversion_status.values() if s["status"] == "processing"]),
        "completed_conversions": len([s for s in conversion_status.values() if s["status"] == "completed"]),
        "failed_conversions": len([s for s in conversion_status.values() if s["status"] == "failed"]),
        "total_conversions": len(conversion_status)
    })

@app.delete("/api/v1/conversions/{request_id}")
async def cancel_conversion(request_id: str):
    """
    Cancela una conversión en progreso
    """
    
    if request_id not in conversion_status:
        raise HTTPException(status_code=404, detail="Conversión no encontrada")
    
    status = conversion_status[request_id]
    
    if status["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"No se puede cancelar conversión en estado: {status['status']}")
    
    # Marcar como cancelada
    conversion_status[request_id].update({
        "status": "cancelled",
        "cancelled_at": datetime.now().isoformat()
    })
    
    return JSONResponse({
        "message": "Conversión cancelada exitosamente",
        "request_id": request_id
    })

# Funciones auxiliares
async def save_uploaded_file(file: UploadFile) -> str:
    """Guarda archivo subido temporalmente"""
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
    content = await file.read()
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name

async def analyze_document(file: UploadFile, file_path: str) -> Dict:
    """Analiza características del documento"""
    
    file_size = os.path.getsize(file_path)
    file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
    
    # Análisis básico (en producción sería más sofisticado)
    document_data = {
        'file_name': file.filename,
        'file_type': file_type,
        'file_size': file_size,
        'mime_type': file.content_type,
        'has_images': file_type in ['pdf', 'docx', 'pptx'],  # Estimación
        'has_tables': file_type in ['pdf', 'docx', 'xlsx'],  # Estimación
        'page_count': 1 if file_type == 'txt' else max(1, file_size // (1024 * 50)),  # Estimación
        'language': 'es',  # Default
        'structural_complexity': min(1.0, file_size / (1024 * 1024 * 10)),  # Basado en tamaño
        'content_preview': '',  # Se llenaría con contenido real
        'temp_file_path': file_path
    }
    
    return document_data

async def process_conversion_background(request: ConversionRequest):
    """Procesa conversión en background"""
    
    try:
        # Actualizar status a processing
        conversion_status[request.request_id].update({
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "progress": 10.0
        })
        
        # Procesar con orquestador
        result = await orchestrator.process_conversion(request)
        
        # Guardar resultado
        conversion_results[request.request_id] = result
        
        # Actualizar status final
        conversion_status[request.request_id].update({
            "status": "completed" if result.success else "failed",
            "processing_mode": result.processing_mode.value,
            "progress": 100.0,
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"✅ Conversión background completada: {request.request_id}")
        
    except Exception as e:
        logger.error(f"❌ Error en conversión background: {str(e)}")
        
        conversion_status[request.request_id].update({
            "status": "failed",
            "progress": 100.0,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "anclora-conversion-api", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
