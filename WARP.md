# Proyecto Warp: Principios de Arquitectura y Buenas Prácticas y Metodología TDD

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Contexto del Proyecto

[INICIO CONTEXTO DEL PROYECTO]
**M2PRD-001: Meet-Teams-to-PRD** es un sistema distribuido Python/JavaScript que transforma grabaciones de audio de reuniones en documentos PRD estructurados y tareas asignadas automáticamente. Utiliza una arquitectura de microservicios con orquestación centralizada (n8n/Make), procesamiento IA/NLP (Python), persistencia políglota (PostgreSQL/Redis/MongoDB) y despliegue híbrido (Serverless/Contenedores).

**Stack principal**: Python 3.11+, JavaScript/TypeScript, PostgreSQL, Redis, MongoDB, n8n/Make, AWS Lambda, Docker/Kubernetes.
**Dependencias clave**: FastAPI, SQLAlchemy, spaCy, OpenAI, Deepgram SDK, pytest, black, mypy.
[FIN CONTEXTO DEL PROYECTO]

---

## 1. Stack Tecnológico Definitivo y Justificación

### 1.1. Arquitectura de Capas del Sistema M2PRD-001

**El sistema M2PRD-001 adopta una arquitectura de microservicios híbrida que separa responsabilidades en capas especializadas**, cada una optimizada para sus requisitos específicos de rendimiento, escalabilidad y mantenibilidad.

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (Portal Web - RF6.0, RF7.0)                   │
│ React/Vue.js + Authentication + Subscription Management │
├─────────────────────────────────────────────────────────┤
│ Backend (API SaaS - RF8.0)                             │
│ Node.js/Python + Express/FastAPI + Business Logic      │
├─────────────────────────────────────────────────────────┤
│ Orquestación Central (RF1.0-RF5.0, RNF5.0)            │
│ n8n/Make + Workflow Management + Retry Logic           │
├─────────────────────────────────────────────────────────┤
│ Módulo IA/NLP (RF3.0, RF4.0)                          │
│ Python Serverless + spaCy/OpenAI + Text Processing     │
├─────────────────────────────────────────────────────────┤
│ Persistencia de Datos (RF8.0 - Crítico de Negocio)   │
│ PostgreSQL (ACID) + Redis (Cache) + Stripe Integration │
└─────────────────────────────────────────────────────────┘
```

### 1.2. Decisiones de Stack por Componente

#### **Frontend (Portal Web - RF6.0, RF7.0)**
**Stack:** React.js (o Vue.js como alternativa)

**Justificación Técnica:**
- **RF6.0 (Autenticación)**: Componentes reutilizables para formularios de login/registro y gestión de sesiones
- **RF7.0 (Gestión de Suscripciones)**: Interfaces dinámicas para planes, facturación y control de consumo
- **Principios SOLID**: Arquitectura de componentes que aplica SRP (Single Responsibility Principle) - cada componente tiene una responsabilidad específica
- **Clean Architecture**: Separación clara entre presentación y lógica de negocio mediante hooks/composables

```javascript path=null start=null
// ✅ Ejemplo de componente React aplicando SRP
function SubscriptionPlanCard({ plan, onSelect }) {
  // Una sola responsabilidad: mostrar un plan de suscripción
  return (
    <div className="plan-card">
      <h3>{plan.name}</h3>
      <p>Horas incluidas: {plan.hours}</p>
      <p>Precio: ${plan.price}/mes</p>
      <button onClick={() => onSelect(plan)}>Seleccionar Plan</button>
    </div>
  );
}
```

#### **Backend (API de Monetización - RF8.0)**
**Stack:** Node.js con Express (o Python con FastAPI como alternativa)

**Justificación Técnica:**
- **RF8.0 (Control de Consumo)**: Manejo eficiente de I/O para múltiples conexiones concurrentes con servicios externos
- **RF6.0 (Autenticación)**: Middleware robusto para JWT y gestión de sesiones
- **Principios ACID**: Integración nativa con PostgreSQL para transacciones críticas de facturación
- **Clean Architecture**: API REST que implementa Dependency Inversion Principle (DIP)

```javascript path=null start=null
// ✅ Ejemplo de API aplicando DIP y Clean Architecture
class SubscriptionController {
  constructor(subscriptionService, paymentGateway) {
    this.subscriptionService = subscriptionService; // ✅ DIP
    this.paymentGateway = paymentGateway; // ✅ DIP
  }
  
  async createSubscription(req, res) {
    // ✅ Clean Architecture - Controller delega a Use Case
    const result = await this.subscriptionService.createSubscription(
      req.body, 
      req.user.id
    );
    res.json(result);
  }
}
```

#### **Persistencia de Datos (Crítico de Negocio - RF8.0)**
**Stack:** PostgreSQL (Principal) + Redis (Cache)

**Justificación Crítica:**
- **Prioridad 10/10**: Los datos financieros y de consumo requieren garantías ACID absolutas
- **RF7.0 (Suscripciones)**: Transacciones atómicas para facturación y cambios de plan
- **RF8.0 (Control de Consumo)**: Consistencia crítica para límites de horas y facturación
- **Principios ACID**: PostgreSQL garantiza Atomicidad, Consistencia, Aislamiento y Durabilidad
- **Performance**: Redis como cache para consultas frecuentes de límites de consumo

```sql path=null start=null
-- ✅ Ejemplo de transacción ACID para consumo de horas
BEGIN TRANSACTION;

-- Verificar límite disponible
SELECT available_hours FROM user_subscriptions 
WHERE user_id = $1 AND status = 'active';

-- Decrementar horas si hay disponibles
UPDATE user_subscriptions 
SET available_hours = available_hours - $2,
    last_updated = NOW()
WHERE user_id = $1 AND available_hours >= $2;

-- Registrar el consumo
INSERT INTO usage_logs (user_id, hours_consumed, meeting_id, timestamp)
VALUES ($1, $2, $3, NOW());

COMMIT; -- ✅ Todo o nada (Atomicidad)
```

#### **Módulo IA/NLP (RF3.0, RF4.0)**
**Stack:** Python Serverless (AWS Lambda/Google Cloud Functions)

**Justificación Técnica:**
- **RF3.0 (Generación de PRD)**: Ecosistema Python robusto para NLP (spaCy, NLTK, transformers)
- **RF4.0 (Asignación Inteligente)**: Bibliotecas de ML maduras para clasificación de requisitos
- **Serverless**: Escalado automático y costo-eficiencia para procesamiento bajo demanda
- **Clean Architecture**: Módulo independiente que implementa Strategy Pattern

```python path=null start=null
# ✅ Ejemplo de Strategy Pattern para extracción de requisitos
from abc import ABC, abstractmethod

class RequirementExtractionStrategy(ABC):
    @abstractmethod
    def extract_requirements(self, transcription: str) -> List[Requirement]:
        pass

class OpenAIExtractionStrategy(RequirementExtractionStrategy):
    """✅ Strategy específica usando OpenAI GPT"""
    
    def extract_requirements(self, transcription: str) -> List[Requirement]:
        # Procesamiento con OpenAI API
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system", 
                "content": "Extract functional and non-functional requirements"
            }]
        )
        return self._parse_requirements(response)

# ✅ Context que usa la estrategia (Strategy Pattern)
class RequirementProcessor:
    def __init__(self, strategy: RequirementExtractionStrategy):
        self.strategy = strategy  # ✅ DIP - Depende de abstracción
    
    def process_meeting(self, transcription: str) -> ProcessedPRD:
        requirements = self.strategy.extract_requirements(transcription)
        return self._generate_prd(requirements)
```

#### **Orquestación Central (RF1.0-RF5.0, RNF5.0)**
**Stack:** n8n/Make (Decisión Arquitectónica Fija)

**Justificación Estratégica:**
- **Prioridad 10/10**: Definido como componente central inamovible
- **RNF5.0 (Tolerancia a Fallos)**: Gestión declarativa de reintentos y recuperación
- **RF1.0-RF5.0**: Orquestación visual de todo el flujo de procesamiento
- **Clean Architecture**: Actúa como Application Service coordinando Use Cases
- **Observability**: Monitoreo visual del estado de cada paso del workflow

#### **Infraestructura y Pasarelas de Pago**
**Stack:** Docker + Docker Compose (Desarrollo) + AWS/GCP + Stripe + Kubernetes (Producción)

**Justificación de Despliegue y Desarrollo:**
- **Docker/Docker Compose:** Contenerización completa para desarrollo local uniforme y reproducible
- **Stripe:** Estándar de industria para RF7.0 (facturación recurrente) y gestión de planes SaaS
- **Serverless:** Módulo IA/NLP con escalado automático y costo optimizado
- **Kubernetes:** Orquestación de contenedores en producción con alta disponibilidad
- **Clean Architecture:** Infraestructura como detalle de implementación, no afecta lógica de negocio

### 1.3. Mapeo de Stack a Principios Arquitectónicos

| Principio/Patrón | Componente de Stack | Implementación |
|------------------|--------------------|-----------------|
| **ACID (Atomicity, Consistency, Isolation, Durability)** | PostgreSQL | Transacciones críticas para facturación y consumo |
| **SRP (Single Responsibility)** | React Components + Microservicios | Cada componente/servicio tiene una responsabilidad específica |
| **DIP (Dependency Inversion)** | Node.js/Python APIs | Inyección de dependencias y uso de abstracciones |
| **Strategy Pattern** | Python IA/NLP | Algoritmos de extracción intercambiables (OpenAI, spaCy) |
| **Circuit Breaker** | n8n/Make + Redis | Tolerancia a fallos en servicios externos |
| **Clean Architecture** | Separación por Capas | Frontend→Backend→Domain→Infrastructure |
| **Factory Pattern** | Microservicios | Creación de servicios especializados por dominio |

### 1.4. Consideraciones de Seguridad y RNF2.0

**Gestión de Secretos:**
- **Stripe API Keys**: AWS Secrets Manager/Google Secret Manager
- **Database Credentials**: Rotación automática cada 30 días
- **JWT Secrets**: Almacenamiento seguro con expiración configurada
- **API Keys Externos**: Deepgram, OpenAI keys en gestores de secretos dedicados

**Cumplimiento GDPR/SOC2:**
- **Logs estructurados**: Sin datos sensibles en logs (PII masking)
- **Cifrado en tránsito**: HTTPS/TLS 1.3 en todas las comunicaciones
- **Cifrado en reposo**: PostgreSQL con cifrado a nivel de disco
- **Auditoría**: Trazabilidad completa de transacciones financieras

---

## 2. Arquitectura de Microservicios: Modelo SaaS (V1.4)

### 2.1. Análisis de Componentes Centrales y Separación de Responsabilidades

**La transición al modelo SaaS (V1.4) redefine la arquitectura al centralizar la lógica de negocio y monetización en un Backend de Servicios dedicado.** Esta evolución arquitectónica implementa una **separación crítica de responsabilidades** que alinea perfectamente con los principios SOLID establecidos en este documento.

#### **Evolución Arquitectónica: De Orquestador Monolítico a Microservicios Especializados**

Anteriormente, el Workflow (n8n/Make) actuaba como orquestador y gatekeeper simultáneamente, violando el **Principio de Responsabilidad Única (SRP)**. La nueva arquitectura SaaS V1.4 **redistribuye estas responsabilidades**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANTES: Workflow Monolítico                  │
│  ❌ Orquestación + Gatekeeper + Control de Consumo + Negocio   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│               AHORA: Microservicios Especializados              │
│  ✅ Servicio de Consumo (Gatekeeper) + Workflow (Orquestador)  │
└─────────────────────────────────────────────────────────────────┘
```

#### **Componentes Redefinidos según SOLID**

**1. Portal Web Frontend (RF7.0 - Gestión de Suscripciones)**
- **Responsabilidad Única**: Capa de presentación para gestión de cuentas y planes
- **Principio OCP**: Extensible para nuevos planes sin modificar código base
- **Interface Segregation**: Interfaces específicas para autenticación vs. facturación

**2. Servicio de Autenticación/Usuarios (RF6.0)**
- **Responsabilidad Única**: Validación de identidad y gestión de sesiones
- **Dependency Inversion**: Depende de abstracciones de autenticación (JWT, OAuth)
- **Integración ACID**: Transacciones seguras para datos de usuario

**3. Servicio de Suscripciones/Consumo - EL NUEVO GATEKEEPER (RF8.0)**
- **Responsabilidad Crítica**: Implementa la lógica de monetización y control de acceso
- **Single Responsibility**: **SOLO** maneja verificación y actualización de consumo
- **ACID Compliance**: Utiliza transacciones PostgreSQL para operaciones financieras críticas
- **Circuit Breaker**: Implementa tolerancia a fallos para operaciones de facturación

**4. Workflow (n8n/Make) - ORQUESTADOR PURO**
- **Responsabilidad Redefinida**: **SOLO** orquestación técnica de procesamiento
- **Dependency Inversion**: Depende del Servicio de Consumo para autorización
- **Open/Closed**: Abierto para nuevos pasos de procesamiento, cerrado para lógica de negocio

### 2.2. Diagramas UML del Modelo SaaS (V1.4)

#### **2.2.1. Diagrama de Casos de Uso - Gestión de Suscripciones y Procesamiento**

```mermaid
%% UML: Diagrama de Casos de Uso (Use Case Diagram) - SaaS Update
graph TD
    subgraph system_boundary [Límite del Sistema: Plataforma M2PRD-001 SaaS]
        subgraph Modulo_Suscripciones [Gestión de Cuenta y Suscripciones]
            UC_Reg(Registrar/Autenticar Usuario)
            UC_Sub(Gestionar Plan de Suscripción - RF7.0)
            UC_Pay(Procesar Pago - Pasarela)
            UC_Reg --> UC_Sub
            UC_Sub --> UC_Pay
        end
        
        subgraph Modulo_Procesamiento [Flujo de Generación de PRD]
            UC_Verif(Verificar Consumo Disponible - RF8.0)
            UC_Proc(Generar y Asignar Requisitos)
            UC_Upd(Actualizar Registro de Consumo)
            UC_Proc -.-> UC_Verif: Consumo es pre-requisito
            UC_Upd -.-> UC_Proc: Se actualiza post-procesamiento
        end
        
        actor_pm[Jefe de Producto/Suscriptor] 
        actor_sysb[Sistema de Facturación/Pasarela]
        
        actor_pm --> UC_Reg
        actor_pm --> UC_Sub
        
        UC_Verif --> actor_sysb
        UC_Pay --> actor_sysb
        
        UC_Proc --> actor_pm
    end
```

#### **2.2.2. Diagrama de Clases - Modelo de Datos SaaS**

```mermaid
%% UML: Diagrama de Clases (Class Diagram) - SaaS Update (Monetización Focus)
classDiagram
    direction LR
    
    class Usuario {
        +id_usuario: string
        -email: string
        -password_hash: string
        +autenticar(token): bool
        +validarSesion(): bool
    }
    
    class PlanDeSuscripcion {
        +id_plan: string
        +nombre: string
        -limite_horas_mensual: float
        -precio_mensual: float
        +getLimite(): float
        +calcularCosto(): float
    }
    
    class RegistroDeConsumo {
        +id_registro: string
        -horas_consumidas: float
        -fecha_registro: datetime
        -meeting_id: string
        +verificarDisponibilidad(id_usuario): bool
        +actualizarConsumo(horas_usadas): void
        +obtenerConsumoMensual(): float
    }

    class Reunion {
        -id_reunion: string
        -url_audio: string
        -duracion_minutos: int
        -estado: string
        +calcularHorasConsumidas(): float
    }
    
    class Transaccion {
        +id_transaccion: string
        +estado: TransactionStatus
        -monto: float
        -stripe_payment_id: string
        +procesarPago(): bool
        +validarPago(): bool
    }
    
    class TransactionStatus {
        <<enumeration>>
        PAGADO
        PENDIENTE
        FALLIDO
        REEMBOLSADO
    }
    
    %% Relaciones con cardinalidad específica:
    
    %% Composición (Rombo relleno) - Fuerte dependencia existencial
    Usuario "1" *-- "1" PlanDeSuscripcion: tiene
    
    %% Agregación (Rombo hueco) - Dependencia lógica/funcional
    Usuario "1" o-- "*" RegistroDeConsumo: registra
    PlanDeSuscripcion "1" o-- "1..*" Transaccion: genera
    RegistroDeConsumo "1" o-- "1" Reunion: asociadoA
    
    %% Asociación
    Usuario "1" -- "0..*" Reunion: organiza
    Transaccion "1" -- "1" TransactionStatus: tiene
```

#### **2.2.3. Diagrama de Secuencia - Flujo Completo SaaS con Control de Consumo**

```mermaid
%% UML: Diagrama de Secuencia (Sequence Diagram) - SaaS Update
sequenceDiagram
    actor PM as Jefe de Producto
    participant Extension as Chrome Extension
    participant AuthSrv as Servicio Auth/Users
    participant ConsumoSrv as Servicio Suscripciones/Consumo
    participant Workflow as n8n/Make Workflow
    participant Deepgram as Deepgram API
    participant ModuloIA as Módulo IA/NLP
    participant Database as PostgreSQL
    
    title Flujo M2PRD-001 SaaS: Verificación de Consumo (RF8.0) y Orquestación

    PM->>Extension: 1. Click 'Iniciar Proceso' (RF1.0)
    activate Extension
    Extension->>AuthSrv: 2. POST /api/auth/validate (token, meeting_url)
    deactivate Extension
    
    activate AuthSrv
    AuthSrv->>Database: 2.1. Validar JWT y sesión
    Database-->>AuthSrv: Usuario válido
    AuthSrv->>ConsumoSrv: 3. POST /api/consumo/verificar (user_id, estimated_hours)
    deactivate AuthSrv
    
    activate ConsumoSrv
    note right of ConsumoSrv: 🔒 GATEKEEPER - Lógica de Monetización (RF6.0, RF8.0)
    ConsumoSrv->>Database: 4. BEGIN TRANSACTION; SELECT available_hours
    Database-->>ConsumoSrv: Horas disponibles: X
    
    alt Consumo OK (Horas Disponibles >= Estimadas)
        ConsumoSrv->>Workflow: 5. POST /webhook/trigger (meeting_data, user_id)
        note right of ConsumoSrv: ✅ Autorización concedida
        deactivate ConsumoSrv
        
        activate Workflow
        note right of Workflow: 🔄 ORQUESTADOR PURO - Solo procesamiento técnico
        Workflow->>Deepgram: 6. Transcribir audio (RF2.0)
        activate Deepgram
        Deepgram-->>Workflow: 7. Transcripción completada
        deactivate Deepgram
        
        Workflow->>ModuloIA: 8. Procesar transcripción (RF3.0, RF4.0)
        activate ModuloIA
        ModuloIA-->>Workflow: 9. PRD y tareas generadas
        deactivate ModuloIA
        
        Workflow->>ConsumoSrv: 10. PUT /api/consumo/actualizar (user_id, horas_reales)
        
        activate ConsumoSrv
        ConsumoSrv->>Database: 10.1. UPDATE user_subscriptions SET available_hours -= horas_reales
        ConsumoSrv->>Database: 10.2. INSERT INTO usage_logs; COMMIT;
        Database-->>ConsumoSrv: Consumo actualizado
        ConsumoSrv-->>Workflow: 11. Consumo registrado exitosamente
        deactivate ConsumoSrv
        
        Workflow->>PM: 12. 📧 Notificación: PRD y tareas listas
        deactivate Workflow
        
    else Consumo Excedido (Horas Insuficientes)
        ConsumoSrv->>Database: ROLLBACK; -- No se procesa
        ConsumoSrv-->>PM: 5. ❌ Error: Límite de horas excedido (RF8.0)
        note left of PM: Redirección a RF7.0: Gestionar Plan
        deactivate ConsumoSrv
    end
```

### 2.3. Impacto en Principios Arquitectónicos Existentes

#### **2.3.1. Refuerzo de Principios SOLID**

**Single Responsibility Principle (SRP)** ✅ **MEJORADO**
- **Antes**: Workflow manejaba orquestación + monetización + control de acceso
- **Ahora**: Cada microservicio tiene una responsabilidad específica y bien definida

**Open/Closed Principle (OCP)** ✅ **APLICADO**
- Servicio de Consumo es **cerrado para modificación** en lógica de facturación
- **Abierto para extensión** mediante nuevos planes y métodos de pago (Stripe)

**Dependency Inversion Principle (DIP)** ✅ **REFORZADO**
- Workflow ahora **depende de la abstracción** del Servicio de Consumo
- No conoce detalles de implementación de la lógica de facturación

#### **2.3.2. Fortalecimiento de Principios ACID**

El nuevo **Servicio de Suscripciones/Consumo** implementa transacciones críticas que **requieren garantías ACID absolutas**:

```sql path=null start=null
-- ✅ ACID Transaction para RF8.0 - Control de Consumo
BEGIN TRANSACTION; -- 🔒 Atomicidad

-- Verificar disponibilidad (Consistency)
SELECT available_hours, plan_id 
FROM user_subscriptions 
WHERE user_id = $1 AND status = 'active' 
FOR UPDATE; -- 🔒 Isolation (Row-level locking)

-- Validar business rules (Consistency)
IF available_hours < estimated_hours THEN
    ROLLBACK; -- ❌ Atomicidad - Todo o nada
    RAISE EXCEPTION 'Insufficient hours available';
END IF;

-- Actualizar consumo (Durability)
UPDATE user_subscriptions 
SET available_hours = available_hours - actual_hours,
    last_usage = NOW()
WHERE user_id = $1;

-- Registrar auditoría (Durability + Compliance)
INSERT INTO usage_audit_log 
(user_id, hours_consumed, meeting_id, transaction_timestamp)
VALUES ($1, $2, $3, NOW());

COMMIT; -- ✅ Durabilidad - Cambios persisten
```

#### **2.3.3. Integración con Metodología TDD**

**El nuevo diseño SaaS mantiene y refuerza la metodología TDD** establecida en este documento:

```python path=null start=null
# ✅ TDD para el nuevo Servicio de Consumo
class TestConsumoService:
    """TDD para RF8.0 - Control de Consumo SaaS."""
    
    def test_should_allow_processing_when_hours_available(self):
        """RED: Test que define el comportamiento de autorización."""
        # Given
        consumo_service = ConsumoService(database_manager=Mock())
        user_id = "user-123"
        estimated_hours = 2.0
        
        # Mock: Usuario con 5 horas disponibles
        consumo_service.database_manager.get_available_hours.return_value = 5.0
        
        # When
        authorization = consumo_service.verificar_consumo_disponible(user_id, estimated_hours)
        
        # Then
        assert authorization.authorized is True
        assert authorization.remaining_hours == 3.0
    
    def test_should_reject_processing_when_insufficient_hours(self):
        """RED: Test para rechazo por límite excedido."""
        # Given
        consumo_service = ConsumoService(database_manager=Mock())
        user_id = "user-456" 
        estimated_hours = 10.0
        
        # Mock: Usuario con solo 2 horas disponibles
        consumo_service.database_manager.get_available_hours.return_value = 2.0
        
        # When & Then
        with pytest.raises(InsufficientHoursException) as exc_info:
            consumo_service.verificar_consumo_disponible(user_id, estimated_hours)
        
        assert "insufficient hours" in str(exc_info.value).lower()
    
    def test_should_update_consumption_atomically_after_processing(self):
        """RED: Test para actualización ACID del consumo."""
        # Given
        consumo_service = ConsumoService(database_manager=Mock())
        user_id = "user-789"
        actual_hours_consumed = 1.5
        
        # When
        result = consumo_service.actualizar_consumo(user_id, actual_hours_consumed)
        
        # Then - Verificar transacción ACID
        assert result.success is True
        consumo_service.database_manager.execute_transaction.assert_called_once()
        # Verificar que se llama con UPDATE + INSERT (consumo + auditoría)
        assert consumo_service.database_manager.execute_transaction.call_args[0][0].startswith('BEGIN')
```

#### **2.3.4. Circuit Breaker Pattern para Servicios SaaS**

La arquitectura SaaS implementa **Circuit Breaker específicamente para operaciones críticas de facturación**:

```python path=null start=null
# ✅ Circuit Breaker para operaciones de facturación críticas
class SaaSPaymentCircuitBreaker(CircuitBreaker):
    """Circuit Breaker especializado para operaciones SaaS críticas."""
    
    def __init__(self):
        super().__init__(
            failure_threshold=2,  # Baja tolerancia para operaciones financieras
            timeout=30,           # Recovery rápido para mejor UX
            expected_exception=(PaymentGatewayException, DatabaseException)
        )
    
    def call_payment_operation(self, operation: Callable) -> PaymentResult:
        """Protege operaciones de pago críticas."""
        try:
            return self.call(operation)
        except CircuitBreakerOpenException:
            # Fallback a modo offline o notificación al admin
            raise PaymentServiceUnavailableException(
                "Payment service temporarily unavailable. Please try again in a few minutes."
            )
```

---

## 3. Entorno de Desarrollo Local: Contenerización con Docker

### 3.1. Justificación Técnica: Docker como Habilitador de Principios Arquitectónicos

**La contenerización del ecosistema SaaS M2PRD-001 no es solo una decisión de infraestructura**, sino una **implementación directa de los principios SOLID y Clean Architecture** establecidos en este documento.

#### **3.1.1. Alineación Docker ↔️ Principios SOLID**

**Single Responsibility Principle (SRP) + Aislamiento de Contenedores**
```
┌──────────────────────────────────────────────────────────────┐
│                    SRP + DOCKER: 1 Servicio = 1 Contenedor                 │
│  ✅ Servicio Consumo (Container) • Servicio Auth (Container)           │
│  ✅ PostgreSQL (Container) • Redis (Container) • Frontend (Container)    │
└──────────────────────────────────────────────────────────────┘
```

**Dependency Inversion Principle (DIP) + Docker Networks**
- **Abstracción**: Los servicios se comunican a través de nombres de servicio Docker, no IPs hardcodeadas
- **Intercambiabilidad**: Un contenedor PostgreSQL puede ser reemplazado por MySQL sin cambiar el código
- **Testabilidad**: Contenedores de test pueden usar bases de datos en memoria o mocks

**Open/Closed Principle (OCP) + Docker Compose**
- **Cerrado para modificación**: La configuración base del `docker-compose.yml` no cambia
- **Abierto para extensión**: Nuevos servicios se añaden como contenedores adicionales

#### **3.1.2. Principio KISS (Keep It Simple, Stupid) + Docker Compose**

**Antes de Docker: Configuración Manual Compleja**
```bash
# ❌ Configuración manual propensa a errores
1. Instalar Node.js v18.x
2. Instalar Python 3.11 + pip
3. Configurar PostgreSQL + crear DB
4. Instalar Redis
5. Configurar variables de entorno
6. Instalar dependencias frontend
7. Instalar dependencias backend
8. Configurar n8n/Make localmente
9. Configurar certificados SSL
10. Sincronizar versiones entre desarrolladores
```

**Después de Docker: Un Solo Comando**
```bash
# ✅ KISS - Simplicidad máxima
docker-compose up --build
```

### 3.2. Arquitectura de Contenedores del Sistema SaaS

#### **3.2.1. Mapeo de Componentes SaaS a Contenedores Docker**

```yaml path=null start=null
# docker-compose.yml - Arquitectura Contenerizada M2PRD-001
version: '3.8'

services:
  # 📱 Frontend - Portal Web SaaS (RF7.0)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:8000
      - REACT_APP_AUTH_URL=http://auth-service:8001
    depends_on:
      - backend
      - auth-service
    networks:
      - saas-network

  # 🔐 Servicio de Autenticación (RF6.0)
  auth-service:
    build: ./auth-service
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/auth_db
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - saas-network

  # 💰 Servicio de Suscripciones/Consumo - GATEKEEPER (RF8.0)
  consumption-service:
    build: ./consumption-service
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/consumption_db
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - saas-network

  # 🔄 Backend Principal - Lógica de Negocio
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/main_db
      - CONSUMPTION_SERVICE_URL=http://consumption-service:8002
      - N8N_WEBHOOK_URL=http://n8n:5678
    depends_on:
      - postgres
      - consumption-service
    networks:
      - saas-network

  # 🤖 Módulo IA/NLP (RF3.0, RF4.0)
  ai-nlp-service:
    build: ./ai-nlp-service
    ports:
      - "8003:8003"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
    networks:
      - saas-network

  # 📊 Orquestación n8n (RF1.0-RF5.0)
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n_db
      - DB_POSTGRESDB_USER=user
      - DB_POSTGRESDB_PASSWORD=pass
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
    networks:
      - saas-network

  # 💾 PostgreSQL - ACID Database (Crítico)
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_MULTIPLE_DATABASES=auth_db,consumption_db,main_db,n8n_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-databases.sh:/docker-entrypoint-initdb.d/init-databases.sh
    ports:
      - "5432:5432"
    networks:
      - saas-network

  # ⚡ Redis - Cache y Sesión Store
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - saas-network

volumes:
  postgres_data:
  redis_data:
  n8n_data:

networks:
  saas-network:
    driver: bridge
```

#### **3.2.2. Beneficios de la Contenerización por Principio Arquitectónico**

| Principio Arquitectónico | Beneficio Docker | Implementación Concreta |
|---------------------------|------------------|-------------------------|
| **SRP** | Aislamiento de responsabilidades | 1 servicio = 1 contenedor |
| **DIP** | Abstracción de dependencias | Service names en vez de IPs |
| **ACID** | Persistencia garantizada | Volumes para PostgreSQL |
| **KISS** | Simplicidad operativa | `docker-compose up --build` |
| **Circuit Breaker** | Aislamiento de fallos | Contenedores independientes |
| **Clean Architecture** | Separación de capas | Redes Docker separadas |

### 3.3. Comandos de Desarrollo y Operación

#### **3.3.1. Comandos Esenciales para Desarrolladores**

```bash path=null start=null
# ✅ COMANDO PRINCIPAL - Levantar entorno completo
docker-compose up --build

# 🔄 Reconstruir servicios específicos
docker-compose build frontend backend

# 📊 Ver logs de servicios específicos
docker-compose logs -f consumption-service

# 🔧 Ejecutar comandos dentro de contenedores
docker-compose exec backend python manage.py migrate
docker-compose exec postgres psql -U user -d consumption_db

# 🧪 Limpiar entorno (desarrollo)
docker-compose down -v  # Elimina contenedores y volúmenes
docker system prune -a  # Limpieza completa

# 📊 Monitoreo del sistema
docker-compose ps      # Estado de servicios
docker-compose top     # Procesos en ejecución
```

#### **3.3.2. Flujo de Desarrollo con TDD + Docker**

```bash path=null start=null
# 1. 🏃‍♂️ Iniciar entorno de desarrollo
docker-compose up --build

# 2. ⚡ Ejecutar tests TDD en contenedores
docker-compose exec backend pytest tests/ -v
docker-compose exec frontend npm test

# 3. 🔄 Hot-reload automático (desarrollo)
# Los cambios en código se reflejan automáticamente
# mediante volumes montados

# 4. 🔍 Debug de servicios
docker-compose exec consumption-service python -m pdb app.py
```

### 3.4. Configuración de Variables de Entorno y Secretos

#### **3.4.1. Archivo .env para Desarrollo Local**

```bash path=null start=null
# .env - Variables de entorno locales
# 🔒 Secretos de desarrollo (NO usar en producción)
JWT_SECRET=dev-jwt-secret-key-change-in-production
STRIPE_SECRET_KEY=sk_test_your_stripe_test_key_here
OPENAI_API_KEY=your-openai-api-key
DEEPGRAM_API_KEY=your-deepgram-api-key

# 💾 Database
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=memorymeet_dev

# ⚡ Redis
REDIS_PASSWORD=dev-redis-password

# 🌍 URLs de servicios
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
AUTH_SERVICE_URL=http://localhost:8001
CONSUMPTION_SERVICE_URL=http://localhost:8002
```

#### **3.4.2. Configuración de Seguridad Local vs. Producción**

**Desarrollo Local (Docker Compose)**
- Secretos en archivo `.env` (Git-ignored)
- Certificados autofirmados
- Debug mode habilitado
- Bases de datos sin cifrado

**Producción (Kubernetes + AWS/GCP)**
- AWS Secrets Manager / Google Secret Manager
- Certificados válidos (Let's Encrypt)
- Debug mode deshabilitado
- Cifrado en tránsito y reposo

### 3.5. Integración con Principios de Testing (TDD)

#### **3.5.1. Contenedores Especializados para Testing**

```yaml path=null start=null
# docker-compose.test.yml - Entorno de testing aislado
version: '3.8'

services:
  # 🧪 Base de datos de test (en memoria)
  postgres-test:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=test_db
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
    tmpfs:
      - /var/lib/postgresql/data  # Base de datos en memoria (rápido)

  # 📊 Test runner para backend
  backend-test:
    build:
      context: ./backend
      target: test  # Multi-stage build
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@postgres-test:5432/test_db
      - TESTING=true
    depends_on:
      - postgres-test
    command: pytest tests/ -v --cov=app --cov-report=html

  # ⚡ Test runner para frontend
  frontend-test:
    build:
      context: ./frontend
      target: test
    environment:
      - CI=true
    command: npm test -- --coverage --watchAll=false
```

**Comando para ejecutar suite completa de tests:**
```bash path=null start=null
# ✅ TDD con Docker - Suite completa
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 3.6. Monitoreo y Observabilidad en Contenedores

#### **3.6.1. Logging Estructurado y Métricas**

```yaml path=null start=null
# Extensión para observabilidad local
services:
  # 📊 Prometheus - Métricas
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - saas-network

  # 📈 Grafana - Dashboards
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - saas-network
```

### 3.7. Onboarding de Desarrolladores: Guía de Inicio Rápido

#### **3.7.1. Setup Inicial - Menos de 5 Minutos**

```bash path=null start=null
# 🏃‍♂️ ONBOARDING COMPLETO M2PRD-001 SaaS

# 1. Clonar repositorio
git clone https://github.com/your-org/m2prd-001-saas.git
cd m2prd-001-saas

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. ✅ COMANDO MÁGICO - Un solo comando para todo
docker-compose up --build

# 4. Verificar que todo funciona
# 📱 Frontend: http://localhost:3000
# 🔐 API Auth: http://localhost:8001/health
# 💰 API Consumo: http://localhost:8002/health  
# 🔄 Backend: http://localhost:8000/health
# 📊 n8n: http://localhost:5678
```

#### **3.7.2. Checklist de Verificación Post-Setup**

- [ ] **Servicios activos**: `docker-compose ps` muestra todos los servicios "Up"
- [ ] **Base de datos**: PostgreSQL acepta conexiones en puerto 5432
- [ ] **Cache**: Redis responde en puerto 6379
- [ ] **APIs**: Endpoints `/health` responden con status 200
- [ ] **Frontend**: Aplicación React carga en http://localhost:3000
- [ ] **Orquestación**: n8n accesible en http://localhost:5678
- [ ] **Tests pasan**: `docker-compose -f docker-compose.test.yml up`

---

## 4. Metodología de Desarrollo: TDD (Test-Driven Development)

### 1.1. Fundamentos del Ciclo TDD

**TDD es el pilar fundamental del desarrollo en M2PRD-001.** Cada funcionalidad debe seguir estrictamente el ciclo **Rojo-Verde-Refactorización**:

```
🔴 RED (Rojo)    → Escribir un test que falle
🟢 GREEN (Verde) → Escribir código mínimo para pasar el test  
🔵 REFACTOR      → Mejorar el código manteniendo los tests pasando
```

### 1.2. Implementación del Ciclo TDD en M2PRD-001

#### **Paso 1: RED - Test que Falla**
```python path=null start=null
# ✅ TDD RED - Comenzamos con el test que define el comportamiento esperado
import pytest
from unittest.mock import Mock
from meeting_processor import MeetingProcessor, ProcessingResult
from exceptions import InvalidMeetingUrlException

class TestMeetingProcessor:
    """✅ TDD - Test First: Definimos comportamiento antes de implementar."""
    
    def test_should_process_google_meet_url_successfully(self):
        """RED: Test que falla inicialmente - define el comportamiento."""
        # Given
        meeting_processor = MeetingProcessor(
            transcription_service=Mock(),
            prd_generator=Mock(),
            task_assigner=Mock()
        )
        meeting_url = "https://meet.google.com/abc-defg-hij"
        
        # When
        result = meeting_processor.process_meeting(meeting_url)
        
        # Then - Define el comportamiento esperado
        assert result.success is True
        assert result.prd is not None
        assert result.processing_time_seconds < 300  # RNF1.0: < 5 minutos
        assert len(result.tasks) > 0
    
    def test_should_reject_invalid_meeting_url(self):
        """RED: Test de validación de entrada."""
        # Given
        meeting_processor = MeetingProcessor(Mock(), Mock(), Mock())
        invalid_url = "not-a-valid-url"
        
        # When & Then
        with pytest.raises(InvalidMeetingUrlException) as exc_info:
            meeting_processor.process_meeting(invalid_url)
        
        assert "Invalid meeting URL" in str(exc_info.value)
```

#### **Paso 2: GREEN - Implementación Mínima**
```python path=null start=null
# ✅ TDD GREEN - Código mínimo para hacer pasar los tests
from dataclasses import dataclass
from typing import List
import re
from abc import ABC, abstractmethod

@dataclass
class ProcessingResult:
    success: bool
    prd: 'PRD' = None
    tasks: List['TareaAsignada'] = None
    processing_time_seconds: float = 0.0

class MeetingProcessor:
    """✅ TDD GREEN - Implementación mínima que satisface los tests."""
    
    def __init__(self, transcription_service, prd_generator, task_assigner):
        self.transcription_service = transcription_service
        self.prd_generator = prd_generator
        self.task_assigner = task_assigner
    
    def process_meeting(self, meeting_url: str) -> ProcessingResult:
        """Implementación mínima para pasar los tests."""
        # Validación básica para pasar el test de URL inválida
        if not self._is_valid_meeting_url(meeting_url):
            raise InvalidMeetingUrlException(f"Invalid meeting URL: {meeting_url}")
        
        # Implementación mínima para pasar el test de éxito
        mock_prd = PRD(id="test-prd", titulo="Test PRD")
        mock_tasks = [TareaAsignada(id_tarea="task-1", descripcion="Test task")]
        
        return ProcessingResult(
            success=True,
            prd=mock_prd,
            tasks=mock_tasks,
            processing_time_seconds=45.0  # < 300 segundos (RNF1.0)
        )
    
    def _is_valid_meeting_url(self, url: str) -> bool:
        """Validación mínima para pasar los tests."""
        valid_patterns = [
            r'https://meet\.google\.com/.+',
            r'https://teams\.microsoft\.com/.+',
            r'https://zoom\.us/.+'
        ]
        return any(re.match(pattern, url) for pattern in valid_patterns)
```

#### **Paso 3: REFACTOR - Mejora del Diseño**
```python path=null start=null
# ✅ TDD REFACTOR - Aplicamos principios SOLID y Clean Architecture
from abc import ABC, abstractmethod
from typing import Protocol
import logging

# Aplicamos ISP (Interface Segregation Principle)
class AudioProcessor(Protocol):
    def process_audio(self, audio_url: str) -> str: pass

class RequirementExtractor(Protocol):
    def extract_requirements(self, transcription: str) -> List['Requisito']: pass

class TaskAssigner(Protocol):
    def assign_tasks(self, requirements: List['Requisito']) -> List['TareaAsignada']: pass

class MeetingProcessor:
    """
    ✅ TDD REFACTOR - Código mejorado manteniendo tests verdes.
    
    Ahora aplica principios SOLID:
    - SRP: Solo procesa reuniones
    - DIP: Depende de abstracciones
    - ISP: Interfaces específicas
    """
    
    def __init__(
        self, 
        audio_processor: AudioProcessor,
        requirement_extractor: RequirementExtractor,
        task_assigner: TaskAssigner,
        logger: logging.Logger = None
    ):
        self.audio_processor = audio_processor
        self.requirement_extractor = requirement_extractor
        self.task_assigner = task_assigner
        self.logger = logger or logging.getLogger(__name__)
    
    def process_meeting(self, meeting_url: str) -> ProcessingResult:
        """✅ REFACTOR - Implementación robusta que mantiene tests verdes."""
        start_time = time.time()
        
        try:
            # Validación mejorada
            self._validate_meeting_url(meeting_url)
            
            # Procesamiento con mejor separación de responsabilidades
            transcription = self.audio_processor.process_audio(meeting_url)
            requirements = self.requirement_extractor.extract_requirements(transcription)
            
            prd = self._generate_prd_from_requirements(requirements)
            tasks = self.task_assigner.assign_tasks(requirements)
            
            processing_time = time.time() - start_time
            
            # Validación de RNF1.0 (< 5 minutos)
            if processing_time > 300:
                self.logger.warning(f"Processing time exceeded 5 minutes: {processing_time}s")
            
            return ProcessingResult(
                success=True,
                prd=prd,
                tasks=tasks,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Meeting processing failed: {str(e)}")
            raise
    
    def _validate_meeting_url(self, url: str) -> None:
        """✅ REFACTOR - Validación extraída a método privado (Clean Code)."""
        if not url or not self._is_valid_meeting_url(url):
            raise InvalidMeetingUrlException(f"Invalid meeting URL: {url}")
    
    def _generate_prd_from_requirements(self, requirements: List[Requisito]) -> PRD:
        """✅ REFACTOR - Lógica de generación de PRD extraída."""
        if not requirements:
            raise ValueError("Cannot generate PRD without requirements")
        
        return PRD(
            id=self._generate_prd_id(),
            titulo=self._extract_title_from_requirements(requirements),
            requirements=requirements,
            fecha_creacion=datetime.now()
        )
```

### 1.3. TDD para Casos de Uso Específicos del Proyecto

#### **TDD para RF4.0 - Asignación Inteligente de Tareas**
```python path=null start=null
# ✅ TDD para Factory Pattern de Asignación de Roles
class TestRoleAssignmentFactory:
    """TDD para RF4.0 - Asignación Inteligente de Tareas."""
    
    def test_should_assign_frontend_developer_for_ui_requirements(self):
        """RED: Test que define comportamiento de clasificación."""
        # Given
        ui_requirement = Requisito(
            descripcion="Necesitamos una interfaz React responsive para el dashboard",
            tipo=RequirementType.FUNCTIONAL
        )
        
        # When
        assigned_role = RoleAssignmentFactory.get_assignee_for_requirement(ui_requirement)
        
        # Then
        assert assigned_role == "Frontend Developer"
    
    def test_should_assign_backend_developer_for_api_requirements(self):
        """RED: Test para clasificación de APIs."""
        # Given
        api_requirement = Requisito(
            descripcion="Implementar API REST para autenticación con JWT",
            tipo=RequirementType.FUNCTIONAL
        )
        
        # When
        assigned_role = RoleAssignmentFactory.get_assignee_for_requirement(api_requirement)
        
        # Then
        assert assigned_role == "Backend Developer"
    
    def test_should_assign_cloud_engineer_for_infrastructure_requirements(self):
        """RED: Test para requisitos de infraestructura."""
        # Given
        infra_requirement = Requisito(
            descripcion="Configurar auto-scaling en AWS Lambda para el procesamiento",
            tipo=RequirementType.NON_FUNCTIONAL
        )
        
        # When
        assigned_role = RoleAssignmentFactory.get_assignee_for_requirement(infra_requirement)
        
        # Then
        assert assigned_role == "Cloud Engineer"

# GREEN: Implementación mínima
class RoleAssignmentFactory:
    """✅ TDD GREEN - Factory que cumple con los tests."""
    
    @classmethod
    def get_assignee_for_requirement(cls, requirement: Requisito) -> str:
        """Implementación mínima para pasar los tests."""
        description_lower = requirement.descripcion.lower()
        
        # Lógica mínima para pasar los tests
        if any(keyword in description_lower for keyword in ['react', 'ui', 'interface', 'dashboard']):
            return "Frontend Developer"
        elif any(keyword in description_lower for keyword in ['api', 'rest', 'jwt', 'autenticación']):
            return "Backend Developer"
        elif any(keyword in description_lower for keyword in ['aws', 'lambda', 'scaling', 'infraestructura']):
            return "Cloud Engineer"
        else:
            return "Full Stack Developer"  # Default

# REFACTOR: Aplicamos Strategy Pattern y mejoramos la clasificación
class RequirementClassificationStrategy(ABC):
    @abstractmethod
    def classify(self, description: str) -> str:
        pass

class KeywordBasedClassifier(RequirementClassificationStrategy):
    """✅ TDD REFACTOR - Estrategia de clasificación basada en keywords."""
    
    def __init__(self):
        self.role_keywords = {
            'Frontend Developer': ['react', 'vue', 'angular', 'ui', 'interface', 'css', 'html', 'responsive'],
            'Backend Developer': ['api', 'rest', 'graphql', 'database', 'sql', 'jwt', 'auth', 'server'],
            'Cloud Engineer': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'lambda', 'scaling'],
            'UX Designer': ['ux', 'ui/ux', 'usabilidad', 'usuario', 'diseño', 'mockup']
        }
    
    def classify(self, description: str) -> str:
        description_lower = description.lower()
        
        for role, keywords in self.role_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return role
        
        return "Full Stack Developer"

class RoleAssignmentFactory:
    """✅ TDD REFACTOR - Factory mejorado con Strategy Pattern."""
    
    def __init__(self, classifier: RequirementClassificationStrategy = None):
        self.classifier = classifier or KeywordBasedClassifier()
    
    def get_assignee_for_requirement(self, requirement: Requisito) -> str:
        """Método refactorizado que mantiene los tests verdes."""
        return self.classifier.classify(requirement.descripcion)
```

### 1.4. TDD para RNF5.0 - Tolerancia a Fallos (Circuit Breaker)

```python path=null start=null
# ✅ TDD para Circuit Breaker Pattern
class TestCircuitBreaker:
    """TDD para RNF5.0 - Tolerancia a Fallos."""
    
    def test_should_allow_calls_when_circuit_is_closed(self):
        """RED: Test para comportamiento normal del circuit breaker."""
        # Given
        circuit_breaker = CircuitBreaker(failure_threshold=3)
        
        def successful_service_call():
            return "success"
        
        # When
        result = circuit_breaker.call(successful_service_call)
        
        # Then
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_should_open_circuit_after_failure_threshold(self):
        """RED: Test para apertura del circuito tras fallos."""
        # Given
        circuit_breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_service_call():
            raise TranscriptionServiceException("Service unavailable")
        
        # When - Ejecutar 3 fallos (threshold)
        for _ in range(3):
            with pytest.raises(TranscriptionServiceException):
                circuit_breaker.call(failing_service_call)
        
        # Then
        assert circuit_breaker.state == CircuitState.OPEN
    
    def test_should_reject_calls_when_circuit_is_open(self):
        """RED: Test para rechazo de calls cuando circuito está abierto."""
        # Given
        circuit_breaker = CircuitBreaker(failure_threshold=1)
        circuit_breaker.state = CircuitState.OPEN
        
        def any_service_call():
            return "should not execute"
        
        # When & Then
        with pytest.raises(CircuitBreakerOpenException):
            circuit_breaker.call(any_service_call)
    
    def test_should_attempt_half_open_after_timeout(self):
        """RED: Test para transición a half-open tras timeout."""
        # Given
        circuit_breaker = CircuitBreaker(failure_threshold=1, timeout=1)
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time() - 2  # 2 segundos atrás
        
        def recovery_test_call():
            return "recovered"
        
        # When
        result = circuit_breaker.call(recovery_test_call)
        
        # Then
        assert result == "recovered"
        assert circuit_breaker.state == CircuitState.CLOSED

# GREEN & REFACTOR: Implementación del Circuit Breaker
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """✅ TDD - Circuit Breaker implementado siguiendo TDD."""
    
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """✅ TDD - Método principal que satisface todos los tests."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si debe intentar resetear el circuito."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.timeout
    
    def _on_success(self):
        """Maneja el éxito de una llamada."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Maneja el fallo de una llamada."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 5. Principios de Diseño: SOLID y KISS (Potenciados por TDD)

### 2.1. TDD + Single Responsibility Principle (SRP)

**TDD facilita SRP porque cada test se enfoca en una responsabilidad específica.**

```python path=null start=null
# ✅ TDD + SRP - Cada clase tiene una sola razón para cambiar
class TestTranscriptionService:
    """TDD para servicio con responsabilidad única: transcripción."""
    
    def test_should_transcribe_audio_file_successfully(self):
        """Test enfocado en una sola responsabilidad."""
        # Given
        transcription_service = TranscriptionService(deepgram_client=Mock())
        audio_file = AudioFile(url="http://example.com/audio.mp3", size_mb=5.2)
        
        # When
        result = transcription_service.transcribe(audio_file)
        
        # Then
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_should_handle_audio_file_too_large(self):
        """Test para manejo de archivos grandes."""
        # Given
        transcription_service = TranscriptionService(deepgram_client=Mock())
        large_audio = AudioFile(url="http://example.com/large.mp3", size_mb=100)
        
        # When & Then
        with pytest.raises(AudioFileTooLargeException):
            transcription_service.transcribe(large_audio)

class TranscriptionService:
    """✅ SRP - Solo se encarga de transcripción de audio."""
    
    def __init__(self, deepgram_client):
        self.deepgram_client = deepgram_client
        self.max_file_size_mb = 50  # Límite de tamaño
    
    def transcribe(self, audio_file: AudioFile) -> str:
        """Única responsabilidad: transcribir audio a texto."""
        self._validate_audio_file(audio_file)
        
        # Llamada a Deepgram API
        response = self.deepgram_client.transcription.prerecorded(
            {'url': audio_file.url},
            {'punctuate': True, 'model': 'nova'}
        )
        
        return self._extract_transcript_text(response)
    
    def _validate_audio_file(self, audio_file: AudioFile) -> None:
        """Validación específica para transcripción."""
        if audio_file.size_mb > self.max_file_size_mb:
            raise AudioFileTooLargeException(
                f"Audio file too large: {audio_file.size_mb}MB > {self.max_file_size_mb}MB"
            )
```

### 2.2. TDD + Dependency Inversion Principle (DIP)

**TDD promueve DIP porque facilita el uso de mocks y abstracciones.**

```python path=null start=null
# ✅ TDD + DIP - Tests usando abstracciones
class TestPRDGenerationService:
    """TDD que promueve inversión de dependencias."""
    
    @pytest.fixture
    def mock_requirement_extractor(self):
        """Mock de la abstracción."""
        mock = Mock(spec=RequirementExtractor)
        mock.extract_requirements.return_value = [
            Requisito(id="req-1", descripcion="Test requirement", tipo=RequirementType.FUNCTIONAL)
        ]
        return mock
    
    @pytest.fixture
    def mock_template_generator(self):
        """Mock de generador de templates."""
        mock = Mock(spec=TemplateGenerator)
        mock.generate_prd_template.return_value = "# Test PRD Template"
        return mock
    
    def test_should_generate_prd_from_transcription(
        self, 
        mock_requirement_extractor, 
        mock_template_generator
    ):
        """TDD usando abstracciones (DIP)."""
        # Given
        prd_service = PRDGenerationService(
            requirement_extractor=mock_requirement_extractor,  # ✅ DIP
            template_generator=mock_template_generator         # ✅ DIP  
        )
        transcription = "We need to implement user authentication and dashboard"
        
        # When
        prd = prd_service.generate_prd(transcription)
        
        # Then
        assert prd is not None
        assert prd.titulo is not None
        assert len(prd.requirements) > 0
        
        # Verificar que usa las abstracciones
        mock_requirement_extractor.extract_requirements.assert_called_once_with(transcription)
        mock_template_generator.generate_prd_template.assert_called_once()

# Abstracciones que facilitan testing
class RequirementExtractor(Protocol):
    def extract_requirements(self, text: str) -> List[Requisito]: pass

class TemplateGenerator(Protocol):
    def generate_prd_template(self, requirements: List[Requisito]) -> str: pass

class PRDGenerationService:
    """✅ DIP - Depende de abstracciones, no de implementaciones concretas."""
    
    def __init__(
        self, 
        requirement_extractor: RequirementExtractor,
        template_generator: TemplateGenerator
    ):
        # ✅ DIP - Dependencias inyectadas como abstracciones
        self.requirement_extractor = requirement_extractor
        self.template_generator = template_generator
    
    def generate_prd(self, transcription: str) -> PRD:
        """Genera PRD usando dependencias abstraídas."""
        requirements = self.requirement_extractor.extract_requirements(transcription)
        
        if not requirements:
            raise ValueError("No requirements found in transcription")
        
        template = self.template_generator.generate_prd_template(requirements)
        
        return PRD(
            id=self._generate_prd_id(),
            titulo=self._generate_title_from_requirements(requirements),
            requirements=requirements,
            template_content=template,
            fecha_creacion=datetime.now()
        )
```

### 2.3. Open/Closed Principle (OCP)

**Implementación para RF5.0 - Integración con PMS:**
```python path=null start=null
from abc import ABC, abstractmethod

# ✅ CUMPLE OCP - Extensible sin modificación
class PMSIntegration(ABC):
    @abstractmethod
    def create_task(self, requirement: Requisito) -> TareaAsignada:
        pass

class JiraIntegration(PMSIntegration):
    def create_task(self, requirement: Requisito) -> TareaAsignada:
        # Implementación específica para Jira
        pass

class TrelloIntegration(PMSIntegration):
    def create_task(self, requirement: Requisito) -> TareaAsignada:
        # Implementación específica para Trello
        pass

class LinearIntegration(PMSIntegration):
    def create_task(self, requirement: Requisito) -> TareaAsignada:
        # Nueva integración sin modificar código existente
        pass

# Factory Pattern para extensibilidad
class PMSIntegrationFactory:
    _integrations = {
        'jira': JiraIntegration,
        'trello': TrelloIntegration,
        'linear': LinearIntegration
    }
    
    @classmethod
    def create_integration(cls, pms_type: str) -> PMSIntegration:
        return cls._integrations[pms_type]()
```

### 2.4. Liskov Substitution Principle (LSP)

**Aplicación en Jerarquía de Requisitos:**
```python path=null start=null
class Requisito(ABC):
    def __init__(self, descripcion: str, prioridad: str):
        self.descripcion = descripcion
        self.prioridad = prioridad
    
    @abstractmethod
    def generar_tarea(self) -> TareaAsignada:
        pass

class RequisitoFuncional(Requisito):
    def generar_tarea(self) -> TareaAsignada:
        # ✅ CUMPLE LSP - Comportamiento consistente con clase base
        return TareaAsignada(
            tipo="funcional",
            descripcion=self.descripcion,
            prioridad=self.prioridad
        )

class RequisitoNoFuncional(Requisito):
    def generar_tarea(self) -> TareaAsignada:
        # ✅ CUMPLE LSP - Comportamiento consistente con clase base
        return TareaAsignada(
            tipo="no_funcional", 
            descripcion=self.descripcion,
            prioridad=self.prioridad
        )
```

### 2.5. Interface Segregation Principle (ISP)

**Interfaces Específicas para Diferentes Responsabilidades:**
```python path=null start=null
# ✅ CUMPLE ISP - Interfaces específicas y cohesivas
class AudioProcessable(Protocol):
    def process_audio(self, audio_data: bytes) -> str:
        pass

class TextAnalyzable(Protocol):
    def extract_requirements(self, text: str) -> List[Requisito]:
        pass

class TaskAssignable(Protocol):
    def assign_to_role(self, requirement: Requisito) -> str:
        pass

class NotificationSender(Protocol):
    def send_notification(self, message: str, recipient: str):
        pass

# Implementación que solo depende de interfaces necesarias
class PRDGenerationService:
    def __init__(
        self, 
        text_analyzer: TextAnalyzable,
        task_assigner: TaskAssignable,
        notifier: NotificationSender
    ):
        # ✅ Solo depende de interfaces que realmente usa
        self.text_analyzer = text_analyzer
        self.task_assigner = task_assigner  
        self.notifier = notifier
```

### 2.6. KISS Principle (Keep It Simple, Stupid)

**Aplicación en Diseño de Componentes:**
```python path=null start=null
# ❌ VIOLACIÓN KISS - Complejidad innecesaria
class ComplexMeetingProcessor:
    def process_with_multiple_algorithms(self, audio):
        # Implementación con múltiples algoritmos, caching complejo,
        # optimizaciones prematuras, configuraciones excesivas
        pass

# ✅ CUMPLE KISS - Implementación simple y directa
class MeetingProcessor:
    def __init__(self, transcription_service: TranscriptionService):
        self.transcription_service = transcription_service
    
    def process_meeting(self, audio_url: str) -> PRD:
        """Procesa una reunión de forma simple y directa."""
        transcription = self.transcription_service.transcribe(audio_url)
        requirements = self._extract_requirements(transcription)
        return self._generate_prd(requirements)
    
    def _extract_requirements(self, transcription: str) -> List[Requisito]:
        # Implementación simple usando bibliotecas estándar
        pass
    
    def _generate_prd(self, requirements: List[Requisito]) -> PRD:
        # Generación directa del PRD
        pass
```

---

## 6. Estrategias de Arquitectura: Clean Architecture (Guiada por TDD)

### 3.1. Capas de Clean Architecture

**Aplicación en M2PRD-001:**

```
┌─────────────────────────────────────────────┐
│ UI/Controllers (Presentation Layer)         │
│ • Chrome Extension                          │
│ • Webhook Endpoints                         │
│ • n8n/Make Workflows                        │
├─────────────────────────────────────────────┤
│ Application Services (Use Cases)            │
│ • ProcessMeetingUseCase                     │
│ • GeneratePRDUseCase                        │
│ • AssignTasksUseCase                        │
├─────────────────────────────────────────────┤
│ Domain Layer (Business Logic)               │
│ • Entities: Reunion, PRD, Requisito        │
│ • Value Objects: AudioFile, Transcripcion  │
│ • Domain Services: RequirementClassifier   │
├─────────────────────────────────────────────┤
│ Infrastructure Layer                        │
│ • Database: PostgreSQL, Redis, MongoDB     │
│ • External APIs: Deepgram, Jira, Linear    │
│ • Cloud Services: AWS Lambda, GCF          │
└─────────────────────────────────────────────┘
```

### 3.2. TDD para Use Cases (Application Layer)

```python path=null start=null
# ✅ TDD para Use Cases - Application Layer
class TestProcessMeetingUseCase:
    """TDD para caso de uso principal del sistema."""
    
    @pytest.fixture
    def setup_use_case_dependencies(self):
        """Setup con todas las dependencias mockeadas."""
        return {
            'meeting_repository': Mock(spec=MeetingRepository),
            'transcription_service': Mock(spec=TranscriptionService), 
            'prd_generator': Mock(spec=PRDGenerationService),
            'task_repository': Mock(spec=TaskRepository),
            'event_publisher': Mock(spec=EventPublisher)
        }
    
    def test_should_execute_complete_meeting_processing_flow(self, setup_use_case_dependencies):
        """RED: Test que define el flujo completo."""
        # Given
        deps = setup_use_case_dependencies
        use_case = ProcessMeetingUseCase(**deps)
        
        command = ProcessMeetingCommand(
            meeting_id="meeting-123",
            audio_url="https://example.com/audio.mp3",
            requester_id="user-456"
        )
        
        # Setup mocks
        mock_meeting = Meeting(id="meeting-123", audio_url=command.audio_url)
        deps['meeting_repository'].get_by_id.return_value = mock_meeting
        deps['transcription_service'].transcribe.return_value = "Mock transcription"
        
        mock_prd = PRD(id="prd-789", titulo="Test PRD")
        deps['prd_generator'].generate_prd.return_value = mock_prd
        
        # When
        response = use_case.execute(command)
        
        # Then - Verificar comportamiento completo
        assert response.success is True
        assert response.prd == mock_prd
        assert response.processing_time_seconds < 300  # RNF1.0
        
        # Verificar secuencia de llamadas (Clean Architecture)
        deps['meeting_repository'].get_by_id.assert_called_once_with("meeting-123")
        deps['transcription_service'].transcribe.assert_called_once()
        deps['prd_generator'].generate_prd.assert_called_once()
        deps['event_publisher'].publish.assert_called_once()

# GREEN: Implementación del Use Case
from dataclasses import dataclass
from typing import List
import time

@dataclass
class ProcessMeetingCommand:
    """Command pattern para entrada del use case."""
    meeting_id: str
    audio_url: str
    requester_id: str

@dataclass  
class ProcessMeetingResponse:
    """Response con resultado del procesamiento."""
    success: bool
    prd: PRD = None
    tasks: List[TareaAsignada] = None
    processing_time_seconds: float = 0.0
    error_message: str = None

class ProcessMeetingUseCase:
    """
    ✅ Clean Architecture + TDD - Use Case en Application Layer.
    
    Orquesta el flujo de procesamiento sin conocer detalles de implementación.
    """
    
    def __init__(
        self,
        meeting_repository: MeetingRepository,
        transcription_service: TranscriptionService,
        prd_generator: PRDGenerationService,
        task_repository: TaskRepository,
        event_publisher: EventPublisher
    ):
        # ✅ Clean Architecture - Dependencias del dominio e infraestructura
        self._meeting_repository = meeting_repository
        self._transcription_service = transcription_service
        self._prd_generator = prd_generator
        self._task_repository = task_repository
        self._event_publisher = event_publisher
    
    def execute(self, command: ProcessMeetingCommand) -> ProcessMeetingResponse:
        """✅ TDD GREEN - Implementación que satisface el test."""
        start_time = time.time()
        
        try:
            # 1. Validar comando
            self._validate_command(command)
            
            # 2. Recuperar reunión (Infrastructure)
            meeting = self._meeting_repository.get_by_id(command.meeting_id)
            if not meeting:
                raise MeetingNotFoundException(f"Meeting {command.meeting_id} not found")
            
            # 3. Transcribir audio (Infrastructure)
            transcription = self._transcription_service.transcribe(meeting.audio_url)
            
            # 4. Generar PRD (Domain Service)
            prd = self._prd_generator.generate_prd(transcription)
            
            # 5. Crear tareas (Domain Logic)
            tasks = self._create_tasks_from_prd(prd)
            
            # 6. Persistir resultados (Infrastructure)
            self._task_repository.save_all(tasks)
            
            # 7. Publicar evento (Infrastructure)
            processing_time = time.time() - start_time
            
            self._event_publisher.publish(
                MeetingProcessedEvent(
                    meeting_id=command.meeting_id,
                    prd_id=prd.id,
                    task_ids=[task.id for task in tasks],
                    processing_time_seconds=processing_time
                )
            )
            
            return ProcessMeetingResponse(
                success=True,
                prd=prd,
                tasks=tasks,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            return ProcessMeetingResponse(
                success=False,
                error_message=str(e),
                processing_time_seconds=time.time() - start_time
            )
    
    def _validate_command(self, command: ProcessMeetingCommand) -> None:
        """Validación de entrada del comando."""
        if not command.meeting_id:
            raise ValueError("Meeting ID is required")
        if not command.audio_url:
            raise ValueError("Audio URL is required")
    
    def _create_tasks_from_prd(self, prd: PRD) -> List[TareaAsignada]:
        """Lógica de dominio para crear tareas."""
        return [req.generar_tarea() for req in prd.requirements]
```

### 3.3. TDD para Domain Entities (Domain Layer)

```python path=null start=null
# ✅ TDD para Entidades de Dominio
class TestPRDEntity:
    """TDD para entidad PRD con lógica de dominio rica."""
    
    def test_should_create_prd_with_valid_requirements(self):
        """RED: Test para creación válida de PRD."""
        # Given
        requirements = [
            Requisito(id="req-1", descripcion="User auth", tipo=RequirementType.FUNCTIONAL),
            Requisito(id="req-2", descripcion="Dashboard UI", tipo=RequirementType.FUNCTIONAL)
        ]
        
        # When
        prd = PRD(
            id="prd-123",
            titulo="User Management System",
            requirements=requirements
        )
        
        # Then
        assert prd.id == "prd-123"
        assert len(prd.requirements) == 2
        assert prd.is_valid()
    
    def test_should_reject_prd_without_requirements(self):
        """RED: Test para invariante de dominio."""
        # Given & When & Then
        with pytest.raises(DomainException) as exc_info:
            PRD(
                id="prd-123",
                titulo="Empty PRD",
                requirements=[]  # ❌ Violación de invariante
            )
        
        assert "PRD must have at least one requirement" in str(exc_info.value)
    
    def test_should_generate_all_tasks_from_requirements(self):
        """RED: Test para lógica de dominio."""
        # Given
        requirements = [
            Requisito(id="req-1", descripcion="Frontend component", tipo=RequirementType.FUNCTIONAL),
            Requisito(id="req-2", descripcion="API endpoint", tipo=RequirementType.FUNCTIONAL)
        ]
        
        prd = PRD(id="prd-123", titulo="Test PRD", requirements=requirements)
        mock_assignee_resolver = Mock()
        mock_assignee_resolver.resolve_assignee_for_requirement.side_effect = ["Frontend Developer", "Backend Developer"]
        
        # When
        tasks = prd.generar_todas_las_tareas(mock_assignee_resolver)
        
        # Then
        assert len(tasks) == 2
        assert all(isinstance(task, TareaAsignada) for task in tasks)
        assert tasks[0].assignee == "Frontend Developer"
        assert tasks[1].assignee == "Backend Developer"

# GREEN & REFACTOR: Entidad PRD rica en comportamiento
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from enum import Enum

class RequirementType(Enum):
    FUNCTIONAL = "funcional"
    NON_FUNCTIONAL = "no_funcional"

@dataclass
class Requisito:
    """✅ TDD - Value Object para requisitos."""
    id: str
    descripcion: str
    tipo: RequirementType
    prioridad: str = "P2"
    
    def generar_tarea(self, assignee_resolver=None) -> 'TareaAsignada':
        """Lógica de dominio para generar tarea."""
        assignee = "Full Stack Developer"  # Default
        
        if assignee_resolver:
            assignee = assignee_resolver.resolve_assignee_for_requirement(self)
        
        return TareaAsignada(
            id_tarea=f"TASK-{self.id}",
            requisito_id=self.id,
            descripcion=self.descripcion,
            assignee=assignee,
            prioridad=self.prioridad
        )

@dataclass
class PRD:
    """
    ✅ TDD - Entidad de dominio rica con invariantes y comportamiento.
    
    Aggregate Root que encapsula la lógica de negocio de los PRDs.
    """
    id: str
    titulo: str
    requirements: List[Requisito]
    fecha_creacion: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validación de invariantes de dominio."""
        self._validate_domain_invariants()
    
    def is_valid(self) -> bool:
        """Verifica si el PRD cumple con las reglas de dominio."""
        try:
            self._validate_domain_invariants()
            return True
        except DomainException:
            return False
    
    def add_requirement(self, requirement: Requisito) -> None:
        """Añade un requisito manteniendo invariantes."""
        if not requirement:
            raise ValueError("Requirement cannot be None")
        
        self.requirements.append(requirement)
    
    def generar_todas_las_tareas(self, assignee_resolver) -> List['TareaAsignada']:
        """
        ✅ TDD - Lógica de dominio para generar todas las tareas.
        
        Business Logic: Un PRD genera tareas basadas en sus requisitos.
        """
        if not self.requirements:
            raise DomainException("Cannot generate tasks from empty requirements")
        
        return [req.generar_tarea(assignee_resolver) for req in self.requirements]
    
    def calcular_complejidad(self) -> str:
        """Lógica de dominio para calcular complejidad del PRD."""
        num_requirements = len(self.requirements)
        
        if num_requirements <= 3:
            return "BAJA"
        elif num_requirements <= 8:
            return "MEDIA"
        else:
            return "ALTA"
    
    def _validate_domain_invariants(self) -> None:
        """✅ Domain-Driven Design - Validación de invariantes."""
        if not self.requirements:
            raise DomainException("PRD must have at least one requirement")
        
        if len(self.titulo) < 5:
            raise DomainException("PRD title must be at least 5 characters")
        
        # Validar que no hay requisitos duplicados
        requirement_ids = [req.id for req in self.requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise DomainException("PRD cannot have duplicate requirements")

@dataclass
class TareaAsignada:
    """Value Object para tareas asignadas."""
    id_tarea: str
    requisito_id: str
    descripcion: str
    assignee: str
    prioridad: str = "P2"
    estado: str = "PENDIENTE"

class DomainException(Exception):
    """Excepción específica de dominio."""
    pass
```

### 3.4. Ports & Adapters (Hexagonal Architecture)

```python path=null start=null
# ✅ PORTS & ADAPTERS - Definición de puertos
from abc import ABC, abstractmethod

# PUERTOS (Interfaces)
class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_url: str, api_key: str) -> str:
        pass

class SecretManager(ABC):
    @abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

class PMSIntegration(ABC):
    @abstractmethod
    def create_task(self, task: TareaAsignada) -> str:
        pass

# ADAPTADORES (Implementaciones)
class DeepgramTranscriptionAdapter(TranscriptionService):
    def __init__(self, deepgram_client):
        self.client = deepgram_client
    
    def transcribe(self, audio_url: str, api_key: str) -> str:
        # ✅ Implementación específica de Deepgram
        response = self.client.transcription.prerecorded(
            {'url': audio_url}, 
            {'punctuate': True, 'model': 'nova'}
        )
        return response['results']['channels'][0]['alternatives'][0]['transcript']

class AWSSecretsManagerAdapter(SecretManager):
    def __init__(self, aws_client):
        self.client = aws_client
    
    def get_secret(self, secret_name: str) -> str:
        # ✅ Implementación específica de AWS
        response = self.client.get_secret_value(SecretId=secret_name)
        return response['SecretString']

class JiraIntegrationAdapter(PMSIntegration):
    def __init__(self, jira_client):
        self.client = jira_client
    
    def create_task(self, task: TareaAsignada) -> str:
        # ✅ Implementación específica de Jira
        issue_data = {
            'project': {'key': 'PRD'},
            'summary': task.descripcion,
            'description': f"Requisito: {task.requisito_id}",
            'issuetype': {'name': 'Task'},
            'assignee': {'name': task.assignee},
            'priority': {'name': task.prioridad}
        }
        issue = self.client.create_issue(fields=issue_data)
        return issue.key
```

---

## 7. Patrones de Diseño Aplicados

### 4.1. Factory Pattern

**Aplicación para RF4.0 - Asignación Inteligente:**
```python path=null start=null
class RoleAssignmentFactory:
    """Factory para resolver asignación de roles basado en tipo de requisito."""
    
    _role_mappings = {
        'ui_requirement': 'Frontend Developer',
        'api_requirement': 'Backend Developer', 
        'database_requirement': 'Backend Developer',
        'infrastructure_requirement': 'Cloud Engineer',
        'user_experience': 'UX Designer',
        'full_stack': 'Full Stack Developer'
    }
    
    @classmethod
    def get_assignee_for_requirement(cls, requisito: Requisito) -> str:
        requirement_type = cls._classify_requirement(requisito.descripcion)
        return cls._role_mappings.get(requirement_type, 'Full Stack Developer')
    
    @classmethod
    def _classify_requirement(cls, descripcion: str) -> str:
        # ✅ Factory Method - Lógica de clasificación centralizada
        descripcion_lower = descripcion.lower()
        
        if any(keyword in descripcion_lower for keyword in ['ui', 'interface', 'frontend', 'react']):
            return 'ui_requirement'
        elif any(keyword in descripcion_lower for keyword in ['api', 'backend', 'server', 'python']):
            return 'api_requirement'
        elif any(keyword in descripcion_lower for keyword in ['database', 'postgresql', 'redis']):
            return 'database_requirement'
        elif any(keyword in descripcion_lower for keyword in ['cloud', 'aws', 'docker', 'kubernetes']):
            return 'infrastructure_requirement'
        elif any(keyword in descripcion_lower for keyword in ['ux', 'user', 'design', 'usability']):
            return 'user_experience'
        else:
            return 'full_stack'
```

### 4.2. Strategy Pattern

**Aplicación para Diferentes Algoritmos de NLP:**
```python path=null start=null
from abc import ABC, abstractmethod

class RequirementExtractionStrategy(ABC):
    @abstractmethod
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        pass

class SpacyRequirementExtractor(RequirementExtractionStrategy):
    def __init__(self, nlp_model):
        self.nlp = nlp_model
    
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        # ✅ STRATEGY - Implementación específica con spaCy
        doc = self.nlp(transcription)
        requirements = []
        
        for sent in doc.sents:
            if self._is_requirement_sentence(sent):
                req = self._create_requirement_from_sentence(sent)
                requirements.append(req)
        
        return requirements

class OpenAIRequirementExtractor(RequirementExtractionStrategy):
    def __init__(self, openai_client):
        self.client = openai_client
    
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        # ✅ STRATEGY - Implementación específica con OpenAI
        prompt = f"""
        Extrae los requisitos funcionales y no funcionales de la siguiente transcripción:
        {transcription}
        
        Formato JSON: [{{"tipo": "funcional|no_funcional", "descripcion": "...", "prioridad": "P0|P1|P2"}}]
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_openai_response(response)

# Context que usa las estrategias
class PRDGenerationService:
    def __init__(self, extraction_strategy: RequirementExtractionStrategy):
        self.extraction_strategy = extraction_strategy
    
    def generate_prd(self, transcription: str) -> PRD:
        # ✅ STRATEGY - El contexto delega la extracción a la estrategia
        requirements = self.extraction_strategy.extract_requirements(transcription)
        
        return PRD(
            id=self._generate_prd_id(),
            titulo=self._extract_title_from_transcription(transcription),
            fecha_creacion=datetime.now(),
            requirements=requirements
        )
```

### 4.3. Observer Pattern

**Aplicación para Notificaciones (RF - Notificar al PM):**
```python path=null start=null
from abc import ABC, abstractmethod
from typing import List

class MeetingProcessingObserver(ABC):
    @abstractmethod
    def on_processing_started(self, meeting_id: str):
        pass
    
    @abstractmethod
    def on_processing_completed(self, meeting_id: str, prd: PRD, tasks: List[TareaAsignada]):
        pass
    
    @abstractmethod 
    def on_processing_failed(self, meeting_id: str, error: Exception):
        pass

class EmailNotificationObserver(MeetingProcessingObserver):
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def on_processing_started(self, meeting_id: str):
        # ✅ OBSERVER - Notificación específica por email
        self.email_service.send_email(
            subject=f"Procesamiento iniciado - Reunión {meeting_id}",
            body="El procesamiento de la reunión ha comenzado...",
            recipients=self._get_pm_emails()
        )
    
    def on_processing_completed(self, meeting_id: str, prd: PRD, tasks: List[TareaAsignada]):
        # ✅ OBSERVER - Notificación de finalización exitosa
        task_summary = self._create_task_summary(tasks)
        self.email_service.send_email(
            subject=f"PRD y tareas listos - Reunión {meeting_id}",
            body=f"PRD generado: {prd.titulo}\nTareas creadas: {task_summary}",
            recipients=self._get_pm_emails(),
            attachments=[prd.generar_pdf()]
        )

class SlackNotificationObserver(MeetingProcessingObserver):
    def __init__(self, slack_client):
        self.slack_client = slack_client
    
    def on_processing_completed(self, meeting_id: str, prd: PRD, tasks: List[TareaAsignada]):
        # ✅ OBSERVER - Notificación específica por Slack
        message = f"""
        ✅ Reunión {meeting_id} procesada exitosamente
        📄 PRD: {prd.titulo}
        📋 Tareas creadas: {len(tasks)}
        """
        self.slack_client.send_message(channel="#pm-notifications", message=message)

# Subject (Observable)
class MeetingProcessor:
    def __init__(self):
        self._observers: List[MeetingProcessingObserver] = []
    
    def add_observer(self, observer: MeetingProcessingObserver):
        self._observers.append(observer)
    
    def remove_observer(self, observer: MeetingProcessingObserver):
        self._observers.remove(observer)
    
    def _notify_processing_started(self, meeting_id: str):
        for observer in self._observers:
            observer.on_processing_started(meeting_id)
    
    def _notify_processing_completed(self, meeting_id: str, prd: PRD, tasks: List[TareaAsignada]):
        for observer in self._observers:
            observer.on_processing_completed(meeting_id, prd, tasks)
    
    def process_meeting(self, meeting_id: str) -> ProcessingResult:
        self._notify_processing_started(meeting_id)
        
        try:
            # Lógica de procesamiento...
            prd = self._generate_prd()
            tasks = self._create_tasks()
            
            self._notify_processing_completed(meeting_id, prd, tasks)
            return ProcessingResult(success=True, prd=prd, tasks=tasks)
            
        except Exception as e:
            self._notify_processing_failed(meeting_id, e)
            raise
```

### 4.4. Circuit Breaker Pattern

**Aplicación para RNF5.0 - Tolerancia a Fallos:**
```python path=null start=null
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Circuito abierto, fallos detectados  
    HALF_OPEN = "half_open" # Probando si el servicio se recuperó

class CircuitBreaker:
    def __init__(
        self, 
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """✅ CIRCUIT BREAKER - Protege llamadas a servicios externos."""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (time.time() - self.last_failure_time) >= self.timeout
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Aplicación en servicios externos
class RobustTranscriptionService:
    def __init__(self, transcription_service: TranscriptionService):
        self.service = transcription_service
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,  # RNF5.0: Máximo 3 reintentos
            timeout=60,           # RNF5.0: Esperar 1 minuto
            expected_exception=TranscriptionServiceException
        )
    
    def transcribe_with_protection(self, audio_url: str, api_key: str) -> str:
        """✅ Transcripción protegida por Circuit Breaker."""
        return self.circuit_breaker.call(
            self.service.transcribe, 
            audio_url, 
            api_key
        )
```

---

## 8. Bases de Datos: Principios ACID (Validados con TDD)

### 5.1. TDD para Transacciones ACID

```python path=null start=null
# ✅ TDD para principios ACID
class TestDatabaseTransactionManager:
    """TDD para gestión de transacciones ACID."""
    
    @pytest.fixture
    def db_manager(self):
        """Setup de manager con BD en memoria."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return DatabaseTransactionManager(engine)
    
    def test_should_commit_transaction_when_successful(self, db_manager):
        """RED: Test para propiedad ATOMICITY y DURABILITY."""
        # Given
        meeting = Meeting(id="meeting-123", audio_url="http://example.com/audio.mp3")
        prd = PRD(id="prd-456", titulo="Test PRD", requirements=[])
        
        # When
        with db_manager.transaction() as session:
            session.add(meeting)
            session.add(prd)
            # Transacción exitosa, debe hacer commit automáticamente
        
        # Then - Verificar DURABILITY
        with db_manager.transaction() as session:
            saved_meeting = session.get(Meeting, "meeting-123")
            saved_prd = session.get(PRD, "prd-456")
            
            assert saved_meeting is not None
            assert saved_prd is not None
    
    def test_should_rollback_transaction_when_error_occurs(self, db_manager):
        """RED: Test para propiedad ATOMICITY en caso de error."""
        # Given
        meeting = Meeting(id="meeting-123", audio_url="http://example.com/audio.mp3")
        
        # When - Simular error en transacción
        with pytest.raises(ValueError):
            with db_manager.transaction() as session:
                session.add(meeting)
                session.flush()  # Asegurar que se agregó temporalmente
                raise ValueError("Simulated error")  # Error que debe causar rollback
        
        # Then - Verificar ATOMICITY (rollback)
        with db_manager.transaction() as session:
            saved_meeting = session.get(Meeting, "meeting-123")
            assert saved_meeting is None  # No debe existir debido al rollback
    
    def test_should_maintain_consistency_with_validation(self, db_manager):
        """RED: Test para propiedad CONSISTENCY."""
        # Given
        invalid_meeting = Meeting(id="", audio_url="")  # Datos inválidos
        
        # When & Then - La validación debe mantener consistencia
        with pytest.raises(ValueError) as exc_info:
            with db_manager.transaction() as session:
                # La validación debe ocurrir antes del commit
                self._validate_meeting_data(invalid_meeting)
                session.add(invalid_meeting)
        
        assert "Meeting must have valid ID" in str(exc_info.value)
    
    def test_should_handle_concurrent_access_with_isolation(self, db_manager):
        """RED: Test para propiedad ISOLATION."""
        # Given
        meeting_id = "concurrent-meeting"
        
        # When - Simular acceso concurrente
        def transaction_1():
            with db_manager.transaction() as session:
                meeting = Meeting(id=meeting_id, audio_url="http://example.com/audio1.mp3")
                session.add(meeting)
                time.sleep(0.1)  # Simular procesamiento
                # Esta transacción debe completarse sin interferencias
        
        def transaction_2():
            time.sleep(0.05)  # Empezar ligeramente después
            with db_manager.transaction() as session:
                # Debe poder leer datos consistentes
                meeting = session.get(Meeting, meeting_id)
                return meeting
        
        # Ejecutar concurrentemente (en pruebas reales usaríamos threading)
        transaction_1()
        result = transaction_2()
        
        # Then - ISOLATION mantenida
        assert result is not None
        assert result.id == meeting_id

# GREEN: Implementación del Transaction Manager
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

class DatabaseTransactionManager:
    """✅ TDD - Gestor de transacciones que garantiza propiedades ACID."""
    
    def __init__(self, engine=None, database_url: str = None):
        if engine:
            self.engine = engine
        elif database_url:
            self.engine = create_engine(database_url)
        else:
            raise ValueError("Either engine or database_url must be provided")
            
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        ✅ ACID Context Manager que garantiza:
        - ATOMICITY: Todo o nada mediante commit/rollback
        - CONSISTENCY: Validaciones antes del commit
        - ISOLATION: Sesiones aisladas por transacción
        - DURABILITY: Cambios persistentes tras commit exitoso
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()  # ✅ ATOMICITY & DURABILITY
        except Exception as e:
            session.rollback()  # ✅ ATOMICITY - Todo o nada
            raise e
        finally:
            session.close()  # ✅ ISOLATION - Limpieza de sesión
    
    def _validate_meeting_data(self, meeting: Meeting) -> None:
        """✅ CONSISTENCY - Validación de reglas de negocio."""
        if not meeting.id:
            raise ValueError("Meeting must have valid ID")
        if not meeting.audio_url:
            raise ValueError("Meeting must have audio URL")

# REFACTOR: Repository con manejo ACID
class MeetingRepository:
    """✅ TDD REFACTOR - Repository que usa principios ACID."""
    
    def __init__(self, db_manager: DatabaseTransactionManager):
        self.db_manager = db_manager
    
    def save_meeting_with_prd_and_tasks(
        self, 
        meeting: Meeting, 
        prd: PRD, 
        tasks: List[TareaAsignada]
    ) -> None:
        """✅ ACID - Operación atómica completa."""
        
        with self.db_manager.transaction() as session:
            # ✅ CONSISTENCY - Validaciones de integridad
            self._validate_meeting_data(meeting)
            self._validate_prd_data(prd)
            self._validate_tasks_data(tasks)
            
            # ✅ ATOMICITY - Todo en una transacción
            session.add(meeting)
            session.add(prd)
            session.add_all(tasks)
            
            # Establecer relaciones
            prd.reunion_id = meeting.id
            for task in tasks:
                task.prd_id = prd.id
            
            # ✅ ISOLATION - La transacción se ejecuta aisladamente
            # ✅ DURABILITY - Los cambios persisten al hacer commit
    
    def _validate_meeting_data(self, meeting: Meeting) -> None:
        """CONSISTENCY - Validaciones de reglas de negocio."""
        if not meeting.url_audio:
            raise ValueError("Meeting must have audio URL")
        if not meeting.id_reunion:
            raise ValueError("Meeting must have valid ID")
    
    def _validate_prd_data(self, prd: PRD) -> None:
        """CONSISTENCY - Validaciones de PRD."""
        if not prd.requirements:
            raise ValueError("PRD must have at least one requirement")
        if len(prd.titulo) < 5:
            raise ValueError("PRD title must be at least 5 characters")
    
    def _validate_tasks_data(self, tasks: List[TareaAsignada]) -> None:
        """CONSISTENCY - Validaciones de tareas."""
        valid_roles = [
            'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 
            'Cloud Engineer', 'UX Designer'
        ]
        
        for task in tasks:
            if task.assignee not in valid_roles:
                raise ValueError(f"Invalid role assignment: {task.assignee}")
```

### 5.2. Implementación de Transacciones ACID

```python path=null start=null
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

class DatabaseTransactionManager:
    """✅ ACID - Gestor de transacciones que garantiza propiedades ACID."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        ✅ ACID - Context manager que garantiza:
        - Atomicity: Todo o nada
        - Consistency: Reglas de integridad
        - Isolation: Transacciones aisladas  
        - Durability: Cambios persistentes
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()  # ✅ ATOMICITY & DURABILITY
        except Exception as e:
            session.rollback()  # ✅ ATOMICITY - Rollback en caso de error
            raise e
        finally:
            session.close()

class MeetingRepository:
    def __init__(self, db_manager: DatabaseTransactionManager):
        self.db_manager = db_manager
    
    def save_meeting_with_prd_and_tasks(
        self, 
        meeting: Reunion, 
        prd: PRD, 
        tasks: List[TareaAsignada]
    ) -> None:
        """✅ ACID - Operación atómica completa."""
        
        with self.db_manager.transaction() as session:
            # ✅ CONSISTENCY - Validaciones de integridad
            self._validate_meeting_data(meeting)
            self._validate_prd_data(prd)
            self._validate_tasks_data(tasks)
            
            # ✅ ATOMICITY - Todo en una transacción
            session.add(meeting)
            session.add(prd)
            session.add_all(tasks)
            
            # ✅ CONSISTENCY - Relaciones consistentes
            prd.reunion_id = meeting.id
            for task in tasks:
                task.prd_id = prd.id
            
            # ✅ ISOLATION - La transacción se ejecuta de forma aislada
            # ✅ DURABILITY - Los cambios persisten al hacer commit
    
    def _validate_meeting_data(self, meeting: Reunion) -> None:
        """✅ CONSISTENCY - Validaciones de reglas de negocio."""
        if not meeting.url_audio:
            raise ValueError("Meeting must have audio URL")
        if not meeting.id_reunion:
            raise ValueError("Meeting must have valid ID")
    
    def _validate_prd_data(self, prd: PRD) -> None:
        """✅ CONSISTENCY - Validaciones de PRD."""
        if not prd.requirements:
            raise ValueError("PRD must have at least one requirement")
        if len(prd.titulo) < 5:
            raise ValueError("PRD title must be at least 5 characters")
    
    def _validate_tasks_data(self, tasks: List[TareaAsignada]) -> None:
        """✅ CONSISTENCY - Validaciones de tareas."""
        valid_roles = ['Frontend Developer', 'Backend Developer', 'Full Stack Developer', 'Cloud Engineer', 'UX Designer']
        
        for task in tasks:
            if task.pm_asignado not in valid_roles:
                raise ValueError(f"Invalid role assignment: {task.pm_asignado}")
```

### 5.3. Gestión de Concurrent Access

```python path=null start=null
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
import redis

class ConcurrentMeetingProcessor:
    """✅ ACID - Gestión de concurrencia para procesamiento de reuniones."""
    
    def __init__(self, db_manager: DatabaseTransactionManager, redis_client: redis.Redis):
        self.db_manager = db_manager
        self.redis = redis_client
    
    def process_meeting_safely(self, meeting_id: str) -> ProcessingResult:
        """✅ ISOLATION - Procesa reunión evitando condiciones de carrera."""
        
        lock_key = f"meeting_processing:{meeting_id}"
        
        # ✅ ISOLATION - Lock distribuido para evitar procesamiento concurrente
        with self.redis.lock(lock_key, timeout=300):  # 5 minutos timeout
            
            with self.db_manager.transaction() as session:
                # ✅ ISOLATION - Select con FOR UPDATE evita lecturas sucias
                meeting = session.execute(
                    select(Meeting)
                    .where(Meeting.id == meeting_id)
                    .with_for_update()  # Bloqueo pesimista
                ).scalar_one_or_none()
                
                if not meeting:
                    raise MeetingNotFoundException(f"Meeting {meeting_id} not found")
                
                if meeting.status == 'PROCESSING':
                    raise MeetingAlreadyProcessingException(
                        f"Meeting {meeting_id} is already being processed"
                    )
                
                # ✅ CONSISTENCY - Actualización atómica de estado
                meeting.status = 'PROCESSING'
                meeting.processing_started_at = datetime.utcnow()
                
                try:
                    # Procesamiento de la reunión
                    result = self._do_processing(meeting)
                    
                    # ✅ ATOMICITY - Todo o nada
                    meeting.status = 'COMPLETED'
                    meeting.processing_completed_at = datetime.utcnow()
                    
                    return result
                    
                except Exception as e:
                    # ✅ CONSISTENCY - Estado consistente en caso de error
                    meeting.status = 'FAILED'
                    meeting.error_message = str(e)
                    raise e
```

---

## 9. Gestión de Calidad de Código

### 6.1. Clean Code Principles

```python path=null start=null
# ✅ CLEAN CODE - Nombres descriptivos y funciones pequeñas
class MeetingAudioProcessor:
    """Procesador de audio de reuniones con principios de Clean Code."""
    
    def process_meeting_audio(self, meeting_url: str) -> ProcessingResult:
        """
        ✅ CLEAN CODE - Función con una sola responsabilidad y nombre descriptivo.
        
        Args:
            meeting_url: URL de la reunión a procesar
            
        Returns:
            ProcessingResult: Resultado del procesamiento con PRD y tareas
            
        Raises:
            InvalidMeetingUrlException: Si la URL no es válida
            TranscriptionFailedException: Si falla la transcripción
        """
        self._validate_meeting_url(meeting_url)
        
        audio_file = self._extract_audio_from_meeting(meeting_url)
        transcription = self._transcribe_audio_safely(audio_file)
        requirements = self._extract_requirements_from_transcription(transcription)
        prd = self._generate_prd_from_requirements(requirements)
        tasks = self._create_tasks_from_prd(prd)
        
        return ProcessingResult(prd=prd, tasks=tasks)
    
    def _validate_meeting_url(self, url: str) -> None:
        """✅ CLEAN CODE - Función pequeña con propósito específico."""
        if not url or not self._is_valid_meeting_url(url):
            raise InvalidMeetingUrlException(f"Invalid meeting URL: {url}")
    
    def _is_valid_meeting_url(self, url: str) -> bool:
        """✅ CLEAN CODE - Función booleana con nombre claro."""
        valid_patterns = [
            r'https://meet\.google\.com/',
            r'https://teams\.microsoft\.com/',
            r'https://zoom\.us/'
        ]
        return any(re.match(pattern, url) for pattern in valid_patterns)
    
    def _extract_audio_from_meeting(self, meeting_url: str) -> AudioFile:
        """✅ CLEAN CODE - Abstracción clara del proceso."""
        # Implementación específica extraída a método privado
        pass
    
    def _transcribe_audio_safely(self, audio_file: AudioFile) -> Transcription:
        """✅ CLEAN CODE - Manejo de errores explícito en el nombre."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return self.transcription_service.transcribe(audio_file)
            except TranscriptionServiceException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise TranscriptionFailedException(
                        f"Failed to transcribe after {max_retries} attempts"
                    ) from e
                self._wait_before_retry(retry_count)
    
    def _wait_before_retry(self, retry_count: int) -> None:
        """✅ CLEAN CODE - Responsabilidad específica extraída."""
        wait_time = min(60, 2 ** retry_count)  # Exponential backoff, max 60s
        time.sleep(wait_time)
```

### 6.2. Logging y Observabilidad

```python path=null start=null
import logging
import structlog
from contextlib import contextmanager
import time
from typing import Dict, Any

# ✅ CLEAN CODE - Configuración centralizada de logging
def configure_structured_logging():
    """Configura logging estructurado para mejor observabilidad."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class ObservableMeetingProcessor:
    """✅ CLEAN CODE - Procesador con observabilidad integrada."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def process_meeting(self, meeting_id: str) -> ProcessingResult:
        """✅ OBSERVABILITY - Procesamiento con logs estructurados."""
        
        with self._log_processing_context(meeting_id) as ctx:
            try:
                self.logger.info(
                    "meeting_processing_started",
                    meeting_id=meeting_id,
                    component="meeting_processor"
                )
                
                # Procesamiento con métricas
                with self._measure_processing_time() as timer:
                    result = self._do_processing(meeting_id)
                
                self.logger.info(
                    "meeting_processing_completed",
                    meeting_id=meeting_id,
                    processing_time_seconds=timer.elapsed,
                    prd_id=result.prd.id,
                    tasks_created=len(result.tasks),
                    component="meeting_processor"
                )
                
                return result
                
            except Exception as e:
                self.logger.error(
                    "meeting_processing_failed",
                    meeting_id=meeting_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    component="meeting_processor",
                    exc_info=True
                )
                raise
    
    @contextmanager
    def _log_processing_context(self, meeting_id: str):
        """✅ OBSERVABILITY - Context manager para logging contextual."""
        self.logger = self.logger.bind(meeting_id=meeting_id)
        try:
            yield self.logger
        finally:
            self.logger = self.logger.unbind("meeting_id")
    
    @contextmanager
    def _measure_processing_time(self):
        """✅ OBSERVABILITY - Medición de tiempo de procesamiento."""
        class Timer:
            def __init__(self):
                self.start_time = time.time()
                self.elapsed = 0
        
        timer = Timer()
        try:
            yield timer
        finally:
            timer.elapsed = time.time() - timer.start_time
```

### 6.3. Testing Strategy

```python path=null start=null
import pytest
from unittest.mock import Mock, patch
from typing import Generator

# ✅ CLEAN CODE - Tests bien estructurados y descriptivos
class TestMeetingProcessor:
    """✅ TESTING - Suite de tests comprehensive."""
    
    @pytest.fixture
    def mock_transcription_service(self) -> Mock:
        """✅ TESTING - Mock para servicio de transcripción."""
        mock = Mock(spec=TranscriptionService)
        mock.transcribe.return_value = "Mock transcription content"
        return mock
    
    @pytest.fixture
    def meeting_processor(self, mock_transcription_service: Mock) -> MeetingProcessor:
        """✅ TESTING - Fixture para procesador con dependencias mockeadas."""
        return MeetingProcessor(
            transcription_service=mock_transcription_service,
            prd_generator=Mock()
        )
    
    def test_process_meeting_success_path(self, meeting_processor: MeetingProcessor):
        """✅ TESTING - Test del camino exitoso."""
        # Given
        meeting_url = "https://meet.google.com/test-meeting"
        
        # When
        result = meeting_processor.process_meeting_audio(meeting_url)
        
        # Then
        assert result.success is True
        assert result.prd is not None
        assert len(result.tasks) == 1
    
    def test_process_meeting_with_transcription_failure_should_retry(
        self, mock_transcription_service: Mock, meeting_processor: MeetingProcessor
    ):
        """✅ TESTING - Test de manejo de errores y reintentos."""
        # Given  
        mock_transcription_service.transcribe.side_effect = TranscriptionServiceException("Service unavailable")
        
        # When & Then
        with pytest.raises(TranscriptionFailedException):
            meeting_processor.process_meeting_audio("https://meet.google.com/test")
        
        # Verify retry behavior (RNF5.0: Max 3 intentos)
        assert mock_transcription_service.transcribe.call_count == 3
```

### 6.4. Configuration Management

```python path=null start=null
@dataclass
class ApplicationConfig:
    """
    ✅ CONFIGURATION - Configuración centralizada de la aplicación.
    
    Maneja toda la configuración siguiendo el principio de "Configuration as Code".
    """
    
    # Performance Configuration (RNF1.0)
    max_processing_time_seconds: int = 300  # 5 minutes
    max_retry_attempts: int = 3  # RNF5.0
    
    # Security Configuration (RNF2.0)
    secret_manager_type: str = "aws"
    
    @classmethod
    def from_environment(cls) -> 'ApplicationConfig':
        """
        ✅ 12-Factor App - Configuración desde variables de entorno.
        """
        required_vars = ['DATABASE_URL', 'REDIS_URL', 'DEEPGRAM_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ConfigurationException(f"Missing required variables: {missing_vars}")
        
        return cls(
            database_url=os.getenv('DATABASE_URL'),
            deepgram_api_key=os.getenv('DEEPGRAM_API_KEY'),
            # ... otros parámetros
        )
```

---

## 10. Resumen de Implementación TDD + Arquitectura

### 7.1. Checklist de Principios Aplicados con TDD

| Principio/Patrón | ✅ Con TDD | Beneficio del TDD |
|------------------|------------|-------------------|
| **SRP (Single Responsibility)** | ✅ | Tests específicos fuerzan responsabilidades claras |
| **OCP (Open/Closed)** | ✅ | Mocks facilitan extensión sin modificar código existente |
| **LSP (Liskov Substitution)** | ✅ | Tests con abstracciones validan comportamiento consistente |
| **ISP (Interface Segregation)** | ✅ | Mocks específicos evitan dependencias innecesarias |
| **DIP (Dependency Inversion)** | ✅ | TDD promueve naturalmente inyección de dependencias |
| **Factory Pattern** | ✅ | Tests definen comportamiento antes de implementar factory |
| **Strategy Pattern** | ✅ | TDD facilita intercambio de algoritmos via mocks |
| **Circuit Breaker** | ✅ | Tests validan estados y transiciones del circuito |
| **ACID Principles** | ✅ | Tests verifican propiedades transaccionales |
| **Clean Code** | ✅ | TDD fuerza nombres descriptivos y funciones pequeñas |

### 7.2. Flujo de Desarrollo TDD Recomendado

```mermaid
graph TD
    A[🔴 RED: Escribir test que falle] --> B[🟢 GREEN: Código mínimo que pase]
    B --> C[🔵 REFACTOR: Aplicar principios SOLID]
    C --> D{¿Más funcionalidad?}
    D -->|Sí| A
    D -->|No| E[✅ Feature completa]
    
    C --> F[Aplicar Clean Architecture]
    C --> G[Aplicar Design Patterns]
    C --> H[Validar ACID/Clean Code]
```

### 7.3. Scripts de Desarrollo TDD

```bash path=null start=null
#!/bin/bash
# ✅ TDD - Scripts para flujo de desarrollo

# Ejecutar tests en modo watch (TDD continuo)
tdd_watch() {
    echo "🔄 Iniciando TDD Watch Mode..."
    pytest --watch tests/ --verbose --tb=short
}

# Ejecutar ciclo TDD completo
tdd_cycle() {
    echo "🔴 RED: Ejecutando tests (deben fallar)..."
    pytest tests/ --tb=short
    
    echo "🟢 GREEN: Implementar código mínimo"
    echo "🔵 REFACTOR: Aplicar principios de arquitectura"
    
    echo "✅ Ejecutando tests finales..."
    pytest tests/ --verbose --cov=src/
}

# Validar cobertura de tests
validate_coverage() {
    echo "📊 Validando cobertura de tests..."
    pytest --cov=src/ --cov-report=html --cov-fail-under=80
    echo "Reporte HTML generado en htmlcov/"
}

# Ejecutar análisis de calidad
quality_check() {
    echo "🔍 Análisis de calidad de código..."
    
    # Formateo con Black
    black --check --diff src/ tests/
    
    # Imports con isort
    isort --check-only --diff src/ tests/
    
    # Linting con flake8
    flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203
    
    # Type checking con mypy
    mypy src/ --strict
    
    echo "✅ Análisis de calidad completado"
}
```

---

## 11. ⚠️ Advertencias Críticas sobre Implementación TDD

### Revisión Humana Obligatoria para TDD

**IMPORTANTE**: La metodología TDD con IA requiere supervisión humana especializada:

1. **Revisión de Tests**: Un desarrollador senior debe validar que los tests realmente definen el comportamiento correcto del negocio.

2. **Validación del Ciclo RED-GREEN-REFACTOR**: Verificar que cada paso del ciclo TDD se ejecuta correctamente y que el refactoring aplica principios arquitectónicos apropiados.

3. **Cobertura de Casos Edge**: Los tests generados por IA pueden no cubrir todos los casos límite críticos del dominio específico.

4. **Integración con Requisitos**: Validar que los tests TDD realmente verifican el cumplimiento de RF/RNF específicos del proyecto.

5. **Performance de Tests**: Verificar que la suite de tests se ejecuta en tiempo razonable para mantener el ciclo TDD ágil.

### Limitaciones Específicas de TDD + LLM

- **Sesgos en Tests**: Los tests pueden reflejar sesgos del modelo y no cubrir escenarios reales del negocio
- **Over-Testing**: Tendencia a generar tests excesivamente complejos o innecesarios
- **Acoplamiento Inadecuado**: Tests que se acoplan demasiado a la implementación en lugar de al comportamiento

### Proceso TDD Recomendado con IA

1. **Fase 1**: Definir comportamiento de negocio con stakeholders humanos
2. **Fase 2**: Generar tests iniciales con IA, revisar con experto de dominio
3. **Fase 3**: Aplicar ciclo RED-GREEN-REFACTOR con revisión continua
4. **Fase 4**: Validar cobertura y calidad con métricas reales

**El éxito del TDD requiere experiencia humana en diseño de tests, conocimiento del dominio de negocio y criterio técnico para balancear cobertura vs. mantenibilidad.**

⚠️ **Nota sobre TDD y Generación Automática**: Los tests generados automáticamente deben ser **siempre** revisados por un desarrollador experimentado antes de ser utilizados como base para el desarrollo. Un test mal diseñado puede llevar a implementaciones incorrectas que cumplan el test pero fallen en producción.