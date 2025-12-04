#!/usr/bin/env python3
# ================================================================================================
# 🧪 MOCK N8N SERVER - Servidor simulado de n8n para testing local
# ================================================================================================
# Simula el comportamiento de n8n recibiendo webhooks y enviando callbacks

import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import logging
from datetime import datetime
import time
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MockN8N")

# ================================================================================================
# 📦 MODELOS DE DATOS
# ================================================================================================

class WebhookPayload(BaseModel):
    """Payload que el Gatekeeper envía a n8n."""
    user_id: str
    meeting_id: str
    meeting_url: str
    transcription_text: str
    language: str = "auto"
    estimated_duration_minutes: int
    remaining_hours: float
    plan_name: str
    consumption_percentage: float
    workflow_trigger_id: str
    triggered_at: str
    callbacks: Dict[str, str]
    services: Dict[str, str]


# ================================================================================================
# 🏗️ FASTAPI APPLICATION
# ================================================================================================

app = FastAPI(
    title="🧪 Mock n8n Server",
    description="Servidor simulado de n8n para testing local sin configurar n8n real",
    version="1.0.0"
)


# ================================================================================================
# 🎯 WEBHOOK ENDPOINT (recibe triggers del Gatekeeper)
# ================================================================================================

@app.post("/webhook/process-meeting")
async def mock_n8n_webhook(request: Request, payload: WebhookPayload):
    """
    🎯 Simula el webhook de n8n que recibe los triggers del Gatekeeper.
    
    Este endpoint:
    1. Recibe el webhook del Gatekeeper
    2. Simula procesamiento (transcripción → IA/NLP → PRD → Tareas)
    3. Envía callback al Gatekeeper con los resultados
    """
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("📥 MOCK N8N - Webhook recibido del Gatekeeper")
    logger.info("=" * 80)
    logger.info(f"   Meeting ID: {payload.meeting_id}")
    logger.info(f"   User ID: {payload.user_id}")
    logger.info(f"   Processing ID: {payload.workflow_trigger_id}")
    logger.info(f"   Transcription length: {len(payload.transcription_text)} chars")
    logger.info(f"   Language: {payload.language}")
    logger.info(f"   Callback URL: {payload.callbacks.get('consumption_update')}")
    
    # Simular procesamiento asíncrono (como haría n8n real)
    asyncio.create_task(
        simulate_processing(payload)
    )
    
    processing_time = (time.time() - start_time) * 1000
    
    logger.info(f"✅ Webhook accepted in {processing_time:.2f}ms")
    logger.info(f"🔄 Processing iniciado en background...")
    logger.info("=" * 80 + "\n")
    
    # Responder inmediatamente (como n8n real)
    return {
        "status": "processing",
        "workflow_id": f"mock-{payload.workflow_trigger_id}",
        "workflow_execution_id": f"mock-exec-{int(time.time())}",
        "message": "Webhook received, processing started"
    }


# ================================================================================================
# 🤖 SIMULACIÓN DE PROCESAMIENTO
# ================================================================================================

async def simulate_processing(payload: WebhookPayload):
    """
    🤖 Simula el procesamiento completo que n8n haría:
    1. Llamar al servicio IA/NLP
    2. Generar PRD
    3. Crear tareas
    4. Enviar callback al Gatekeeper
    """
    workflow_execution_id = f"mock-exec-{int(time.time())}"
    
    try:
        logger.info(f"🔄 [mock-{payload.workflow_trigger_id}] Procesamiento iniciado")
        
        # Simular delay de procesamiento real (2-5 segundos)
        processing_delay = random.uniform(2.0, 5.0)
        logger.info(f"⏳ [mock-{payload.workflow_trigger_id}] Simulando procesamiento ({processing_delay:.1f}s)...")
        await asyncio.sleep(processing_delay)
        
        # Simular llamada al servicio IA/NLP
        logger.info(f"🤖 [mock-{payload.workflow_trigger_id}] Llamando a IA/NLP service...")
        nlp_results = await simulate_nlp_processing(payload)
        
        # Simular generación de PRD y tareas
        logger.info(f"📄 [mock-{payload.workflow_trigger_id}] Generando PRD y tareas...")
        prd_results = simulate_prd_generation(nlp_results)
        
        # Calcular duración real del procesamiento
        actual_duration_minutes = int(processing_delay / 60 * payload.estimated_duration_minutes)
        if actual_duration_minutes < 1:
            actual_duration_minutes = random.randint(1, 3)
        
        # Preparar callback payload
        callback_payload = {
            "user_id": payload.user_id,
            "meeting_id": payload.meeting_id,
            "processing_id": payload.workflow_trigger_id,
            "actual_duration_minutes": actual_duration_minutes,
            "prd_generated": True,
            "tasks_created": prd_results["tasks_count"],
            "requirements_extracted": prd_results["requirements_count"],
            "workflow_execution_id": workflow_execution_id,
            "processing_status": "completed",
            "error_message": None
        }
        
        # Enviar callback al Gatekeeper
        logger.info(f"📤 [mock-{payload.workflow_trigger_id}] Enviando callback a Gatekeeper...")
        await send_callback_to_gatekeeper(
            callback_url=payload.callbacks["consumption_update"],
            callback_payload=callback_payload
        )
        
        logger.info(f"✅ [mock-{payload.workflow_trigger_id}] Procesamiento completado exitosamente")
        logger.info("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ [mock-{payload.workflow_trigger_id}] Error en procesamiento: {str(e)}")
        
        # Enviar callback de fallo
        error_callback_payload = {
            "user_id": payload.user_id,
            "meeting_id": payload.meeting_id,
            "processing_id": payload.workflow_trigger_id,
            "actual_duration_minutes": 0,
            "prd_generated": False,
            "tasks_created": 0,
            "requirements_extracted": 0,
            "workflow_execution_id": workflow_execution_id,
            "processing_status": "failed",
            "error_message": str(e)
        }
        
        await send_callback_to_gatekeeper(
            callback_url=payload.callbacks["consumption_update"],
            callback_payload=error_callback_payload
        )


async def simulate_nlp_processing(payload: WebhookPayload) -> Dict[str, Any]:
    """Simula el procesamiento del servicio IA/NLP."""
    # Simular delay de NLP
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # Simular extracción de requisitos
    word_count = len(payload.transcription_text.split())
    requirements_count = max(3, int(word_count / 50))  # 1 requisito cada ~50 palabras
    
    return {
        "success": True,
        "requirements_count": requirements_count,
        "word_count": word_count,
        "language": payload.language
    }


def simulate_prd_generation(nlp_results: Dict[str, Any]) -> Dict[str, Any]:
    """Simula la generación de PRD y tareas."""
    requirements_count = nlp_results["requirements_count"]
    
    # Simular generación de tareas (1-2 tareas por requisito)
    tasks_count = requirements_count + random.randint(0, requirements_count)
    
    return {
        "prd_generated": True,
        "prd_id": f"prd-mock-{int(time.time())}",
        "requirements_count": requirements_count,
        "tasks_count": tasks_count
    }


async def send_callback_to_gatekeeper(callback_url: str, callback_payload: Dict[str, Any]):
    """
    📤 Enviar callback al Gatekeeper con los resultados del procesamiento.
    
    Simula lo que n8n haría: hacer POST al callback endpoint del Gatekeeper.
    """
    logger.info(f"🔗 Enviando callback a: {callback_url}")
    logger.info(f"📦 Payload: {callback_payload}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                callback_url,
                json=callback_payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Callback enviado exitosamente: {response.status_code}")
                logger.info(f"📥 Response: {response.json()}")
            else:
                logger.warning(f"⚠️ Callback respondió con código: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                
    except Exception as e:
        logger.error(f"❌ Error enviando callback: {str(e)}")


# ================================================================================================
# 🏥 HEALTH CHECK
# ================================================================================================

@app.get("/health")
async def health_check():
    """Health check del mock server."""
    return {
        "status": "healthy",
        "service": "mock-n8n-server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "message": "🧪 Mock n8n server running for local testing"
    }


@app.get("/")
async def root():
    """Información del mock server."""
    return {
        "service": "🧪 Mock n8n Server",
        "description": "Simula n8n para testing local sin configurar n8n real",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/process-meeting",
            "health": "/health"
        },
        "usage": """
        Este servidor simula n8n localmente:
        
        1. Recibe webhooks del Gatekeeper en /webhook/process-meeting
        2. Simula procesamiento (transcripción → IA/NLP → PRD)
        3. Envía callback al Gatekeeper con resultados
        
        Para usarlo:
        1. Iniciar este servidor: python mock_n8n_server.py
        2. El servidor corre en http://localhost:5678
        3. El Gatekeeper puede enviar webhooks sin configurar n8n real
        """
    }


# ================================================================================================
# 🚀 MAIN ENTRY POINT
# ================================================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🧪 MOCK N8N SERVER - Iniciando...")
    logger.info("=" * 80)
    logger.info("📍 URL: http://localhost:5678")
    logger.info("🎯 Webhook endpoint: http://localhost:5678/webhook/process-meeting")
    logger.info("🏥 Health check: http://localhost:5678/health")
    logger.info("=" * 80)
    logger.info("")
    logger.info("✅ El servidor simulará el comportamiento completo de n8n:")
    logger.info("   1. Recibir webhooks del Gatekeeper")
    logger.info("   2. Simular procesamiento (2-5 segundos)")
    logger.info("   3. Enviar callback con resultados")
    logger.info("")
    logger.info("💡 Tip: Configura N8N_WEBHOOK_URL=http://localhost:5678/webhook/process-meeting")
    logger.info("=" * 80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5678,
        log_level="info"
    )
