# 🔗 Guía de Integración n8n - M2PRD-001 SaaS

## Resumen Ejecutivo

Esta guía documenta la integración completa entre el sistema M2PRD-001 y la plataforma de automatización de workflows **n8n** (o Make como alternativa). El sistema utiliza webhooks para orquestar el procesamiento completo de reuniones: desde la autorización de consumo hasta la actualización final de horas utilizadas.

---

## Tabla de Contenidos

1. [Arquitectura de Integración](#arquitectura-de-integración)
2. [Flujo Completo de Procesamiento](#flujo-completo-de-procesamiento)
3. [Endpoints y Contratos de API](#endpoints-y-contratos-de-api)
4. [Configuración de n8n](#configuración-de-n8n)
5. [Manejo de Errores y Reintentos](#manejo-de-errores-y-reintentos)
6. [Seguridad y Autenticación](#seguridad-y-autenticación)
7. [Testing y Debugging](#testing-y-debugging)
8. [Monitoreo y Observabilidad](#monitoreo-y-observabilidad)

---

## Arquitectura de Integración

### Componentes del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE INTEGRACIÓN n8n                     │
└─────────────────────────────────────────────────────────────────┘

[1] Cliente/Frontend
      ↓ POST /process/start
[2] Gatekeeper Backend (FastAPI) 🚦
      ├─ Verificar consumo (ACID)
      ├─ Autorización ✅/❌
      └─ Trigger webhook → n8n
                            ↓
[3] n8n Workflow Orchestrator 🔄
      ├─ Recibir webhook trigger
      ├─ Procesar transcripción
      ├─ Llamar IA/NLP service
      ├─ Generar PRD
      ├─ Crear tareas
      └─ Callback → Gatekeeper
                            ↓
[4] Gatekeeper Backend (Callback) 📥
      ├─ Recibir resultados
      ├─ Actualizar consumo (ACID)
      └─ Confirmar a n8n
```

### Separación de Responsabilidades

| Componente | Responsabilidad | Principio SOLID |
|------------|----------------|-----------------|
| **Gatekeeper Backend** | Control de consumo y autorización | SRP - Single Responsibility |
| **n8n Workflow** | Orquestación de procesamiento | OCP - Open/Closed |
| **IA/NLP Service** | Procesamiento de transcripciones | DIP - Dependency Inversion |
| **Callback Endpoint** | Actualización post-procesamiento | ISP - Interface Segregation |

---

## Flujo Completo de Procesamiento

### Fase 1: Autorización y Trigger (Gatekeeper → n8n)

```mermaid
sequenceDiagram
    participant Client as Cliente/Frontend
    participant GK as Gatekeeper Backend
    participant DB as PostgreSQL
    participant N8N as n8n Workflow

    Client->>GK: POST /process/start
    Note over Client,GK: {user_id, meeting_id, transcription, ...}
    
    GK->>DB: BEGIN TRANSACTION
    GK->>DB: SELECT available_hours
    DB-->>GK: Horas disponibles
    
    alt ✅ Consumo OK
        GK->>N8N: POST webhook trigger
        Note over GK,N8N: Payload completo con transcripción
        N8N-->>GK: 200 OK (trigger recibido)
        GK->>DB: COMMIT
        GK-->>Client: 200 OK (authorized=true)
    else ❌ Consumo Insuficiente
        GK->>DB: ROLLBACK
        GK-->>Client: 403 Forbidden (insufficient_hours)
    end
```

### Fase 2: Procesamiento en n8n

```mermaid
graph LR
    A[n8n recibe webhook] --> B{Validar payload}
    B -->|Válido| C[Procesar transcripción]
    B -->|Inválido| Z[Error y callback]
    
    C --> D[Llamar IA/NLP service]
    D --> E[Generar PRD]
    E --> F[Crear tareas]
    F --> G[Calcular duración real]
    G --> H[Callback a Gatekeeper]
    
    H --> I{¿Callback exitoso?}
    I -->|Sí| J[Fin exitoso]
    I -->|No| K[Reintentar callback]
    K --> H
```

### Fase 3: Callback y Actualización (n8n → Gatekeeper)

```mermaid
sequenceDiagram
    participant N8N as n8n Workflow
    participant GK as Gatekeeper Backend
    participant DB as PostgreSQL
    participant Client as Cliente (notificación)

    N8N->>GK: POST /process/callback
    Note over N8N,GK: {processing_id, actual_duration, results}
    
    alt ✅ Procesamiento Exitoso
        GK->>DB: BEGIN TRANSACTION
        GK->>DB: UPDATE consumption
        GK->>DB: INSERT usage_log
        GK->>DB: COMMIT
        GK-->>N8N: 200 OK (consumption_updated=true)
        GK->>Client: Notificación (PRD listo)
    else ❌ Procesamiento Falló
        GK-->>N8N: 200 OK (consumption_updated=false)
        Note over GK,N8N: Fallo reconocido, no se actualiza consumo
    end
```

---

## Endpoints y Contratos de API

### 1. Endpoint de Trigger: `/api/v1/consumption/process/start`

**Método:** `POST`  
**Propósito:** Autorizar procesamiento y disparar workflow n8n

#### Request Body

```json
{
  "user_id": "user-123",
  "meeting_id": "meeting-456",
  "meeting_url": "https://meet.google.com/abc-defg-hij",
  "estimated_duration_minutes": 60,
  "transcription_text": "Juan: Necesitamos implementar un sistema de autenticación con JWT...",
  "language": "es"
}
```

#### Success Response (200 OK)

```json
{
  "authorized": true,
  "message": "Processing initiated successfully. ID: proc-meeting-456-1234567890",
  "user_id": "user-123",
  "remaining_hours": 8.5,
  "consumption_percentage": 15.0,
  "workflow_trigger_url": "https://n8n.company.com/webhook/process-meeting"
}
```

#### Error Responses

**403 Forbidden** - Horas insuficientes:
```json
{
  "error": "INSUFFICIENT_HOURS",
  "message": "Not enough hours available. Required: 1.00, Available: 0.50",
  "user_id": "user-123",
  "available_hours": 0.5,
  "required_hours": 1.0
}
```

**503 Service Unavailable** - Webhook n8n falló:
```json
{
  "error": "WORKFLOW_UNAVAILABLE",
  "message": "Processing service temporarily unavailable. Please try again later.",
  "processing_id": "proc-meeting-456-1234567890",
  "user_id": "user-123"
}
```

---

### 2. Webhook Payload a n8n

**URL del Webhook:** Configurada en variable de entorno `N8N_WEBHOOK_URL`

#### Estructura del Payload

```json
{
  "user_id": "user-123",
  "meeting_id": "meeting-456",
  "meeting_url": "https://meet.google.com/abc-defg-hij",
  "transcription_text": "Transcripción completa de la reunión...",
  "language": "es",
  "estimated_duration_minutes": 60,
  
  "remaining_hours": 8.5,
  "plan_name": "Professional",
  "consumption_percentage": 15.0,
  
  "workflow_trigger_id": "proc-meeting-456-1234567890",
  "triggered_at": "2024-01-15T14:30:00Z",
  
  "callbacks": {
    "consumption_update": "http://localhost:8002/api/v1/consumption/process/callback",
    "status_update": "http://localhost:8002/api/v1/workflow/status"
  },
  
  "services": {
    "nlp_service_url": "http://localhost:8003",
    "gatekeeper_service_url": "http://localhost:8002"
  }
}
```

#### Campos del Payload

| Campo | Tipo | Descripción | Obligatorio |
|-------|------|-------------|-------------|
| `user_id` | string | ID del usuario | ✅ |
| `meeting_id` | string | ID único de la reunión | ✅ |
| `transcription_text` | string | Texto completo de la transcripción | ✅ |
| `workflow_trigger_id` | string | ID único del procesamiento | ✅ |
| `callbacks.consumption_update` | string | URL para callback de actualización | ✅ |
| `services.nlp_service_url` | string | URL del servicio IA/NLP | ✅ |

---

### 3. Endpoint de Callback: `/api/v1/consumption/process/callback`

**Método:** `POST`  
**Propósito:** Recibir notificación de n8n después del procesamiento

#### Request Body

```json
{
  "user_id": "user-123",
  "meeting_id": "meeting-456",
  "processing_id": "proc-meeting-456-1234567890",
  "actual_duration_minutes": 75,
  
  "prd_generated": true,
  "tasks_created": 12,
  "requirements_extracted": 8,
  
  "workflow_execution_id": "n8n-exec-789",
  "processing_status": "completed",
  "error_message": null
}
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Processing completed successfully. Consumption updated.",
  "processing_id": "proc-meeting-456-1234567890",
  "consumption_updated": true,
  "remaining_hours": 7.75,
  "consumption_percentage": 22.5
}
```

#### Procesamiento Fallido (n8n notifica error)

**Request:**
```json
{
  "user_id": "user-123",
  "meeting_id": "meeting-456",
  "processing_id": "proc-meeting-456-1234567890",
  "actual_duration_minutes": 75,
  "prd_generated": false,
  "processing_status": "failed",
  "error_message": "IA/NLP service timeout"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processing failure acknowledged. No consumption update performed.",
  "processing_id": "proc-meeting-456-1234567890",
  "consumption_updated": false
}
```

---

## Configuración de n8n

### Paso 1: Crear Workflow en n8n

1. **Crear nuevo Workflow** en n8n
2. **Agregar nodo Webhook** como trigger
3. **Configurar método:** POST
4. **Configurar path:** `/webhook/process-meeting`
5. **Copiar URL del webhook** generada

Ejemplo de URL:
```
https://n8n.yourcompany.com/webhook/process-meeting
```

### Paso 2: Configurar Variables de Entorno

En el backend de Gatekeeper, configurar:

```bash
# .env o variables de entorno
N8N_WEBHOOK_URL=https://n8n.yourcompany.com/webhook/process-meeting
N8N_API_KEY=your-n8n-api-key-here  # Si usas autenticación
N8N_TIMEOUT_SECONDS=60
N8N_MAX_RETRIES=3
```

### Paso 3: Estructura del Workflow n8n

```
[1] Webhook Trigger
     ↓
[2] Validate Payload (Function Node)
     ↓
[3] HTTP Request → IA/NLP Service
     ├─ URL: {{$json.services.nlp_service_url}}/process
     ├─ Method: POST
     └─ Body: {transcription_text, language}
     ↓
[4] Process NLP Results (Function Node)
     ↓
[5] Generate PRD (Function Node)
     ↓
[6] Create Tasks (Function Node)
     ↓
[7] Calculate Duration (Function Node)
     ↓
[8] HTTP Request → Callback Gatekeeper
     ├─ URL: {{$json.callbacks.consumption_update}}
     ├─ Method: POST
     └─ Body: {processing_id, actual_duration, results}
     ↓
[9] Handle Callback Response
```

### Paso 4: Configuración de Nodos Específicos

#### Nodo 3: HTTP Request a IA/NLP Service

```javascript
// URL
{{ $json.services.nlp_service_url }}/api/v1/nlp/process

// Headers
Content-Type: application/json

// Body (JSON)
{
  "text": "{{ $json.transcription_text }}",
  "language": "{{ $json.language }}",
  "extract_requirements": true,
  "assign_tasks": true,
  "detect_priorities": true,
  "user_metadata": {
    "user_id": "{{ $json.user_id }}",
    "meeting_id": "{{ $json.meeting_id }}"
  }
}
```

#### Nodo 8: HTTP Request a Callback

```javascript
// URL
{{ $json.callbacks.consumption_update }}

// Headers
Content-Type: application/json

// Body (JSON)
{
  "user_id": "{{ $json.user_id }}",
  "meeting_id": "{{ $json.meeting_id }}",
  "processing_id": "{{ $json.workflow_trigger_id }}",
  "actual_duration_minutes": {{ $json.calculated_duration }},
  "prd_generated": {{ $json.prd_generated }},
  "tasks_created": {{ $json.tasks_count }},
  "requirements_extracted": {{ $json.requirements_count }},
  "workflow_execution_id": "{{ $workflow.id }}",
  "processing_status": "completed"
}
```

---

## Manejo de Errores y Reintentos

### Estrategia de Reintentos en Gatekeeper

El componente `WebhookTrigger` implementa reintentos automáticos:

```python
# Configuración por entorno
development:
  timeout_seconds: 30
  max_retries: 2
  retry_delay_seconds: 1.0

staging:
  timeout_seconds: 45
  max_retries: 3
  retry_delay_seconds: 2.0

production:
  timeout_seconds: 60
  max_retries: 5
  retry_delay_seconds: 3.0
```

### Backoff Exponencial

```python
# Algoritmo de espera
wait_time = retry_delay_seconds * attempt_number

# Ejemplo:
# Intento 1 → Espera 1s antes del retry
# Intento 2 → Espera 2s antes del retry
# Intento 3 → Espera 3s antes del retry
```

### Estados del Circuit Breaker

| Estado | Descripción | Acción |
|--------|-------------|--------|
| **CLOSED** | Funcionando normalmente | Permitir llamadas |
| **OPEN** | Fallos excedieron threshold | Rechazar llamadas inmediatamente |
| **HALF_OPEN** | Intentando recuperación | Permitir llamada de prueba |

---

## Seguridad y Autenticación

### Seguridad del Webhook Trigger (Gatekeeper → n8n)

#### Opción 1: Autenticación Básica en URL

```bash
N8N_WEBHOOK_URL=https://username:password@n8n.yourcompany.com/webhook/process-meeting
```

#### Opción 2: Bearer Token en Headers

```python
# En WebhookTrigger
self.http_client = httpx.AsyncClient(
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {N8N_API_KEY}"
    }
)
```

### Seguridad del Callback (n8n → Gatekeeper)

**⚠️ CRÍTICO EN PRODUCCIÓN:**

#### Opción 1: API Key Específica para n8n

```python
# En consumption_router.py
from fastapi import Header, HTTPException

@router.post("/process/callback")
async def n8n_processing_callback(
    callback_data: N8NCallbackRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    # Validar API Key
    if x_api_key != N8N_CALLBACK_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Procesar callback...
```

#### Opción 2: Whitelist de IPs

```python
# En consumption_router.py
from fastapi import Request

ALLOWED_N8N_IPS = ["203.0.113.0", "198.51.100.0"]

@router.post("/process/callback")
async def n8n_processing_callback(
    request: Request,
    callback_data: N8NCallbackRequest
):
    client_ip = request.client.host
    if client_ip not in ALLOWED_N8N_IPS:
        raise HTTPException(status_code=403, detail="IP not allowed")
    
    # Procesar callback...
```

#### Opción 3: Firma HMAC

```python
import hmac
import hashlib
from fastapi import Header, HTTPException

N8N_WEBHOOK_SECRET = "your-secret-key"

@router.post("/process/callback")
async def n8n_processing_callback(
    callback_data: N8NCallbackRequest,
    x_signature: str = Header(..., alias="X-Signature")
):
    # Calcular firma esperada
    payload_bytes = callback_data.json().encode('utf-8')
    expected_signature = hmac.new(
        N8N_WEBHOOK_SECRET.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Validar firma
    if not hmac.compare_digest(x_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Procesar callback...
```

---

## Testing y Debugging

### Testing Local sin n8n

Para development, puedes usar un mock del webhook:

```bash
# Iniciar mock server de n8n
python -m backend.tests.integration.mock_n8n_server
```

```python
# mock_n8n_server.py
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/webhook/process-meeting")
async def mock_n8n_webhook(request: Request):
    payload = await request.json()
    
    print(f"📥 Mock n8n received webhook:")
    print(f"  - Meeting ID: {payload['meeting_id']}")
    print(f"  - User ID: {payload['user_id']}")
    print(f"  - Transcription length: {len(payload['transcription_text'])} chars")
    
    # Simular procesamiento
    import time
    time.sleep(2)
    
    # Simular callback a Gatekeeper
    import httpx
    async with httpx.AsyncClient() as client:
        callback_response = await client.post(
            payload['callbacks']['consumption_update'],
            json={
                "user_id": payload['user_id'],
                "meeting_id": payload['meeting_id'],
                "processing_id": payload['workflow_trigger_id'],
                "actual_duration_minutes": 75,
                "prd_generated": True,
                "tasks_created": 12,
                "requirements_extracted": 8,
                "processing_status": "completed"
            }
        )
        print(f"✅ Callback sent to Gatekeeper: {callback_response.status_code}")
    
    return {"status": "processing", "workflow_id": "mock-12345"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5678)
```

### Ejecutar Tests de Integración

```bash
# Activar virtual environment
source venv/bin/activate

# Ejecutar tests del callback
pytest backend/tests/integration/test_n8n_callback.py -v

# Ejecutar tests del webhook trigger
pytest backend/tests/integration/test_gatekeeper_webhook_integration.py -v

# Ejecutar tests con coverage
pytest backend/tests/integration/ --cov=backend.app --cov-report=html
```

### Debugging de Webhooks en Producción

#### Herramienta 1: n8n Execution Logs

En n8n → Executions → Ver detalles del workflow

#### Herramienta 2: Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "webhook_triggered",
    meeting_id=meeting_id,
    user_id=user_id,
    processing_id=processing_id,
    webhook_url=webhook_url,
    response_time_ms=response_time
)
```

#### Herramienta 3: Webhook Testing Tools

- **RequestBin**: https://requestbin.com
- **Webhook.site**: https://webhook.site
- **ngrok**: Para exponer localhost temporalmente

```bash
# Exponer puerto 8002 públicamente
ngrok http 8002
```

---

## Monitoreo y Observabilidad

### Métricas Clave

1. **Webhook Trigger Success Rate**
   ```python
   webhook_trigger_success_rate = 
       successful_triggers / total_triggers * 100
   ```

2. **Callback Response Time**
   ```python
   avg_callback_response_time = 
       sum(response_times) / len(response_times)
   ```

3. **Processing Failure Rate**
   ```python
   processing_failure_rate = 
       failed_processings / total_processings * 100
   ```

### Dashboards Recomendados

#### Grafana Dashboard - n8n Integration

```yaml
panels:
  - title: "Webhook Triggers (Hourly)"
    metrics:
      - webhook_trigger_sent
      - webhook_trigger_failed
      - webhook_trigger_timeout
  
  - title: "Callback Processing (Hourly)"
    metrics:
      - callback_received
      - callback_consumption_updated
      - callback_failed
  
  - title: "Processing Duration Distribution"
    metrics:
      - avg_processing_duration_minutes
      - p50_processing_duration
      - p95_processing_duration
      - p99_processing_duration
```

### Alertas Críticas

```yaml
alerts:
  - name: "High Webhook Failure Rate"
    condition: webhook_failure_rate > 10%
    window: 5 minutes
    action: PagerDuty alert
  
  - name: "n8n Service Unreachable"
    condition: consecutive_webhook_failures >= 5
    action: Slack notification + PagerDuty
  
  - name: "Callback Processing Delayed"
    condition: avg_callback_delay > 5 minutes
    action: Slack notification
```

---

## Checklist de Producción

### Pre-Deployment

- [ ] Variables de entorno configuradas (`N8N_WEBHOOK_URL`, `N8N_API_KEY`)
- [ ] Workflow n8n creado y activado
- [ ] Callback endpoint accesible públicamente
- [ ] Autenticación/seguridad implementada (API Key o HMAC)
- [ ] Whitelist de IPs configurada (si aplica)
- [ ] Tests de integración pasando (100%)
- [ ] Logging estructurado configurado
- [ ] Métricas y alertas configuradas

### Post-Deployment

- [ ] Verificar webhook trigger en n8n (Executions tab)
- [ ] Monitorear logs de Gatekeeper backend
- [ ] Verificar métricas en Grafana/Datadog
- [ ] Realizar test end-to-end con datos reales
- [ ] Documentar URL del webhook en wiki interna

---

## Solución de Problemas Comunes

### Problema 1: Webhook n8n no recibe datos

**Síntomas:**
- Error 503 en `/process/start`
- Logs: `Webhook timeout after 30 seconds`

**Solución:**
1. Verificar que n8n esté accesible: `curl https://n8n.yourcompany.com/health`
2. Verificar URL del webhook correcta
3. Verificar firewall permite tráfico saliente a n8n
4. Aumentar timeout: `N8N_TIMEOUT_SECONDS=60`

### Problema 2: Callback no actualiza consumo

**Síntomas:**
- n8n ejecuta correctamente
- Callback retorna 200 OK
- Consumo no se actualiza en DB

**Solución:**
1. Verificar logs del callback endpoint
2. Verificar que `processing_status` sea `"completed"`
3. Verificar transacción ACID en logs de DB
4. Verificar que el usuario existe y tiene suscripción activa

### Problema 3: Webhook falla intermitentemente

**Síntomas:**
- Algunas llamadas exitosas, otras fallan
- Circuit breaker se abre frecuentemente

**Solución:**
1. Verificar rate limits en n8n
2. Implementar backoff exponencial más agresivo
3. Verificar capacidad de n8n (CPU/memoria)
4. Considerar queue intermedia (Redis/RabbitMQ)

---

## Referencias y Recursos

- **Documentación n8n**: https://docs.n8n.io
- **Repositorio del Proyecto**: `memorymeet/`
- **Código Webhook Trigger**: `backend/app/services/webhook_trigger.py`
- **Código Callback Endpoint**: `backend/app/api/v1/consumption_router.py`
- **Tests de Integración**: `backend/tests/integration/test_n8n_callback.py`

---

## Contacto y Soporte

Para preguntas o soporte técnico sobre la integración n8n:

- **Slack**: #memorymeet-dev
- **Email**: dev-team@memorymeet.com
- **Documentación Interna**: https://wiki.memorymeet.com/n8n-integration

---

**Última actualización:** 2024-01-15  
**Versión del documento:** 1.0  
**Mantenedor:** DevOps Team
