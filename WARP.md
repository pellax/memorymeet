# Proyecto Warp: Principios de Arquitectura y Buenas Prácticas

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Contexto del Proyecto

**M2PRD-001: Meet-Teams-to-PRD** es un sistema distribuido Python/JavaScript que transforma grabaciones de audio de reuniones en documentos PRD estructurados y tareas asignadas automáticamente. Utiliza una arquitectura de microservicios con orquestación centralizada (n8n/Make), procesamiento IA/NLP (Python), persistencia políglota (PostgreSQL/Redis/MongoDB) y despliegue híbrido (Serverless/Contenedores).

---

## 1. Principios de Diseño: SOLID y KISS

### 1.1. Single Responsibility Principle (SRP)

**Aplicación en M2PRD-001:**
- **Módulo IA/NLP**: Se enfoca exclusivamente en procesamiento de lenguaje natural
- **Extensión Chrome**: Responsabilidad única de capturar eventos de reuniones
- **Webhook Service**: Solo recibe y valida requests HTTP
- **Orquestador (n8n/Make)**: Únicamente coordina flujos de trabajo

**Implementación Práctica:**
```python path=null start=null
# ❌ VIOLACIÓN SRP - Clase con múltiples responsabilidades
class MeetingProcessor:
    def capture_audio(self): pass
    def transcribe_audio(self): pass
    def generate_prd(self): pass
    def assign_tasks(self): pass
    def send_notifications(self): pass

# ✅ CUMPLE SRP - Responsabilidades separadas
class AudioCaptureService:
    def capture_audio_from_meeting(self, meeting_url): pass

class TranscriptionService:
    def transcribe_audio(self, audio_file): pass

class PRDGenerationService:
    def generate_prd(self, transcription): pass

class TaskAssignmentService:
    def assign_tasks_to_roles(self, requirements): pass
```

### 1.2. Open/Closed Principle (OCP)

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

### 1.3. Clean Architecture Layers

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

## 2. Patrones de Diseño Aplicados

### 2.1. Factory Pattern para RF4.0 - Asignación Inteligente

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
```

### 2.2. Strategy Pattern para Diferentes Algoritmos de NLP

```python path=null start=null
class RequirementExtractionStrategy(ABC):
    @abstractmethod
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        pass

class SpacyRequirementExtractor(RequirementExtractionStrategy):
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        # ✅ STRATEGY - Implementación específica con spaCy
        doc = self.nlp(transcription)
        return self._process_entities(doc)

class OpenAIRequirementExtractor(RequirementExtractionStrategy):
    def extract_requirements(self, transcription: str) -> List[Requisito]:
        # ✅ STRATEGY - Implementación específica con OpenAI
        prompt = f"Extrae requisitos de: {transcription}"
        return self._parse_openai_response(self.client.chat.completions.create(...))
```

### 2.3. Circuit Breaker Pattern para RNF5.0 - Tolerancia a Fallos

```python path=null start=null
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
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
        except Exception as e:
            self._on_failure()
            raise e
```

## 3. Bases de Datos: Principios ACID

### 3.1. Implementación de Transacciones ACID

```python path=null start=null
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class DatabaseTransactionManager:
    """✅ ACID - Gestor de transacciones que garantiza propiedades ACID."""
    
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
    def save_meeting_with_prd_and_tasks(
        self, meeting: Reunion, prd: PRD, tasks: List[TareaAsignada]
    ) -> None:
        """✅ ACID - Operación atómica completa."""
        
        with self.db_manager.transaction() as session:
            # ✅ CONSISTENCY - Validaciones de integridad
            self._validate_meeting_data(meeting)
            self._validate_prd_data(prd)
            
            # ✅ ATOMICITY - Todo en una transacción
            session.add(meeting)
            session.add(prd)
            session.add_all(tasks)
            
            # ✅ ISOLATION - La transacción se ejecuta de forma aislada
            # ✅ DURABILITY - Los cambios persisten al hacer commit
```

## 4. Gestión de Calidad de Código

### 4.1. Testing Strategy

```python path=null start=null
import pytest
from unittest.mock import Mock, patch

# ✅ CLEAN CODE - Tests bien estructurados y descriptivos
class TestMeetingProcessor:
    """✅ TESTING - Suite de tests comprehensive."""
    
    @pytest.fixture
    def mock_transcription_service(self) -> Mock:
        """✅ TESTING - Mock para servicio de transcripción."""
        mock = Mock(spec=TranscriptionService)
        mock.transcribe.return_value = "Mock transcription content"
        return mock
    
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

### 4.2. Configuration Management

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

## 5. Resumen de Principios Aplicados

### 5.1. Checklist de Implementación

| Principio/Patrón | ✅ Implementado | Aplicación en M2PRD-001 |
|------------------|----------------|---------------------------|
| **SRP (Single Responsibility)** | ✅ | Cada servicio tiene una responsabilidad única |
| **OCP (Open/Closed)** | ✅ | Extensible vía PMSIntegrationFactory sin modificar código |
| **LSP (Liskov Substitution)** | ✅ | Jerarquía de Requisito permite sustitución |
| **ISP (Interface Segregation)** | ✅ | Interfaces específicas por responsabilidad |
| **DIP (Dependency Inversion)** | ✅ | Dependencias por abstracción con inversión de control |
| **Factory Pattern** | ✅ | RoleAssignmentFactory para RF4.0 - Asignación Inteligente |
| **Strategy Pattern** | ✅ | Múltiples algoritmos de NLP intercambiables |
| **Circuit Breaker** | ✅ | Protección para RNF5.0 - Tolerancia a Fallos |
| **ACID Principles** | ✅ | Transacciones atómicas con PostgreSQL |
| **Clean Architecture** | ✅ | Capas bien definidas con dependencias hacia adentro |

### 5.2. Mapeo a Requisitos del Proyecto

| Requisito | Principio/Patrón Aplicado | Implementación |
|-----------|---------------------------|----------------|
| **RF4.0 - Asignación Inteligente** | Factory Pattern | RoleAssignmentFactory con clasificadores |
| **RF5.0 - Integración PMS** | Open/Closed + Factory | PMSIntegrationFactory extensible (Jira, Trello, Linear) |
| **RNF1.0 - Rendimiento < 5min** | Circuit Breaker + Monitoring | Health checks y alertas de rendimiento |
| **RNF2.0 - Seguridad** | Configuration Management | Gestores de secretos externos |
| **RNF5.0 - Tolerancia a Fallos** | Circuit Breaker + Retry Pattern | Reintentos exponenciales |

---

# M2PRD-001: Meet-Teams-to-PRD

## 1. Descripción del Proyecto

El proyecto **Meet-Teams-to-PRD** (M2PRD-001) implementa un sistema de orquestación distribuida cuyo objetivo principal es transformar una grabación de audio de una reunión (Meet/Teams) en un borrador estructurado de **Product Requirements Document (PRD)** y tareas asignadas automáticamente en un sistema de gestión de proyectos (PMS).

La arquitectura se centra en la **Plataforma de Automatización (Workflow)** como el orquestador central que gestiona la lógica de negocio, las llamadas a servicios externos (Deepgram, Módulo IA/NLP, APIs de PMS) y el manejo de errores/reintentos (RNF5.0).

### **Componentes Clave:**

| Componente | Rol en el Sistema |
| :--- | :--- |
| **Extensión de Chrome** | Disparador inicial. Captura la URL de la reunión y envía la solicitud. |
| **Webhook** | Punto de entrada del sistema. Recibe la solicitud y activa el Flujo de Trabajo. |
| **Workflow (Orquestador)** | Gestiona la secuencia de procesamiento, desde la transcripción hasta la asignación de tareas. |
| **Deepgram** | Servicio externo de Transcripción. Transforma el Archivo de Audio en texto. |
| **Módulo IA/NLP** | Motor de Procesamiento de Requisitos. Analiza la Transcripción para generar Requisitos y el borrador de PRD. |
| **APIs de PMS** | Servicio para interactuar con el sistema de gestión de proyectos (Jira/Asana) para crear y asignar la Tarea Asignada. |

### **Objetos de Datos Centrales:**

* `Reunion`
* `ArchivoDeAudio`
* `Transcripcion`
* `Requisito` (Funcional o NoFuncional)
* `PRD` (Documento de Requisitos de Producto)
* `TareaAsignada`

## 2. Diagramas UML (Mermaid)

### 2.1. Diagrama de Casos de Uso

```mermaid
%% UML: Diagrama de Casos de Uso (Use Case Diagram)
graph TD
    subgraph system_boundary [Límite del Sistema: M2PRD-001 Workflow]
        UC1(Capturar ID de Reunión)
        UC2(Invocar Servicio de Transcripción)
        UC3(Generar Requisitos e Ítemes de PRD)
        UC4(Asignar Requisitos como Tareas)
        UC5(Notificar al PM)
        
        UC2 -- <<include>> --> UC1: Inicia el Flujo
        UC3 -- <<include>> --> UC2: Procesa la Transcripción
        UC4 -- <<include>> --> UC3: Usa los Requisitos Generados
    end
    
    actor_pm[Jefe de Producto (PM)] 
    actor_automation((Plataforma de Automatización))

    actor_pm --> UC1: Inicia Proceso
    actor_automation --> UC2: Orquesta Llamada
    actor_automation --> UC3: Orquesta Llamada
    actor_automation --> UC4: Orquesta Llamada
    
    %% Relación de Generalización (Hereda la capacidad de iniciar y recibir notificaciones)
    actor_pm --|> actor_automation: Administrador de Flujo
    
    UC5 --> actor_pm: Tarea y PRD Listos
```

### 2.2. Diagrama de Clases

```mermaid
%% UML: Diagrama de Clases (Class Diagram)
classDiagram
    direction LR
    
    class Reunion {
        - id_reunion: string
        - url_audio: string
        - + iniciarProcesamiento(url): bool
    }
    
    class ArchivoDeAudio {
        - sizeMB: float
        - + cargarDesdeURL(url): ArchivoDeAudio
    }
    
    class Transcripcion {
        - texto_crudo: string
        - - segundos: int
        - + analizarTexto(): Requisito[]
    }

    class Requisito {
        - + id_requisito: string
        - + tipo: (Funcional | NoFuncional)
        - - descripcion: string
        - - prioridad: (P0 | P1 | P2)
        - + generarTarea(): TareaAsignada
    }
    
    class PRD {
        - titulo: string
        - - fecha_creacion: date
        - + generarPDF(): void
    }
    
    class TareaAsignada {
        - + id_tarea: string
        - - pm_asignado: string
        - - estado: string
    }
    
    %% Relaciones:
    
    %% Composición (Rombo relleno) - Fuerte dependencia existencial
    Reunion "1" *-- "1" ArchivoDeAudio: contiene
    ArchivoDeAudio "1" *-- "1" Transcripcion: esGeneradaDe
    PRD "1" *-- "*" Requisito: contiene
    Requisito "1" *-- "1" TareaAsignada: asigna
    
    %% Asociación (Línea continua) - Dependencia lógica/funcional
    Transcripcion "1" -- "1" PRD: esFuentePara
```

### 2.3. Diagrama de Secuencia

```mermaid
%% UML: Diagrama de Secuencia (Sequence Diagram)
sequenceDiagram
    actor PM
    participant Extension
    participant Webhook
    participant Workflow
    participant Deepgram
    participant Modulo_IA as Modulo IA/NLP
    participant APIs_PMS
    
    title Escenario 1: Flujo Básico con Orquestación y Manejo de Errores (RNF5.0)

    PM->>Extension: 1. Click en 'Iniciar Captura' (RF1.0)
    activate Extension
    Extension->>Webhook: 2. POST /trigger (url_audio)
    deactivate Extension
    
    activate Webhook
    Webhook->>Workflow: 3. Iniciar Flujo
    deactivate Webhook
    
    activate Workflow
    Workflow->>Deepgram: 4. Llama a Transcribir (ArchivoDeAudio)
    
    loop Reintentos (RNF5.0: Max 3 veces)
        alt Transcripción Exitosa (RF2.0)
            Deepgram-->>Workflow: 5. Transcripción OK (Transcripcion)
            
            Workflow->>Modulo_IA: 6. Procesar(Transcripcion)
            
            alt Generación Exitosa (RF3.0)
                Modulo_IA-->>Workflow: 7. Requisitos OK (PRD, Requisito[])
                
                Workflow->>APIs_PMS: 8. Crear Tareas(Requisito[]) (RF4.0)
                APIs_PMS-->>Workflow: 9. Tareas Creadas (TareaAsignada[])
                
                Workflow->>PM: 10. Notificación: PRD y Tareas Listas
                deactivate Workflow
                
            else Generación Falla (RF3.0)
                Modulo_IA--xWorkflow: 7. Error de Procesamiento
                Workflow->>PM: 10. Notificación de Fallo Crítico
                break Falla Crítica
            end
        else Transcripción Falla
            Deepgram--xWorkflow: 5. Error de Servicio
            Workflow->>Workflow: 5.1. Esperar 1min y Reintentar
            
        end
    end
    
    opt Si Falla el último Reintento (RNF5.0)
        Workflow->>PM: 11. Notificación de Fallo de Transcripción
        deactivate Workflow
    end
```

## 3. Objetivos y Métricas (KPI)

### **Visión del Proyecto:**
Ser el puente de documentación sin fisuras entre la ideación conceptual y la implementación de ingeniería.

### **Metas Principales:**
1. **Reducir el tiempo de conversión** de "Reunión a Tarea Asignada" en un **70%**
2. **Garantizar una formulación de requisitos no ambigua**
3. **Lograr una tasa de precisión del 85%** en la asignación de roles

### **Métricas de Éxito (KPI):**

| KPI | Descripción | Objetivo |
| :--- | :--- | :--- |
| **Tasa de Adopción** | Usuarios activos de la extensión por mes | Crecimiento mensual sostenido |
| **Tiempo de Conversión** | Tiempo promedio de "Reunión a Tarea Asignada" (minutos) | Reducción del 70% vs. proceso manual |
| **Precisión de Asignación** | Porcentaje de precisión en la asignación automática de tareas | ≥ 85% |
| **NPS (Net Promoter Score)** | Satisfacción del usuario relacionado con la claridad del PRD generado | ≥ 8.0/10 |

## 4. Requisitos Detallados Adicionales

### **Requisitos Funcionales Refinados:**

**RF4.0 - Asignación Inteligente de Tareas:**
El flujo de trabajo DEBE clasificar el requisito y asignarlo automáticamente para los roles predefinidos:
- **Full Stack Developer**
- **Backend Developer** 
- **Frontend Developer**
- **Cloud Engineer**
- **UX Designer**

**RF5.0 - Integración con PMS:**
El flujo de trabajo DEBE ser capaz de crear tareas o historias de usuario en los siguientes sistemas:
- **Jira** (Atlassian API)
- **Trello** (Trello API)
- **Linear** (Linear API)

### **Requisitos No Funcionales Específicos:**

**RNF1.0 - Rendimiento:**
El proceso de generación de PRD y asignación DEBE completarse en **menos de 5 minutos** después de finalizar la reunión.

**RNF2.0 - Seguridad:**
El flujo de trabajo DEBE manejar tokens de API y credenciales de forma segura mediante:
- Cifrado de credenciales en reposo
- Uso de variables de entorno para tokens
- Rotación automática de credenciales cuando sea posible
- Auditoría de accesos a APIs externas

**RNF5.0 - Tolerancia a Fallos (Existente):**
Máximo 3 intentos de reintento con espera de 1 minuto entre intentos para servicios externos.

## 5. Hitos del Proyecto (Milestones)

### **Hito 1: Lanzamiento del MVP**
**Alcance:**
- Grabación desde Google Meet
- Disparo de Webhook
- Transcripción con Deepgram
- Generación de PRD básico (sin asignación automática)

**Entregables:**
- Extensión de Chrome funcional
- Webhook endpoint operativo
- Integración con Deepgram
- Generación básica de PRD

### **Hito 2: Workflow Completo**
**Alcance:**
- Implementación de Asignación Inteligente (RF4.0)
- Integración completa con Jira (RF5.0)
- Optimización de rendimiento (RNF1.0)

**Entregables:**
- Sistema de clasificación de requisitos por rol
- Integración funcional con Jira API
- Cumplimiento del objetivo de < 5 minutos (RNF1.0)
- Dashboard de métricas básicas

### **Hito 3: Integración Completa y Estabilización**
**Alcance:**
- Integración con Microsoft Teams
- Soporte para Trello y Linear (RF5.0)
- Estabilización del Workflow
- Implementación completa de seguridad (RNF2.0)

**Entregables:**
- Extensión compatible con Microsoft Teams
- APIs integradas: Jira, Trello, Linear
- Sistema de gestión segura de credenciales
- Documentación completa de usuario
- Métricas de KPI implementadas

# Arquitectura y Stack Tecnológico del Proyecto Meet-Teams-to-PRD

## 1. Principios Arquitectónicos

El proyecto M2PRD-001 adopta un modelo arquitectónico **distribuido y orientado a servicios ligeros** que prioriza:

- **Rapidez de Desarrollo**: Cada componente puede desarrollarse y desplegarse independientemente
- **Escalabilidad Horizontal**: Los servicios pueden escalar según la demanda específica
- **Desacoplamiento**: Fallos en un componente no comprometen todo el sistema
- **Flexibilidad Tecnológica**: Cada servicio utiliza el stack más apropiado para su función específica
- **Mantenibilidad**: Separación clara de responsabilidades facilita el mantenimiento y evolución

Esta arquitectura permite cumplir eficientemente con los requisitos de rendimiento (RNF1.0: < 5 minutos) y tolerancia a fallos (RNF5.0).

## 2. Stack Tecnológico Central 🛠️

| Componente | Stack Recomendado | Justificación RNF/RF Clave |
| :--- | :--- | :--- |
| **Frontend/Disparador (RF1.0)** | Extensión de Chrome con Vanilla JS / React Ligero | El énfasis está en ser un trigger de datos (disparo de Webhook) y no en el procesamiento. Una biblioteca ligera o JS nativo minimiza la huella y acelera el desarrollo/carga en el navegador. |
| **Backend/Motor de Procesamiento (RF3.0, RF4.0)** | Python (para Módulo IA/NLP) | Productividad y bibliotecas robustas (e.g., NLTK, spaCy, TensorFlow) para el procesamiento y clasificación de texto (Generación de PRD y Asignación Inteligente de Tareas). Este módulo se ejecutará como un servicio llamado por n8n/Make. |
| **Persistencia de Datos** | Redis (Cache de Sesión) y PostgreSQL/MongoDB (Metadata) | Persistencia Políglota: Redis para el manejo rápido de metadatos de sesión/tokens (RF1.0, RNF2.0). PostgreSQL (SQL) para metadatos estructurados del sistema (auditoría de flujos) o MongoDB (NoSQL) si la estructura de los logs es variable (Priorizando RNF de Escalabilidad). |
| **Orquestación/Flujo de Trabajo (RF1.0, RNF5.0)** | n8n / Make (Decisión del PRD) | Imprescindible (Prioridad 10/10): El PRD lo define como el Componente de Procesamiento Central. Gestiona las APIs (Deepgram, PMS) y la gestión de errores/reintentos (RNF5.0). |
| **Infraestructura/Despliegue** | Serverless (AWS Lambda/Google Cloud Functions) + Docker/Kubernetes (para n8n/Make) | Escalabilidad y Rendimiento (RNF1.0): El módulo IA/NLP se beneficia de la ejecución bajo demanda (Serverless). n8n/Make (si es autogestionado) debe ejecutarse en contenedores (Docker/K8s) para portabilidad y robustez. |

## 3. Componentes y Decisiones Clave

### 3.1. Backend/Motor de Procesamiento (Módulo IA/NLP) 🐍

**Lenguaje Elegido:** Python

**Justificación Fundamental:**
El corazón del proyecto M2PRD-001 es el **Procesamiento del Lenguaje Natural (PLN)** para la Generación de PRD (RF3.0) y la Asignación Inteligente de Tareas (RF4.0).

**Ventajas Técnicas:**
- **Estándar de facto** en Minería de Datos en la Web y PLN moderno
- **Ecosistema de bibliotecas especializado:**
  - `SciPy` - Computación científica y análisis estadístico
  - `Scikit-learn` - Algoritmos de machine learning para clasificación de requisitos
  - `Hugging Face Transformers` - Modelos de lenguaje preentrenados (BERT, GPT, etc.)
  - `NLTK` y `spaCy` - Análisis de texto y extracción de entidades
  - `TensorFlow`/`PyTorch` - Deep learning para modelos avanzados
- **Aceleración de desarrollo** mediante bibliotecas maduras y probadas
- **Versatilidad** para implementar modelos de clasificación y extracción de información
- **Amplia comunidad** y documentación especializada en IA/NLP

**Arquitectura de Ejecución:**
El flujo de trabajo en n8n/Make consumirá la transcripción y llamará a un **servicio serverless o microservicio** escrito en Python para realizar el procesamiento. Esta arquitectura mantiene la **rapidez de desarrollo** y la **versatilidad** operacional.

### 3.2. Persistencia de Datos: Persistencia Políglota 💾

**Enfoque Estratégico:**
Se adopta un enfoque de **persistencia políglota** para satisfacer las distintas necesidades de datos del sistema, optimizando cada tipo de almacenamiento según su propósito específico.

#### **PostgreSQL (Base de Datos Relacional)**
- **Uso Primario:** Metadata estructurada del sistema y **auditoría crítica** de flujos de trabajo
- **Justificación Detallada:**
  - **Integridad ACID** para datos críticos del sistema
  - **Esquemas relacionales** para trazabilidad completa de procesos
  - **Soporte robusto** para consultas complejas de auditoría (RNF5.0)
  - **Consistencia de datos** para configuraciones de usuarios y roles predefinidos (RF4.0)
- **Casos de Uso Específicos:**
  - Datos de usuario y configuraciones de extensión
  - Roles predefinidos para asignación inteligente (Full Stack, Backend, Frontend, Cloud, UX)
  - **Registro de auditoría** de flujos de trabajo (RNF5.0)
  - Métricas de KPI y seguimiento de rendimiento
  - Logs de ejecución estructurados

#### **Redis (Key-Value Store)**
- **Uso Primario:** Caché de alto rendimiento para datos temporales y credenciales
- **Justificación Detallada:**
  - **Alto rendimiento** y baja latencia para acceso frecuente (RNF2.0)
  - **Resiliencia** en el acceso a datos críticos
  - **Gestión segura** de tokens de API y credenciales (RNF2.0)
  - **Expiración automática** para metadatos de sesión de corta duración
- **Casos de Uso Específicos:**
  - Tokens de autenticación para APIs externas (Deepgram, Jira, Trello, Linear)
  - Credenciales temporales y rotación de secretos
  - Estado de sesiones activas durante procesamiento
  - Caché de respuestas de APIs para optimización
  - Metadatos de ejecución temporal

#### **MongoDB (Base de Datos NoSQL - Opcional)**
- **Uso Potencial:** Almacenamiento flexible para documentos de estructura variable
- **Justificación Detallada:**
  - **Flexibilidad de esquema** para PRDs generados con formato variable
  - **Escalabilidad horizontal** ante grandes volúmenes de datos
  - **Capacidad de indexación** para búsquedas complejas en transcripciones
- **Casos de Uso Potenciales:**
  - Almacenamiento de PRDs generados con estructura dinámica
  - Transcripciones procesadas y metadata asociada
  - Logs del sistema no estructurados
  - Documentos de requisitos con formato variable

### 3.3. Orquestación e Infraestructura: Escalabilidad y Monitoreo

#### **Orquestador Central: n8n / Make**
- **Restricción Arquitectónica:** Inamovible según PRD (Prioridad 10/10)
- **Justificación Estratégica:** 
  - **Simplifica la integración** con servicios externos (Deepgram, Jira/Trello/Linear API) (RF5.0)
  - **Gestión robusta de errores** y reintentos automáticos
  - **Interface visual** para diseño y debugging de flujos complejos
  - **Conectores nativos** para APIs de terceros
  - **Gestión declarativa de errores** sin código personalizado
- **Rol Crítico:** Coordinación de toda la lógica de negocio y mitigación del riesgo de dependencia del flujo de trabajo (RNF5.0)

#### **Infraestructura Híbrida Optimizada:**

**Serverless (AWS Lambda/Google Cloud Functions):**
- **Componente:** Módulo IA/NLP Python
- **Justificación Detallada:**
  - **Garantiza el Rendimiento (RNF1.0)** mediante escalado instantáneo
  - **Escalabilidad ante picos de demanda** (fin de reuniones Meet/Teams)
  - **Optimización de costos** con pago por ejecución únicamente
  - **Alta disponibilidad** sin gestión de infraestructura
  - **Aislamiento de recursos** para cada procesamiento
- **Ventajas Operacionales:**
  - Escalado automático según carga de trabajo
  - Sin overhead de mantenimiento de servidores
  - Cumplimiento automático de RNF1.0 (< 5 minutos)

**Contenedores (Docker/Kubernetes):**
- **Componente:** Orquestador n8n/Make (despliegue autogestionado)
- **Justificación Detallada:**
  - **Portabilidad completa** entre entornos (desarrollo, staging, producción)
  - **Robustez operacional** con control total sobre el flujo de trabajo
  - **Simplifica mantenimiento y monitoreo** del flujo crítico (RNF5.0)
  - **Gestión de recursos** predecible y controlada
- **Ventajas Estratégicas:**
  - Despliegue consistente en entornos robustos
  - Escalado horizontal controlado
  - Monitoring y observabilidad integrada
  - Recuperación rápida ante fallos

## 4. Seguridad y Gestión de Riesgos (RNFs)

### **Seguridad (RNF2.0): Gestión de Credenciales y Tokens**

#### **Restricción de Seguridad Crítica:**
La gestión de tokens **DEBE delegarse** a un gestor de secretos dedicado y **NO almacenarse directamente** en el código de la extensión o el flujo de trabajo.

#### **Implementación de Seguridad:**
- **Gestores de Secretos Recomendados:**
  - `AWS Secrets Manager` - Para infraestructura en AWS
  - `Azure Key Vault` - Para infraestructura en Azure
  - `HashiCorp Vault` - Para entornos híbridos o multi-cloud
- **Características de Seguridad:**
  - **Rotación automática** de tokens de API
  - **Cifrado en tránsito y reposo** para todas las credenciales
  - **Control de acceso granular** por servicio y usuario
  - **Auditoría completa** de accesos a credenciales

#### **Nota Importante sobre n8n/Make:**
Aunque n8n/Make ya gestiona credenciales de forma interna, se recomienda la integración con gestores de secretos externos para cumplir con estándares empresariales de seguridad.

### **Orquestación (RNF5.0): Mitigación del Riesgo Máximo**

#### **Identificación del Riesgo Crítico:**
El **riesgo de dependencia del flujo de trabajo es MÁXIMO**. La paralización del orquestador compromete todo el sistema.

#### **Justificación de la Elección n8n/Make:**
La elección de n8n/Make es **correcta y estratégica** porque:
- **Gestión de errores robusta** nativa
- **Sistema de reintentos** configurable y declarativo
- **Monitoreo integrado** de flujos de trabajo
- **Recuperación automática** ante fallos temporales

#### **Estrategias de Mitigación:**
- **Gestión de Errores Avanzada:**
  - Reintentos exponenciales configurables (máximo 3 intentos)
  - Timeout personalizado por servicio externo
  - Notificaciones automáticas en caso de fallo crítico
- **Circuit Breaker Pattern:**
  - Protección contra cascadas de fallos en servicios externos
  - Aislamiento de servicios problemáticos
  - Recuperación automática cuando el servicio se estabiliza
- **Monitoreo Proactivo:**
  - Alertas en tiempo real para servicios críticos
  - Métricas de salud de cada componente
  - Dashboards de observabilidad integrados
- **Procedimientos de Contingencia:**
  - Recuperación manual para fallos críticos del orquestador
  - Backups automáticos de configuraciones de flujo
  - Documentación de procedimientos de emergencia

## 6. Development Setup

### **Development Commands:**
```bash
# Chrome Extension Development
npm install
npm run build:dev
npm run watch

# Python IA/NLP Module
pip install -r requirements.txt
python -m pytest tests/
python app.py --dev

# Docker Containers (n8n self-hosted)
docker-compose up -d
docker-compose logs -f n8n

# Infrastructure as Code
terraform init
terraform plan
terraform apply
```

### **Environment Setup:**
```bash
# Required Environment Variables
export DEEPGRAM_API_KEY=<secret>
export OPENAI_API_KEY=<secret>
export JIRA_API_TOKEN=<secret>
export TRELLO_API_KEY=<secret>
export LINEAR_API_KEY=<secret>
```

## 7. Architecture Implementation Notes

### **Key Design Patterns:**
- **Orchestration Pattern**: Central workflow manages all service interactions
- **Event-Driven Architecture**: Webhook triggers initiate processing chains
- **Retry Pattern**: Implement exponential backoff for service failures
- **Circuit Breaker**: Protect against cascading failures in external services

### **Integration Points:**
- Deepgram API for audio transcription
- OpenAI/Claude API for requirement extraction
- Jira/Trello/Linear APIs for task creation
- Chrome Extension APIs for meeting capture
- Microsoft Teams API for expanded meeting support

### **Error Handling Requirements:**
- Maximum 3 retry attempts for transcription failures
- 1-minute wait between retry attempts
- Fallback notifications to PM on critical failures
- Comprehensive logging for debugging workflow issues
- Security audit trails for API access

## 7. Architecture Implementation Notes

### **Key Design Patterns:**
- **Orchestration Pattern**: Central workflow manages all service interactions
- **Event-Driven Architecture**: Webhook triggers initiate processing chains
- **Retry Pattern**: Implement exponential backoff for service failures
- **Circuit Breaker**: Protect against cascading failures in external services

### **Integration Points:**
- Deepgram API for audio transcription
- OpenAI/Claude API for requirement extraction
- Jira/Trello/Linear APIs for task creation
- Chrome Extension APIs for meeting capture
- Microsoft Teams API for expanded meeting support

### **Error Handling Requirements:**
- Maximum 3 retry attempts for transcription failures
- 1-minute wait between retry attempts
- Fallback notifications to PM on critical failures
- Comprehensive logging for debugging workflow issues
- Security audit trails for API access

---

---

## ⚠️ Advertencias Críticas sobre Implementación

### Revisión Humana Obligatoria

**IMPORTANTE**: Este documento contiene arquitecturas y patrones de diseño generados con asistencia de IA. Antes de implementar cualquier parte de esta arquitectura:

1. **Revisión de Arquitectura**: Un arquitecto de software senior debe revisar y validar todas las decisiones arquitectónicas propuestas.

2. **Validación de Patrones**: Los patrones de diseño deben ser evaluados en el contexto específico del proyecto para confirmar su aplicabilidad.

3. **Testing Exhaustivo**: Todos los componentes críticos requieren pruebas unitarias, de integración y de carga antes del despliegue.

4. **Revisión de Seguridad**: Un especialista en seguridad debe validar las implementaciones de RNF2.0 (gestión de credenciales y tokens).

5. **Validación de Rendimiento**: Los requisitos de RNF1.0 (< 5 minutos) deben ser validados con datos reales en entorno similar a producción.

### Limitaciones de LLMs

- **Alucinaciones**: El código y arquitecturas generadas pueden contener errores sutiles que parecen correctos
- **Contexto Limitado**: Algunos detalles específicos del proyecto pueden no haber sido considerados completamente
- **Evolución Tecnológica**: Las mejores prácticas y bibliotecas recomendadas deben ser validadas con versiones actuales

### Proceso de Implementación Recomendado

1. **Fase 1**: Implementar MVP con arquitectura simplificada
2. **Fase 2**: Validar patrones con métricas reales 
3. **Fase 3**: Refactorizar aplicando principios avanzados gradualmente
4. **Fase 4**: Optimización basada en datos de producción

**La implementación exitosa de estos principios requiere experiencia humana, juicio técnico y validación continua con métricas reales del sistema.**

⚠️ **Nota sobre la Generación de Código y Alucinaciones:** Cualquier código o *snippet* generado con ayuda de IA (LLMs) debe ser **siempre** verificado y probado exhaustivamente. El riesgo de 'alucinaciones' del modelo (respuestas que suenan correctas pero son falsas) es una limitación crucial. Se requiere una revisión humana obligatoria antes del despliegue.
