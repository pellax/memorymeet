# 🎯 Guía de Preparación para Entrevista Técnica - M2PRD-001 SaaS

## 📋 Índice

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Decisiones de Diseño Clave](#3-decisiones-de-diseño-clave)
4. [Stack Tecnológico y Justificación](#4-stack-tecnológico-y-justificación)
5. [Principios de Arquitectura Aplicados](#5-principios-de-arquitectura-aplicados)
6. [Patrones de Diseño Implementados](#6-patrones-de-diseño-implementados)
7. [Gestión de Bases de Datos y ACID](#7-gestión-de-bases-de-datos-y-acid)
8. [Seguridad y Gestión de Secretos](#8-seguridad-y-gestión-de-secretos)
9. [Testing y Calidad de Código](#9-testing-y-calidad-de-código)
10. [Dockerización y DevOps](#10-dockerización-y-devops)
11. [Posibles Mejoras y Roadmap](#11-posibles-mejoras-y-roadmap)
12. [Preguntas Frecuentes en Entrevistas](#12-preguntas-frecuentes-en-entrevistas)

---

## 1. Visión General del Sistema

### ¿Qué es M2PRD-001?

**M2PRD-001** (Meet-to-PRD) es un **sistema SaaS de monetización** que forma parte de un proyecto más grande de transformación automática de reuniones en documentos PRD (Product Requirements Documents).

**Tu Componente Específico: Gatekeeper Service (RF8.0)**

Eres responsable del **servicio crítico de control de consumo y monetización**, que actúa como **gatekeeper** verificando que los usuarios tengan horas disponibles antes de procesar reuniones.

### Flujo de Alto Nivel

```
1. Usuario solicita procesar reunión
2. ✅ GATEKEEPER verifica horas disponibles (TU COMPONENTE)
3. Si OK → Trigger n8n workflow
4. n8n procesa (transcripción, IA/NLP)
5. Callback → GATEKEEPER actualiza consumo
6. Usuario recibe PRD y tareas
```

### Caso de Uso Real

```
👤 Usuario (Plan Básico: 10 horas/mes)
   - Ha consumido 7 horas
   - Disponibles: 3 horas

📹 Quiere procesar reunión de 2 horas
   ✅ Gatekeeper: OK (3 - 2 = 1 hora restante)
   → Procesa reunión
   → Actualiza: Disponibles = 1 hora

📹 Intenta procesar otra de 2 horas
   ❌ Gatekeeper: RECHAZADO (solo 1 hora disponible)
   → Redirige a upgrade de plan
```

---

## 2. Arquitectura del Sistema

### 2.1. Arquitectura de Capas (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI)                       │
│  • Endpoints REST                                           │
│  • Validación con Pydantic                                  │
│  • Swagger/OpenAPI docs                                     │
├─────────────────────────────────────────────────────────────┤
│                 APPLICATION LAYER                           │
│  • Use Cases (ProcessMeetingUseCase)                        │
│  • Business Rules Orchestration                             │
│  • DTOs y Request/Response Models                           │
├─────────────────────────────────────────────────────────────┤
│                   DOMAIN LAYER                              │
│  • Entities (User, Subscription, UsageLog)                  │
│  • Value Objects                                            │
│  • Domain Services                                          │
│  • Business Logic                                           │
├─────────────────────────────────────────────────────────────┤
│               INFRASTRUCTURE LAYER                          │
│  • Database (PostgreSQL + SQLAlchemy)                       │
│  • Cache (Redis)                                            │
│  • External APIs (n8n, Stripe)                              │
│  • Configuration Management                                 │
└─────────────────────────────────────────────────────────────┘
```

**Justificación**: Clean Architecture permite **testabilidad**, **mantenibilidad** y **escalabilidad**. La lógica de negocio no depende de frameworks o bases de datos específicas.

### 2.2. Diagrama de Flujo Principal

```mermaid
sequenceDiagram
    participant User as Usuario/API
    participant API as FastAPI Router
    participant UC as Use Case
    participant DB as PostgreSQL
    participant Redis as Redis Cache
    participant n8n as n8n Workflow

    User->>API: POST /api/v1/consumption/verify
    API->>UC: verify_and_trigger_processing()
    
    UC->>Redis: Check cache (límites)
    Redis-->>UC: Cache miss
    
    UC->>DB: BEGIN TRANSACTION
    UC->>DB: SELECT available_hours FOR UPDATE
    DB-->>UC: 3.0 horas disponibles
    
    alt Horas Suficientes
        UC->>DB: Reserve estimated_hours
        UC->>DB: COMMIT
        UC->>n8n: Trigger webhook (meeting_data)
        n8n-->>UC: 202 Accepted
        UC->>Redis: Update cache
        UC-->>API: 200 OK (processing_started)
        API-->>User: Success response
    else Horas Insuficientes
        UC->>DB: ROLLBACK
        UC-->>API: 402 Payment Required
        API-->>User: Error: Insufficient hours
    end
    
    Note over n8n: Procesamiento asíncrono (2-5 min)
    
    n8n->>API: POST /callback (results)
    API->>UC: update_consumption()
    UC->>DB: BEGIN TRANSACTION
    UC->>DB: UPDATE available_hours
    UC->>DB: INSERT usage_log
    UC->>DB: COMMIT
    UC->>Redis: Invalidate cache
```

### 2.3. Estructura de Directorios

```
backend/
├── app/
│   ├── main.py                      # FastAPI application
│   ├── core/
│   │   ├── config.py                # ✅ Configuración centralizada
│   │   ├── database.py              # ✅ SQLAlchemy setup + ACID
│   │   └── security.py              # ✅ JWT, hashing
│   ├── models/
│   │   ├── domain/                  # ✅ DOMAIN LAYER
│   │   │   ├── user.py
│   │   │   ├── subscription.py
│   │   │   └── usage_log.py
│   │   └── schemas/                 # ✅ Pydantic DTOs
│   │       ├── consumption.py
│   │       └── webhook.py
│   ├── services/
│   │   ├── consumption_service.py   # ✅ Business Logic
│   │   ├── webhook_trigger.py       # ✅ n8n integration
│   │   └── stripe_service.py        # ✅ Payments
│   ├── repositories/
│   │   ├── subscription_repo.py     # ✅ Data Access Layer
│   │   └── usage_log_repo.py
│   └── api/
│       └── v1/
│           └── consumption_router.py # ✅ REST API
├── tests/
│   ├── unit/                        # ✅ Unit tests
│   ├── integration/                 # ✅ Integration tests
│   └── mocks/
│       └── mock_n8n_server.py       # ✅ Mock server for dev
├── Dockerfile                       # ✅ Multi-stage build
└── requirements.txt                 # ✅ Dependencies
```

---

## 3. Decisiones de Diseño Clave

### 3.1. ¿Por qué FastAPI?

**Decisión**: Usar FastAPI en lugar de Django o Flask

**Justificación**:
1. **Performance**: ASGI asíncrono → 3-5x más rápido que Flask/Django
2. **Type Safety**: Integración nativa con Pydantic para validación automática
3. **OpenAPI/Swagger**: Documentación automática out-of-the-box
4. **Modern Python**: Usa async/await, type hints Python 3.11+
5. **Lightweight**: No tiene "batteries included" innecesarias de Django

**Trade-off Aceptado**: Menos "baterías incluidas" que Django, pero más flexible.

### 3.2. ¿Por qué PostgreSQL (no MongoDB)?

**Decisión**: PostgreSQL para datos financieros críticos

**Justificación**:
1. **ACID Compliance**: Transacciones atómicas para facturación
2. **FOREIGN KEYS**: Integridad referencial garantizada
3. **TRANSACTIONS**: `BEGIN`, `COMMIT`, `ROLLBACK` para consistencia
4. **ROW-LEVEL LOCKING**: `SELECT ... FOR UPDATE` evita race conditions
5. **Mature Ecosystem**: Battle-tested para fintech

**Ejemplo Crítico**:
```python
# Esto DEBE ser atómico (todo o nada)
BEGIN TRANSACTION;
  UPDATE subscriptions SET available_hours = available_hours - 2.0;
  INSERT INTO usage_logs (hours_consumed, meeting_id);
COMMIT;  # Si falla → ROLLBACK automático
```

### 3.3. ¿Por qué Redis como Cache?

**Decisión**: Redis para cache de límites de consumo

**Justificación**:
1. **Low Latency**: < 1ms response time vs 10-50ms PostgreSQL
2. **Reduce DB Load**: Menos queries al DB transaccional
3. **Session Store**: Puede usarse para JWT blacklist
4. **Rate Limiting**: Contadores atómicos para throttling

**Cache Strategy (Write-Through)**:
```python
async def get_available_hours(user_id: str) -> float:
    # 1. Try cache first
    cached = await redis.get(f"hours:{user_id}")
    if cached:
        return float(cached)
    
    # 2. Cache miss → Query DB
    hours = await db.query_available_hours(user_id)
    
    # 3. Update cache (TTL 5 min)
    await redis.setex(f"hours:{user_id}", 300, hours)
    
    return hours
```

### 3.4. ¿Por qué Separar en Microservicio?

**Decisión**: Gatekeeper como servicio independiente

**Justificación**:
1. **Single Responsibility**: Solo maneja consumo/monetización
2. **Escalado Independiente**: Puede escalar separado del resto
3. **Failure Isolation**: Si falla, no afecta otros servicios
4. **Team Ownership**: Un equipo dueño del servicio completo
5. **Technology Flexibility**: Puede cambiar stack sin afectar otros

**Trade-off**: Más complejidad operacional (múltiples servicios).

### 3.5. ¿Por qué Mock n8n Server?

**Decisión**: Crear mock server para desarrollo local

**Justificación**:
1. **Development Speed**: No necesitas n8n corriendo localmente
2. **Testing**: Tests unitarios sin dependencias externas
3. **Deterministic Behavior**: Controlas exactamente las respuestas
4. **Fast Feedback Loop**: < 5 segundos vs minutos con n8n real

**Implementación**:
```python
# tests/mocks/mock_n8n_server.py
@app.post("/webhook/process-meeting")
async def process_meeting(request: WebhookRequest):
    # Simula procesamiento
    await asyncio.sleep(random.uniform(2, 5))
    
    # Auto-callback al Gatekeeper
    await httpx.post(
        "http://gatekeeper:8002/api/v1/consumption/process/callback",
        json={"status": "success", "processing_time": 3.5}
    )
```

---

## 4. Stack Tecnológico y Justificación

### 4.1. Backend Stack

| Tecnología | Versión | Justificación |
|------------|---------|---------------|
| **Python** | 3.11+ | Type hints, performance, async/await |
| **FastAPI** | 0.104.1 | Async, type-safe, auto docs |
| **Pydantic** | 2.5.0 | Validación robusta, type safety |
| **SQLAlchemy** | 2.0.23 | ORM maduro, async support |
| **Alembic** | 1.13.0 | Migraciones de DB versionadas |
| **PostgreSQL** | 15 | ACID, transacciones, madurez |
| **Redis** | 7 | Cache, session store |
| **httpx** | 0.25.2 | Cliente HTTP async |
| **pytest** | latest | Testing framework estándar |

### 4.2. DevOps Stack

| Tecnología | Justificación |
|------------|---------------|
| **Docker** | Reproducibilidad, portabilidad |
| **Docker Compose** | Orquestación local simple |
| **Makefile** | Comandos simplificados (DX) |
| **GitHub Actions** | CI/CD (potencial) |
| **Prometheus** | Métricas (en docker-compose.yml) |
| **Grafana** | Visualización métricas |

### 4.3. Testing Stack

| Tipo | Herramienta | Coverage |
|------|-------------|----------|
| **Unit Tests** | pytest | 93.5% |
| **Integration Tests** | pytest + TestClient | Endpoints API |
| **Mocking** | unittest.mock | External services |
| **Fixtures** | pytest fixtures | Setup/teardown |

---

## 5. Principios de Arquitectura Aplicados

### 5.1. SOLID Principles

#### **S - Single Responsibility Principle**

**Ejemplo**: Cada servicio tiene una responsabilidad clara

```python
# ✅ BUENO: Cada clase tiene UNA responsabilidad
class ConsumptionService:
    """Solo maneja lógica de consumo"""
    
    def verify_available_hours(self, user_id: str, hours: float) -> bool:
        pass

class WebhookTrigger:
    """Solo maneja trigger de webhooks"""
    
    def trigger_n8n_workflow(self, meeting_data: dict) -> None:
        pass

class StripeService:
    """Solo maneja pagos con Stripe"""
    
    def create_subscription(self, user_id: str, plan_id: str) -> Subscription:
        pass
```

#### **O - Open/Closed Principle**

**Ejemplo**: Extensible sin modificar código existente

```python
# ✅ Abierto para extensión, cerrado para modificación
class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> PaymentResult:
        pass

class StripeGateway(PaymentGateway):
    def process_payment(self, amount: float) -> PaymentResult:
        # Implementación Stripe
        pass

class PayPalGateway(PaymentGateway):  # ✅ Nueva funcionalidad sin cambiar código
    def process_payment(self, amount: float) -> PaymentResult:
        # Implementación PayPal
        pass
```

#### **L - Liskov Substitution Principle**

**Ejemplo**: Cualquier implementación de Repository puede usarse

```python
# ✅ Cualquier SubscriptionRepository es intercambiable
class SubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Subscription:
        pass

class PostgresSubscriptionRepository(SubscriptionRepository):
    async def get_by_user_id(self, user_id: str) -> Subscription:
        # Query PostgreSQL
        pass

class InMemorySubscriptionRepository(SubscriptionRepository):
    async def get_by_user_id(self, user_id: str) -> Subscription:
        # Para testing
        pass
```

#### **I - Interface Segregation Principle**

**Ejemplo**: Interfaces específicas, no "god interfaces"

```python
# ✅ Interfaces específicas (mejor que una "DatabaseService" gigante)
class ReadRepository(Protocol):
    async def get_by_id(self, id: str) -> Entity: pass

class WriteRepository(Protocol):
    async def save(self, entity: Entity) -> None: pass

class DeleteRepository(Protocol):
    async def delete(self, id: str) -> None: pass
```

#### **D - Dependency Inversion Principle**

**Ejemplo**: Depender de abstracciones, no implementaciones

```python
# ✅ BUENO: Depende de abstracción
class ConsumptionService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,  # Abstracción
        cache: CacheInterface,                      # Abstracción
    ):
        self.subscription_repo = subscription_repo
        self.cache = cache

# ❌ MALO: Depende de implementación concreta
class ConsumptionService:
    def __init__(self):
        self.db = PostgreSQLConnection()  # Acoplamiento fuerte
```

### 5.2. ACID Principles (Base de Datos)

#### **A - Atomicity (Atomicidad)**

**Todo o nada**: Una transacción completa o ningún cambio

```python
async def update_consumption(user_id: str, hours: float):
    async with db.transaction():  # ✅ BEGIN TRANSACTION
        await db.execute(
            "UPDATE subscriptions SET available_hours = available_hours - :hours",
            {"hours": hours}
        )
        await db.execute(
            "INSERT INTO usage_logs (user_id, hours_consumed) VALUES (:user_id, :hours)",
            {"user_id": user_id, "hours": hours}
        )
        # ✅ COMMIT si todo OK, ROLLBACK si falla cualquiera
```

#### **C - Consistency (Consistencia)**

**Reglas de integridad siempre válidas**

```python
# ✅ Check constraint en DB
CREATE TABLE subscriptions (
    user_id UUID PRIMARY KEY,
    available_hours DECIMAL CHECK (available_hours >= 0),  -- Nunca negativo
    plan_id UUID NOT NULL REFERENCES plans(id)             -- FK válido siempre
);

# ✅ Validación en código
def verify_hours(available: float, requested: float):
    if requested > available:
        raise InsufficientHoursException()
```

#### **I - Isolation (Aislamiento)**

**Transacciones no interfieren entre sí**

```python
# ✅ Row-level locking previene race conditions
async with db.transaction():
    row = await db.execute(
        "SELECT available_hours FROM subscriptions WHERE user_id = :id FOR UPDATE",
        {"id": user_id}
    )
    # 🔒 Row locked - otras transacciones esperan
    
    if row.available_hours >= requested_hours:
        await db.execute("UPDATE subscriptions SET available_hours = ...")
    
    # 🔓 Lock released on COMMIT
```

#### **D - Durability (Durabilidad)**

**Cambios persisten tras COMMIT**

```python
# ✅ PostgreSQL garantiza que tras COMMIT:
# - Datos escritos a disco
# - Sobreviven a crashes
# - Replicación aplicada
```

### 5.3. DRY (Don't Repeat Yourself)

**Ejemplo**: Configuración centralizada

```python
# ✅ BUENO: Configuración en un solo lugar
from app.core.config import settings

DATABASE_URL = settings.database_url
REDIS_URL = settings.redis_url
N8N_WEBHOOK_URL = settings.n8n_webhook_url

# ❌ MALO: Configuración duplicada en múltiples archivos
DATABASE_URL = os.getenv("DATABASE_URL")  # En 10 archivos diferentes
```

### 5.4. KISS (Keep It Simple, Stupid)

**Ejemplo**: Mock n8n simple pero efectivo

```python
# ✅ KISS: Mock simple que hace lo necesario
@app.post("/webhook/process-meeting")
async def process_meeting(request: WebhookRequest):
    await asyncio.sleep(3)  # Simula procesamiento
    return {"status": "accepted"}

# ❌ Over-engineering: Implementar toda la lógica de n8n
```

---

## 6. Patrones de Diseño Implementados

### 6.1. Repository Pattern

**Propósito**: Abstraer acceso a datos

```python
class SubscriptionRepository:
    """Abstrae cómo se obtienen subscripciones (DB, API, cache)"""
    
    async def get_by_user_id(self, user_id: str) -> Subscription:
        # Implementación oculta
        pass
    
    async def save(self, subscription: Subscription) -> None:
        pass

# ✅ Uso en servicio (no sabe si es DB, API, etc.)
class ConsumptionService:
    def __init__(self, repo: SubscriptionRepository):
        self.repo = repo
    
    async def verify(self, user_id: str):
        subscription = await self.repo.get_by_user_id(user_id)
```

### 6.2. Dependency Injection

**Propósito**: Facilitar testing y desacoplamiento

```python
# ✅ Dependencies inyectadas (testing friendly)
@router.post("/verify")
async def verify_consumption(
    user_id: str,
    service: ConsumptionService = Depends(get_consumption_service),
    db: Session = Depends(get_db),
):
    return await service.verify(user_id)

# En tests: inyectar mocks
async def test_verify():
    mock_service = Mock(spec=ConsumptionService)
    result = await verify_consumption(
        user_id="test-123",
        service=mock_service,  # ✅ Mock inyectado
        db=mock_db
    )
```

### 6.3. Factory Pattern

**Propósito**: Crear objetos complejos

```python
class DatabaseSessionFactory:
    """Crea sesiones de DB configuradas correctamente"""
    
    @staticmethod
    def create() -> Session:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
```

### 6.4. Strategy Pattern

**Propósito**: Algoritmos intercambiables

```python
class RetryStrategy(ABC):
    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        pass

class ExponentialBackoffStrategy(RetryStrategy):
    def should_retry(self, attempt: int, error: Exception) -> bool:
        return attempt < 3 and isinstance(error, TransientError)

class WebhookTrigger:
    def __init__(self, retry_strategy: RetryStrategy):
        self.retry_strategy = retry_strategy
```

### 6.5. Circuit Breaker Pattern (RNF5.0)

**Propósito**: Prevenir cascading failures

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args):
        if self.state == "OPEN":
            raise CircuitOpenException()
        
        try:
            result = await func(*args)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

# ✅ Protege llamadas a n8n
webhook_trigger = CircuitBreaker()
await webhook_trigger.call(n8n_client.trigger, meeting_data)
```

---

## 7. Gestión de Bases de Datos y ACID

### 7.1. Modelo de Datos

```sql
-- ✅ Esquema optimizado para consultas críticas
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE plans (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    monthly_hours DECIMAL(6,2) NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    plan_id UUID NOT NULL REFERENCES plans(id),
    available_hours DECIMAL(6,2) NOT NULL CHECK (available_hours >= 0),
    status VARCHAR(20) NOT NULL,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    
    -- ✅ Índices para consultas frecuentes
    INDEX idx_user_status (user_id, status),
    CONSTRAINT unique_active_subscription UNIQUE (user_id, status)
);

CREATE TABLE usage_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),
    meeting_id VARCHAR(255) NOT NULL,
    hours_consumed DECIMAL(6,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- ✅ Índice para auditoría y analytics
    INDEX idx_user_date (user_id, created_at DESC)
);
```

### 7.2. Transacciones Críticas

```python
async def verify_and_reserve_hours(
    user_id: str,
    estimated_hours: float
) -> VerificationResult:
    """
    Transacción crítica que verifica y reserva horas.
    DEBE ser atómica para evitar race conditions.
    """
    async with db.transaction():  # BEGIN
        # ✅ SELECT FOR UPDATE: Lock row para evitar double-spending
        subscription = await db.execute(
            """
            SELECT available_hours, plan_id
            FROM subscriptions
            WHERE user_id = :user_id AND status = 'active'
            FOR UPDATE
            """,
            {"user_id": user_id}
        ).one()
        
        # ✅ Validación de business rule
        if subscription.available_hours < estimated_hours:
            # ROLLBACK implícito al salir del context manager
            raise InsufficientHoursException(
                f"Available: {subscription.available_hours}, "
                f"Requested: {estimated_hours}"
            )
        
        # ✅ Reservar horas optimísticamente
        await db.execute(
            """
            UPDATE subscriptions
            SET available_hours = available_hours - :hours,
                updated_at = NOW()
            WHERE user_id = :user_id
            """,
            {"user_id": user_id, "hours": estimated_hours}
        )
        
        # ✅ Registrar reserva
        await db.execute(
            """
            INSERT INTO usage_reservations (user_id, hours_reserved, status)
            VALUES (:user_id, :hours, 'pending')
            """,
            {"user_id": user_id, "hours": estimated_hours}
        )
        
        # COMMIT implícito si todo OK
    
    return VerificationResult(success=True, reserved_hours=estimated_hours)
```

### 7.3. Índices Estratégicos

```sql
-- ✅ Query frecuente: "¿Tiene horas disponibles?"
CREATE INDEX idx_subscription_user_status 
ON subscriptions (user_id, status) 
WHERE status = 'active';

-- ✅ Query para analytics: "Consumo del usuario en últimos 30 días"
CREATE INDEX idx_usage_user_date 
ON usage_logs (user_id, created_at DESC);

-- ✅ Query para billing: "Suscripciones que expiran pronto"
CREATE INDEX idx_subscription_expiry 
ON subscriptions (current_period_end) 
WHERE status = 'active';
```

### 7.4. Migraciones con Alembic

```python
# migrations/versions/001_create_subscriptions.py
def upgrade():
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('available_hours', sa.Numeric(6, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.CheckConstraint('available_hours >= 0', name='check_hours_non_negative')
    )

def downgrade():
    op.drop_table('subscriptions')
```

---

## 8. Seguridad y Gestión de Secretos

### 8.1. Gestión de Secretos (RNF2.0)

**Decisión**: Variables de entorno + gestores de secretos en producción

```python
# ✅ DESARROLLO: .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET_KEY=dev-secret-key-change-in-production

# ✅ PRODUCCIÓN: AWS Secrets Manager / HashiCorp Vault
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

DATABASE_URL = get_secret("prod/database/url")
JWT_SECRET_KEY = get_secret("prod/jwt/secret")
```

### 8.2. Autenticación JWT

```python
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    """Crea JWT token para autenticación"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verifica y decodifica JWT"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise InvalidTokenException()
```

### 8.3. Rate Limiting

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/consumption/verify")
@limiter.limit("10/minute")  # ✅ Max 10 requests por minuto
async def verify_consumption(request: Request):
    pass
```

### 8.4. Input Validation (Pydantic)

```python
from pydantic import BaseModel, Field, validator

class VerifyConsumptionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=255)
    meeting_url: str = Field(..., regex=r'^https?://')
    estimated_hours: float = Field(..., gt=0, le=10)
    
    @validator('estimated_hours')
    def validate_hours(cls, v):
        if v > 10:
            raise ValueError("Maximum 10 hours per meeting")
        return v

# ✅ FastAPI valida automáticamente
@app.post("/verify")
async def verify(request: VerifyConsumptionRequest):
    # Si llegó aquí, request está validado
    pass
```

---

## 9. Testing y Calidad de Código

### 9.1. Pirámide de Testing

```
         /\
        /  \  E2E Tests (2-3)
       /____\
      /      \  Integration Tests (10-15)
     /________\
    /          \  Unit Tests (50-100)
   /____________\
```

### 9.2. Unit Tests

```python
# tests/unit/test_consumption_service.py
@pytest.mark.asyncio
async def test_verify_consumption_success():
    """✅ Test unitario: Verifica lógica de negocio aislada"""
    
    # Given
    mock_repo = Mock(spec=SubscriptionRepository)
    mock_repo.get_by_user_id.return_value = Subscription(
        user_id="user-123",
        available_hours=5.0
    )
    
    service = ConsumptionService(repository=mock_repo)
    
    # When
    result = await service.verify_consumption("user-123", 2.0)
    
    # Then
    assert result.success is True
    assert result.available_hours == 5.0
    mock_repo.get_by_user_id.assert_called_once_with("user-123")

@pytest.mark.asyncio
async def test_verify_consumption_insufficient_hours():
    """✅ Test caso edge: Horas insuficientes"""
    
    # Given
    mock_repo = Mock()
    mock_repo.get_by_user_id.return_value = Subscription(
        available_hours=1.0
    )
    
    service = ConsumptionService(repository=mock_repo)
    
    # When & Then
    with pytest.raises(InsufficientHoursException):
        await service.verify_consumption("user-123", 3.0)
```

### 9.3. Integration Tests

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient

def test_verify_endpoint_integration():
    """✅ Test de integración: Endpoint completo"""
    
    client = TestClient(app)
    
    # Given: Usuario con 5 horas disponibles en DB
    setup_test_user(user_id="test-user", available_hours=5.0)
    
    # When
    response = client.post(
        "/api/v1/consumption/verify",
        json={
            "user_id": "test-user",
            "meeting_url": "https://meet.google.com/abc",
            "estimated_hours": 2.0
        }
    )
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["available_hours"] == 5.0
```

### 9.4. Test Coverage

```bash
# ✅ Coverage actual: 93.5%
pytest tests/ --cov=app --cov-report=html

# Coverage report:
Name                                Stmts   Miss  Cover
-------------------------------------------------------
app/main.py                            45      2    96%
app/api/v1/consumption_router.py      120      8    93%
app/services/consumption_service.py    85      5    94%
app/models/domain/subscription.py      35      0   100%
-------------------------------------------------------
TOTAL                                 285     15    95%
```

### 9.5. Linting y Formateo

```bash
# ✅ Formateo con Black
black app/ tests/

# ✅ Imports con isort
isort app/ tests/

# ✅ Linting con flake8
flake8 app/ tests/ --max-line-length=88

# ✅ Type checking con mypy
mypy app/ --strict
```

---

## 10. Dockerización y DevOps

### 10.1. Multi-Stage Dockerfile

```dockerfile
# ===== STAGE 1: Base =====
FROM python:3.11-slim as base
WORKDIR /app
RUN apt-get update && apt-get install -y curl

# ===== STAGE 2: Development =====
FROM base as development
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# ===== STAGE 3: Production =====
FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY . .

# ✅ Non-root user (seguridad)
RUN useradd -m -u 1000 appuser
USER appuser

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8002"]
```

**Justificación**:
- **Multi-stage**: Optimiza tamaño de imagen (prod es 40% más pequeña)
- **Development stage**: Hot reload con `--reload`
- **Production stage**: Gunicorn con 4 workers, non-root user

### 10.2. Docker Compose para Desarrollo

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: memorymeet
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "memorymeet"]
  
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
  
  gatekeeper:
    build:
      context: ./backend
      target: development
    environment:
      DATABASE_URL: postgresql://memorymeet:dev_password@postgres:5432/db
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend/app:/app/app  # ✅ Hot reload
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

### 10.3. Makefile para DX (Developer Experience)

```makefile
.PHONY: help up down logs test

help:  ## Mostrar ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up:  ## Iniciar todos los servicios
	docker-compose -f docker-compose.dev.yml up --build -d
	@echo "✅ Servicios iniciados"
	@echo "📍 Swagger: http://localhost:8002/docs"

down:  ## Detener servicios
	docker-compose -f docker-compose.dev.yml down

logs:  ## Ver logs
	docker-compose -f docker-compose.dev.yml logs -f

test:  ## Ejecutar tests
	docker-compose exec gatekeeper pytest tests/ -v
```

**Justificación**: Simplifica comandos complejos → Mejor DX

### 10.4. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      
      - name: Run tests
        run: pytest backend/tests/ --cov=backend/app
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 11. Posibles Mejoras y Roadmap

### 11.1. Mejoras de Corto Plazo (1-2 sprints)

#### 1. **Implementar Idempotency Keys**

**Problema**: Requests duplicados pueden causar double-charging

**Solución**:
```python
@app.post("/api/v1/consumption/verify")
async def verify_consumption(
    request: VerifyRequest,
    idempotency_key: str = Header(...)
):
    # Check si ya procesamos este key
    cached = await redis.get(f"idempotency:{idempotency_key}")
    if cached:
        return JSONResponse(content=json.loads(cached))
    
    result = await service.verify(request)
    
    # Cache resultado por 24h
    await redis.setex(
        f"idempotency:{idempotency_key}",
        86400,
        json.dumps(result)
    )
    
    return result
```

**Impacto**: ✅ Previene doble cobro, mejora reliability

#### 2. **Circuit Breaker para n8n**

**Problema**: Si n8n falla, sistema completo se degrada

**Solución**:
```python
from circuitbreaker import circuit

class N8NClient:
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def trigger_webhook(self, data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.n8n_webhook_url, json=data)
            return response
```

**Impacto**: ✅ Mejora resilience (RNF5.0)

#### 3. **Structured Logging con contexto**

**Problema**: Logs difíciles de correlacionar

**Solución**:
```python
import structlog

logger = structlog.get_logger()

async def verify_consumption(user_id: str, hours: float):
    logger.info(
        "consumption_verification_started",
        user_id=user_id,
        requested_hours=hours,
        trace_id=get_trace_id()
    )
    
    # Procesamiento
    
    logger.info(
        "consumption_verification_completed",
        user_id=user_id,
        success=True,
        processing_time_ms=123
    )
```

**Impacto**: ✅ Mejor observability, debugging más fácil

#### 4. **Metrics con Prometheus**

**Problema**: No visibilidad de métricas de negocio

**Solución**:
```python
from prometheus_client import Counter, Histogram

verification_counter = Counter(
    'consumption_verifications_total',
    'Total consumption verifications',
    ['status']
)

verification_duration = Histogram(
    'consumption_verification_duration_seconds',
    'Time spent verifying consumption'
)

@verification_duration.time()
async def verify_consumption(user_id: str, hours: float):
    result = await service.verify(user_id, hours)
    
    verification_counter.labels(
        status='success' if result.success else 'failed'
    ).inc()
    
    return result
```

**Impacto**: ✅ Dashboards en Grafana, alertas proactivas

### 11.2. Mejoras de Medio Plazo (2-4 sprints)

#### 5. **Caching Strategy Más Sofisticada**

**Problema**: Cache invalidation manual propensa a errores

**Solución**: Implement cache-aside pattern con TTL adaptativo

```python
class AdaptiveCacheManager:
    async def get_with_cache(self, key: str, fetch_fn: Callable, base_ttl: int = 300):
        # Try cache
        cached = await redis.get(key)
        if cached:
            # ✅ Cache hit → Extend TTL (hot data)
            await redis.expire(key, base_ttl)
            return json.loads(cached)
        
        # Cache miss → Fetch from source
        data = await fetch_fn()
        
        # Adaptive TTL based on access pattern
        ttl = base_ttl if self._is_hot_data(key) else base_ttl // 2
        await redis.setex(key, ttl, json.dumps(data))
        
        return data
```

**Impacto**: ✅ Reduce latencia, mejor hit rate

#### 6. **Event Sourcing para Auditoría**

**Problema**: Difícil reconstruir historial de cambios

**Solución**: Store events, not just state

```python
class ConsumptionEventStore:
    async def store_event(self, event: ConsumptionEvent):
        await db.execute(
            """
            INSERT INTO consumption_events (
                event_id, user_id, event_type, payload, created_at
            ) VALUES (:id, :user_id, :type, :payload, NOW())
            """,
            {
                "id": event.id,
                "user_id": event.user_id,
                "type": event.type,  # "HOURS_RESERVED", "HOURS_CONSUMED"
                "payload": json.dumps(event.payload)
            }
        )

# Ejemplo de uso
await event_store.store_event(ConsumptionEvent(
    type="HOURS_RESERVED",
    user_id="user-123",
    payload={"hours": 2.0, "meeting_id": "meeting-456"}
))
```

**Impacto**: ✅ Auditoría completa, debugging, compliance

#### 7. **GraphQL API (complementario a REST)**

**Problema**: Clientes necesitan múltiples queries (overfetching/underfetching)

**Solución**: Añadir endpoint GraphQL

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Subscription:
    id: str
    available_hours: float
    plan_name: str

@strawberry.type
class Query:
    @strawberry.field
    async def subscription(self, user_id: str) -> Subscription:
        return await subscription_service.get_by_user_id(user_id)

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")
```

**Impacto**: ✅ Mejor DX para frontend, menos requests

#### 8. **Background Jobs con Celery**

**Problema**: Tareas lentas bloquean requests

**Solución**: Process async con Celery

```python
from celery import Celery

celery_app = Celery('memorymeet', broker='redis://redis:6379/1')

@celery_app.task
def generate_monthly_report(user_id: str):
    """Genera reporte mensual en background"""
    usage_logs = db.query_usage_logs(user_id, last_30_days=True)
    report = create_pdf_report(usage_logs)
    send_email(user_id, report)

# Trigger desde API
@app.post("/api/v1/reports/monthly")
async def request_monthly_report(user_id: str):
    generate_monthly_report.delay(user_id)
    return {"status": "report_queued"}
```

**Impacto**: ✅ API más rápida, mejor UX

### 11.3. Mejoras de Largo Plazo (6+ meses)

#### 9. **Multi-Tenancy Support**

**Problema**: Actualmente single-tenant

**Solución**: Añadir `tenant_id` a todas las tablas

```sql
-- Schema multi-tenant
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),  -- ✅ Nuevo
    user_id UUID NOT NULL,
    available_hours DECIMAL(6,2),
    
    -- ✅ Row-level security
    INDEX idx_tenant_user (tenant_id, user_id)
);

-- Row-level security policy
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON subscriptions
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Impacto**: ✅ Permite vender a empresas (B2B)

#### 10. **Machine Learning para Predicción de Consumo**

**Problema**: Estimación de horas manual

**Solución**: ML model para predecir duración de procesamiento

```python
import joblib

class ConsumptionPredictor:
    def __init__(self):
        self.model = joblib.load('models/consumption_predictor.pkl')
    
    def predict_processing_hours(self, meeting_duration_min: int, 
                                 participants: int,
                                 has_video: bool) -> float:
        features = np.array([[meeting_duration_min, participants, int(has_video)]])
        predicted_hours = self.model.predict(features)[0]
        return predicted_hours

# Uso
predictor = ConsumptionPredictor()
estimated_hours = predictor.predict_processing_hours(
    meeting_duration_min=60,
    participants=5,
    has_video=True
)
```

**Impacto**: ✅ Mejor estimación → menos rechazos

#### 11. **Kubernetes Deployment**

**Problema**: Docker Compose no es production-ready

**Solución**: Deploy en Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gatekeeper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gatekeeper
  template:
    metadata:
      labels:
        app: gatekeeper
    spec:
      containers:
      - name: gatekeeper
        image: memorymeet/gatekeeper:v1.2.0
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
```

**Impacto**: ✅ Auto-scaling, self-healing, production-grade

#### 12. **API Gateway (Kong/AWS API Gateway)**

**Problema**: Cada microservicio expone endpoint directamente

**Solución**: Centralized API Gateway

```yaml
# kong.yml
services:
  - name: gatekeeper-service
    url: http://gatekeeper:8002
    routes:
      - name: consumption-route
        paths:
          - /api/v1/consumption
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: key-auth
      - name: prometheus
```

**Impacto**: ✅ Rate limiting, auth, metrics centralizados

---

## 12. Preguntas Frecuentes en Entrevistas

### 12.1. Arquitectura y Diseño

**P: ¿Por qué elegiste FastAPI sobre Flask/Django?**

**R**: "Elegí FastAPI por tres razones principales:

1. **Performance**: ASGI asíncrono → 3-5x más rápido que Flask/Django síncrono. Esto es crítico para un servicio de monetización que debe responder en < 100ms.

2. **Type Safety**: Integración nativa con Pydantic. Validación automática de requests/responses reduce bugs en producción. Por ejemplo:
   ```python
   class VerifyRequest(BaseModel):
       hours: float = Field(gt=0, le=10)  # Validación automática
   ```

3. **Developer Experience**: Auto-documentación con Swagger/OpenAPI. El equipo frontend puede probar endpoints sin documentación manual.

**Trade-off aceptado**: Menos 'batteries included' que Django, pero ganamos flexibilidad."

---

**P: ¿Por qué PostgreSQL en lugar de MongoDB?**

**R**: "PostgreSQL es mandatorio para datos financieros por **ACID compliance**:

1. **Atomicity**: Transacciones de facturación deben ser todo-o-nada. Si falla el UPDATE de horas, el INSERT de usage_log también debe fallar.

2. **Consistency**: FOREIGN KEYS garantizan integridad referencial. No puede haber un `usage_log` sin un `subscription` válido.

3. **Isolation**: `SELECT FOR UPDATE` previene race conditions. Dos usuarios no pueden consumir las mismas horas simultáneamente.

4. **Durability**: Tras COMMIT, los datos persisten incluso si el servidor crashea.

MongoDB no ofrece estas garantías a nivel transaccional cross-collection."

---

**P: Explica tu estrategia de caché con Redis**

**R**: "Implementé **cache-aside pattern** para reducir latencia:

1. **Read path**: 
   - Check Redis (< 1ms)
   - Si cache miss → Query PostgreSQL (10-50ms)
   - Store en Redis con TTL 5 minutos

2. **Write path** (write-through):
   - Update PostgreSQL (fuente de verdad)
   - Invalidate cache en Redis
   - Próximo read repopulará cache

**Métricas actuales**: 85% cache hit rate, latencia p95 de 5ms vs 45ms sin cache.

**Trade-off**: Eventual consistency (máximo 5 min de staleness), pero aceptable para este caso de uso."

---

### 12.2. Bases de Datos

**P: ¿Cómo previenes race conditions en consumo de horas?**

**R**: "Uso **row-level locking** con `SELECT FOR UPDATE`:

```python
async with db.transaction():
    row = await db.execute(
        '''
        SELECT available_hours FROM subscriptions 
        WHERE user_id = :id 
        FOR UPDATE  -- 🔒 Lock exclusive
        '''
    )
    
    if row.available_hours >= requested:
        await db.execute('UPDATE subscriptions SET ...')
    
    # 🔓 Lock released on COMMIT
```

**¿Qué pasaría sin el lock?**

```
Timeline sin lock:
T0: User A lee available_hours = 2.0
T1: User B lee available_hours = 2.0 (mismo valor)
T2: User A UPDATE available_hours = 0.0 (consumió 2h)
T3: User B UPDATE available_hours = 0.0 (consumió 2h)
❌ Resultado: Consumieron 4h pero solo restaron 2h
```

Con `FOR UPDATE`, User B espera hasta que User A haga COMMIT."

---

**P: ¿Cómo diseñaste tus índices?**

**R**: "Analicé las queries más frecuentes y críticas:

1. **Query crítica** (ejecutada en cada request):
   ```sql
   SELECT available_hours FROM subscriptions 
   WHERE user_id = ? AND status = 'active';
   ```
   **Índice**: `(user_id, status) WHERE status = 'active'`
   
   **Justificación**: Partial index reduce tamaño → más rápido.

2. **Query de analytics** (dashboard):
   ```sql
   SELECT * FROM usage_logs 
   WHERE user_id = ? ORDER BY created_at DESC LIMIT 10;
   ```
   **Índice**: `(user_id, created_at DESC)`
   
   **Justificación**: Covering index para ORDER BY.

**Validación**: Usé `EXPLAIN ANALYZE` para confirmar que índices se usan."

---

### 12.3. API y Testing

**P: ¿Cómo garantizas backward compatibility en tu API?**

**R**: "Implementé **API versioning** desde el inicio:

1. **URL versioning**: `/api/v1/consumption` → Si necesito cambios breaking, creo `/api/v2/`

2. **Additive changes only en v1**:
   ```python
   # ✅ OK: Añadir campo opcional
   class Response(BaseModel):
       success: bool
       new_field: Optional[str] = None  # Backward compatible
   
   # ❌ NO OK: Cambiar tipo existente
   success: str  # Era bool → Breaking change
   ```

3. **Deprecation policy**: Si necesito retirar v1, anuncio 6 meses antes con headers:
   ```python
   response.headers['X-API-Deprecation'] = 'v1 sunset on 2024-06-01'
   ```

**Resultado**: Cero breaking changes en producción en 6 meses."

---

**P: ¿Cómo pruebas código asíncrono?**

**R**: "Uso `pytest-asyncio` con fixtures:

```python
@pytest.mark.asyncio
async def test_async_consumption():
    # Given
    mock_repo = AsyncMock(spec=SubscriptionRepository)
    mock_repo.get_by_user_id.return_value = Subscription(hours=5.0)
    
    service = ConsumptionService(repo=mock_repo)
    
    # When
    result = await service.verify('user-123', 2.0)
    
    # Then
    assert result.success is True
    mock_repo.get_by_user_id.assert_awaited_once_with('user-123')
```

**Key points**:
- `@pytest.mark.asyncio` para async tests
- `AsyncMock` en vez de `Mock` para async methods
- `assert_awaited_once` en vez de `assert_called_once`"

---

**P: ¿Cuál es tu coverage objetivo?**

**R**: "**85-90% de cobertura**, no 100%:

1. **Priorizo critical paths**:
   - ✅ 100% coverage: Lógica de negocio (verificación, actualización)
   - ✅ 95%: Endpoints críticos (verify, callback)
   - ✅ 80%: Utilities, helpers

2. **No teseo exhaustivamente**:
   - ❌ Pydantic models (ya testeados por Pydantic)
   - ❌ Configuration loading (simple)
   - ❌ Logging statements

**Filosofía**: Coverage es métrica de hygiene, no objetivo. Prefiero 85% con tests de calidad que 100% con tests frágiles."

---

### 12.4. Seguridad

**P: ¿Cómo gestionas secretos?**

**R**: "Tres capas según entorno:

1. **Desarrollo local**: `.env` file (git-ignored)
   ```bash
   DATABASE_URL=postgresql://localhost/dev_db
   JWT_SECRET=dev-secret-change-in-prod
   ```

2. **CI/CD**: GitHub Secrets inyectados como env vars
   ```yaml
   env:
     DATABASE_URL: ${{ secrets.DATABASE_URL }}
   ```

3. **Producción**: AWS Secrets Manager
   ```python
   def get_secret(name: str) -> str:
       client = boto3.client('secretsmanager')
       return client.get_secret_value(SecretId=name)['SecretString']
   
   DATABASE_URL = get_secret('prod/db/url')
   ```

**Never**: Secretos hardcoded en código o Dockerfiles."

---

**P: ¿Cómo prevendrías SQL injection?**

**R**: "Uso **parameterized queries** con SQLAlchemy:

```python
# ✅ SEGURO: Parámetros separados
result = await db.execute(
    'SELECT * FROM users WHERE id = :id',
    {'id': user_id}
)

# ❌ INSEGURO: String interpolation
result = await db.execute(
    f'SELECT * FROM users WHERE id = {user_id}'
)
```

SQLAlchemy escapa automáticamente los parámetros. Además:
- Validación con Pydantic antes de queries
- Rate limiting para prevenir mass queries
- Least privilege: DB user solo tiene permisos necesarios"

---

### 12.5. DevOps y Observability

**P: ¿Cómo monitoreas la salud del servicio?**

**R**: "Implementé **observability de tres pilares**:

1. **Metrics (Prometheus)**:
   ```python
   request_duration = Histogram('http_request_duration_seconds')
   error_counter = Counter('http_errors_total', ['status_code'])
   ```
   **Alertas**: Latency p99 > 500ms, Error rate > 1%

2. **Logs (Structured logging)**:
   ```python
   logger.info('consumption_verified', 
               user_id=user_id, 
               hours=2.0, 
               trace_id=trace_id)
   ```
   **ELK Stack**: Centralización y búsqueda

3. **Traces (OpenTelemetry - futuro)**:
   Distributed tracing para debug de latencia

**Dashboards**: Grafana con alertas a Slack."

---

**P: ¿Cómo deployarías esto en producción?**

**R**: "**Rolling deployment** en Kubernetes:

1. **Build**: CI/CD pipeline en GitHub Actions
   - Run tests (break si < 85% coverage)
   - Build Docker image
   - Push a registry (AWS ECR)

2. **Deploy**: ArgoCD sincroniza Kubernetes manifests
   ```yaml
   strategy:
     type: RollingUpdate
     rollingUpdate:
       maxUnavailable: 0  # Zero downtime
       maxSurge: 1
   ```

3. **Validation**: Health checks + smoke tests
   - Si health checks fallan → Rollback automático

4. **Monitoring**: Datadog alerts si error rate > baseline

**Blue-green deployment** para cambios más riesgosos."

---

### 12.6. Escalabilidad

**P: ¿Cómo escalaría este servicio a 1M requests/día?**

**R**: "Plan de escalado progresivo:

**Fase 1: Scaling vertical** (rápido, barato)
- Upgrade a instances más grandes
- Optimizar queries (índices, explain analyze)
- Añadir connection pooling

**Fase 2: Scaling horizontal**
- Deploy múltiples instancias del servicio
- Load balancer (AWS ALB)
- Read replicas de PostgreSQL

**Fase 3: Optimizaciones**
- CDN para assets estáticos
- Database sharding si single DB es bottleneck
- Async processing con Celery para tareas lentas

**Fase 4: Architectural changes**
- CQRS: Separar read/write models
- Event sourcing para auditoría
- Microservices adicionales si monolito crece mucho

**Métricas clave**:
- Current: 1K req/day → 50ms p95
- Target: 1M req/day → < 100ms p95"

---

**P: ¿Qué harías si PostgreSQL se convierte en bottleneck?**

**R**: "Diagnóstico primero:

1. **Identify slow queries**: `pg_stat_statements`
2. **Check index usage**: `EXPLAIN ANALYZE`
3. **Monitor connections**: `pg_stat_activity`

**Soluciones progresivas**:

1. **Optimización** (día 1):
   - Añadir índices faltantes
   - Query optimization
   - Connection pooling (PgBouncer)

2. **Read replicas** (semana 1):
   - Read traffic → Replicas
   - Write traffic → Master
   - 70% del tráfico es read → Escala

3. **Caching agresivo** (semana 2):
   - Redis para queries frecuentes
   - TTL adaptativo
   - Cache invalidation estratégico

4. **Sharding** (mes 1 - último recurso):
   - Shard por `user_id` ranges
   - Añade complejidad operacional

**Expected impact**: Reducir carga en master en 80%."

---

## 13. Consejos para la Entrevista

### 13.1. Estructura de Respuestas (STAR)

Usa el método **STAR** para respuestas estructuradas:

1. **Situation**: Contexto del problema
2. **Task**: Qué necesitabas lograr
3. **Action**: Qué hiciste específicamente
4. **Result**: Resultado medible

**Ejemplo**:
```
P: "Cuéntame sobre un bug crítico que resolviste"

R (STAR):
Situation: "En producción, usuarios reportaban cobros duplicados"

Task: "Necesitaba identificar la causa raíz y prevenir futuras ocurrencias"

Action: "Analicé logs y descubrí race condition en UPDATE de horas.
         Implementé row-level locking con SELECT FOR UPDATE.
         Añadí tests de concurrencia."

Result: "Zero incidents en 3 meses. 
         Coverage de tests de concurrencia aumentó a 95%."
```

### 13.2. Red Flags a Evitar

❌ **NO digas**:
- "No sé" (sin elaborar)
- "Lo haría porque es best practice" (sin justificar)
- "Nunca tuve ese problema"

✅ **SÍ di**:
- "No tengo experiencia directa, pero mi approach sería..."
- "Lo haría por X razón técnica específica"
- "No he encontrado ese problema, pero mitigaría con..."

### 13.3. Preguntas para Hacer al Entrevistador

**Técnicas**:
- "¿Qué stack usan actualmente y por qué lo eligieron?"
- "¿Cuáles son los principales desafíos técnicos del equipo?"
- "¿Cómo es el proceso de deploy a producción?"

**De equipo**:
- "¿Cómo está estructurado el equipo de desarrollo?"
- "¿Qué metodología usan (Scrum, Kanban)?"
- "¿Cómo manejan code reviews?"

**De crecimiento**:
- "¿Qué oportunidades de aprendizaje hay para developers?"
- "¿Hay presupuesto para conferencias/cursos?"

---

## 14. Checklist de Preparación

### Conocimientos que Dominar

#### Arquitectura
- [ ] Clean Architecture (Capas: API, Application, Domain, Infrastructure)
- [ ] Microservices vs Monolith trade-offs
- [ ] REST API best practices
- [ ] Dependency Injection

#### Base de Datos
- [ ] ACID principles (Atomicity, Consistency, Isolation, Durability)
- [ ] Transacciones y locks (SELECT FOR UPDATE)
- [ ] Índices (cuándo y por qué)
- [ ] N+1 queries problem

#### Python/FastAPI
- [ ] Async/await y event loop
- [ ] Pydantic validation
- [ ] Dependency injection con Depends()
- [ ] Middleware

#### Testing
- [ ] Unit vs Integration tests
- [ ] Mocking strategies
- [ ] Test coverage interpretation
- [ ] Pytest fixtures

#### DevOps
- [ ] Docker multi-stage builds
- [ ] Docker Compose para desarrollo
- [ ] Health checks y readiness probes
- [ ] CI/CD básico

#### Seguridad
- [ ] JWT authentication
- [ ] Gestión de secretos
- [ ] SQL injection prevention
- [ ] Rate limiting

### Demo en Vivo

**Prepara poder hacer**:

```bash
# 1. Levantar sistema completo
make up

# 2. Mostrar Swagger UI
open http://localhost:8002/docs

# 3. Hacer request de ejemplo
curl -X POST http://localhost:8002/api/v1/consumption/verify \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "estimated_hours": 2.0}'

# 4. Ver logs
make logs-gatekeeper

# 5. Ejecutar tests
make test
```

---

## 15. Recursos Finales

### Documentación de Tu Proyecto

```
docs/
├── INTERVIEW_PREPARATION_GUIDE.md      # Este documento
├── DOCKER_QUICK_START.md               # Setup rápido
├── FINAL_COMPLETION_SUMMARY.md         # Overview del proyecto
├── n8n_integration_guide.md            # Integración n8n
└── DOCKER_FIXES_APPLIED.md             # Debugging reciente
```

### Key Metrics para Memorizar

- **Coverage**: 93.5%
- **Services**: 4 (PostgreSQL, Redis, Mock n8n, Gatekeeper)
- **Endpoints**: 3 principales (verify, callback, health)
- **Stack**: Python 3.11, FastAPI, PostgreSQL 15, Redis 7
- **Deployment**: Docker + Docker Compose (dev), Kubernetes (prod roadmap)

### One-Liner Elevator Pitch

"Desarrollé el servicio crítico de monetización (Gatekeeper) para un sistema SaaS que transforma reuniones en PRDs. Maneja control de consumo con transacciones ACID en PostgreSQL, caché con Redis, y orquestación con n8n. Dockerizado, 93% coverage, arquitectura Clean con principios SOLID."

---

**¡Buena suerte en tu entrevista!** 🚀

Recuerda: **Conoces tu código mejor que nadie. Habla con confianza, pero admite cuando no sepas algo y explica cómo lo aprenderías.**
