# Proyecto Warp: Principios de Arquitectura y Buenas Prácticas

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
```python
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
```python
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

### 1.3. Liskov Substitution Principle (LSP)

**Aplicación en Jerarquía de Requisitos:**
```python
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

### 1.4. Interface Segregation Principle (ISP)

**Interfaces Específicas para Diferentes Responsabilidades:**
```python
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

### 1.5. Dependency Inversion Principle (DIP)

**Implementación con Inversión de Control:**
```python
# ✅ CUMPLE DIP - Depende de abstracciones, no de concreciones
class WorkflowOrchestrator:
    def __init__(
        self,
        transcription_service: TranscriptionService,  # Abstracción
        prd_generator: PRDGenerationService,         # Abstracción  
        pms_integration: PMSIntegration,             # Abstracción
        secret_manager: SecretManager                # Abstracción
    ):
        self.transcription_service = transcription_service
        self.prd_generator = prd_generator
        self.pms_integration = pms_integration
        self.secret_manager = secret_manager

    def process_meeting(self, meeting_data: dict) -> ProcessingResult:
        # ✅ Usa abstracciones, permite testing y flexibilidad
        api_key = self.secret_manager.get_secret("DEEPGRAM_API_KEY")
        transcription = self.transcription_service.transcribe(
            meeting_data['audio_url'], 
            api_key
        )
        prd = self.prd_generator.generate_prd(transcription)
        tasks = self.pms_integration.create_tasks(prd.requirements)
        return ProcessingResult(prd=prd, tasks=tasks)
```

### 1.6. KISS Principle (Keep It Simple, Stupid)

**Aplicación en Diseño de Componentes:**
```python
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

## 2. Estrategias de Arquitectura: Clean Architecture

### 2.1. Capas de Clean Architecture

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

### 2.2. Implementación de Casos de Uso

```python
# ✅ CLEAN ARCHITECTURE - Caso de uso bien definido
class ProcessMeetingUseCase:
    def __init__(
        self,
        meeting_repository: MeetingRepository,          # Puerto
        transcription_service: TranscriptionService,   # Puerto
        prd_generator: PRDGenerationService,           # Puerto
        task_repository: TaskRepository,               # Puerto
        event_publisher: EventPublisher                # Puerto
    ):
        self._meeting_repository = meeting_repository
        self._transcription_service = transcription_service
        self._prd_generator = prd_generator
        self._task_repository = task_repository
        self._event_publisher = event_publisher

    def execute(self, command: ProcessMeetingCommand) -> ProcessMeetingResponse:
        # 1. Validar entrada
        self._validate_command(command)
        
        # 2. Recuperar reunión
        meeting = self._meeting_repository.get_by_id(command.meeting_id)
        
        # 3. Procesar audio (delegado a servicio de dominio)
        transcription = self._transcription_service.transcribe(meeting.audio_url)
        
        # 4. Generar PRD
        prd = self._prd_generator.generate(transcription)
        
        # 5. Crear tareas
        tasks = self._create_tasks_from_requirements(prd.requirements)
        
        # 6. Persistir resultados
        self._task_repository.save_all(tasks)
        
        # 7. Publicar evento de finalización
        self._event_publisher.publish(
            MeetingProcessedEvent(
                meeting_id=command.meeting_id,
                prd_id=prd.id,
                task_ids=[task.id for task in tasks]
            )
        )
        
        return ProcessMeetingResponse(
            success=True,
            prd=prd,
            tasks=tasks,
            processing_time=self._calculate_processing_time()
        )
```

### 2.3. Entidades de Dominio

```python
# ✅ CLEAN ARCHITECTURE - Entidades ricas en comportamiento
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class RequirementType(Enum):
    FUNCTIONAL = "funcional"
    NON_FUNCTIONAL = "no_funcional"

class Priority(Enum):
    P0 = "P0"  # Crítico
    P1 = "P1"  # Alto
    P2 = "P2"  # Medio

@dataclass
class Requisito:
    """Entidad de dominio para requisitos."""
    id_requisito: str
    tipo: RequirementType
    descripcion: str
    prioridad: Priority
    
    def generar_tarea(self, assignee_resolver: 'AssigneeResolver') -> 'TareaAsignada':
        """Lógica de dominio para generar tareas."""
        assignee = assignee_resolver.resolve_assignee_for_requirement(self)
        
        return TareaAsignada(
            id_tarea=self._generate_task_id(),
            requisito_id=self.id_requisito,
            assignee=assignee,
            estado="PENDIENTE",
            prioridad=self.prioridad.value
        )
    
    def _generate_task_id(self) -> str:
        """Genera ID único para la tarea."""
        import uuid
        return f"TASK-{uuid.uuid4().hex[:8]}"

@dataclass  
class PRD:
    """Agregado raíz para PRD."""
    id: str
    titulo: str
    fecha_creacion: datetime
    requirements: List[Requisito]
    
    def add_requirement(self, requirement: Requisito) -> None:
        """Invariante de dominio: PRD debe tener al menos un requisito."""
        self.requirements.append(requirement)
    
    def generar_todas_las_tareas(self, assignee_resolver: 'AssigneeResolver') -> List['TareaAsignada']:
        """Lógica de dominio para generar todas las tareas."""
        if not self.requirements:
            raise DomainException("PRD debe tener al menos un requisito para generar tareas")
            
        return [req.generar_tarea(assignee_resolver) for req in self.requirements]
    
    def generar_pdf(self) -> bytes:
        """Generación del documento PDF."""
        # Lógica de dominio para generar PDF
        pass
```

### 2.4. Ports & Adapters (Hexagonal Architecture)

```python
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

## 3. Patrones de Diseño Aplicados

### 3.1. Factory Pattern

**Aplicación para RF4.0 - Asignación Inteligente:**
```python
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

### 3.2. Strategy Pattern

**Aplicación para Diferentes Algoritmos de NLP:**
```python
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

### 3.3. Observer Pattern

**Aplicación para Notificaciones (RF - Notificar al PM):**
```python
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

### 3.4. Circuit Breaker Pattern

**Aplicación para RNF5.0 - Tolerancia a Fallos:**
```python
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

## 4. Bases de Datos: Principios ACID

### 4.1. Implementación de Transacciones ACID

```python
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

### 4.2. Gestión de Concurrent Access

```python
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

## 5. Gestión de Calidad de Código

### 5.1. Clean Code Principles

```python
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

### 5.2. Logging y Observabilidad

```python
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

### 5.3. Testing Strategy

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
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
    def mock_prd_generator(self) -> Mock:
        """✅ TESTING - Mock para generador de PRD."""
        mock = Mock(spec=PRDGenerationService)
        mock_prd = PRD(
            id="test-prd-1",
            titulo="Test PRD",
            fecha_creacion=datetime.now(),
            requirements=[
                Requisito(
                    id_requisito="req-1",
                    tipo=RequirementType.FUNCTIONAL,
                    descripcion="Test requirement",
                    prioridad=Priority.P1
                )
            ]
        )
        mock.generate_prd.return_value = mock_prd
        return mock
    
    @pytest.fixture
    def meeting_processor(
        self, 
        mock_transcription_service: Mock, 
        mock_prd_generator: Mock
    ) -> MeetingProcessor:
        """✅ TESTING - Fixture para procesador con dependencias mockeadas."""
        return MeetingProcessor(
            transcription_service=mock_transcription_service,
            prd_generator=mock_prd_generator
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
        assert result.prd.titulo == "Test PRD"
        assert len(result.tasks) == 1
        assert result.tasks[0].requisito_id == "req-1"
    
    def test_process_meeting_with_invalid_url_should_raise_exception(
        self, 
        meeting_processor: MeetingProcessor
    ):
        """✅ TESTING - Test de validación de entrada."""
        # Given
        invalid_url = "not-a-valid-url"
        
        # When & Then
        with pytest.raises(InvalidMeetingUrlException) as exc_info:
            meeting_processor.process_meeting_audio(invalid_url)
        
        assert "Invalid meeting URL" in str(exc_info.value)
    
    def test_process_meeting_with_transcription_failure_should_retry_and_fail(
        self,
        mock_transcription_service: Mock,
        meeting_processor: MeetingProcessor
    ):
        """✅ TESTING - Test de manejo de errores y reintentos."""
        # Given  
        mock_transcription_service.transcribe.side_effect = TranscriptionServiceException("Service unavailable")
        meeting_url = "https://meet.google.com/test-meeting"
        
        # When & Then
        with pytest.raises(TranscriptionFailedException):
            meeting_processor.process_meeting_audio(meeting_url)
        
        # Verify retry behavior
        assert mock_transcription_service.transcribe.call_count == 3
    
    @patch('time.sleep')  # ✅ TESTING - Mock de sleep para tests rápidos
    def test_retry_logic_uses_exponential_backoff(
        self,
        mock_sleep: Mock,
        mock_transcription_service: Mock,
        meeting_processor: MeetingProcessor
    ):
        """✅ TESTING - Test de lógica de backoff exponencial."""
        # Given
        mock_transcription_service.transcribe.side_effect = [
            TranscriptionServiceException("Retry 1"),
            TranscriptionServiceException("Retry 2"), 
            "Success on third try"
        ]
        meeting_url = "https://meet.google.com/test-meeting"
        
        # When
        result = meeting_processor.process_meeting_audio(meeting_url)
        
        # Then
        assert result.success is True
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2)  # First retry: 2^1 = 2 seconds
        mock_sleep.assert_any_call(4)  # Second retry: 2^2 = 4 seconds

# ✅ TESTING - Tests de integración con base de datos
@pytest.mark.integration
class TestMeetingRepository:
    """✅ TESTING - Tests de integración para repositorio."""
    
    @pytest.fixture
    def db_session(self) -> Generator[Session, None, None]:
        """✅ TESTING - Fixture para sesión de BD de prueba."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_save_meeting_with_prd_and_tasks_atomically(self, db_session: Session):
        """✅ TESTING - Test de transacción atómica."""
        # Given
        meeting = Meeting(id="test-meeting", url_audio="http://example.com/audio.mp3")
        prd = PRD(id="test-prd", titulo="Test PRD", fecha_creacion=datetime.now())
        tasks = [
            TareaAsignada(id_tarea="task-1", pm_asignado="Backend Developer"),
            TareaAsignada(id_tarea="task-2", pm_asignado="Frontend Developer")
        ]
        
        repository = MeetingRepository(db_session)
        
        # When
        repository.save_meeting_with_prd_and_tasks(meeting, prd, tasks)
        
        # Then - Verify all data was saved
        saved_meeting = db_session.get(Meeting, "test-meeting")
        saved_prd = db_session.get(PRD, "test-prd") 
        saved_tasks = db_session.query(TareaAsignada).filter(
            TareaAsignada.prd_id == "test-prd"
        ).all()
        
        assert saved_meeting is not None
        assert saved_prd is not None
        assert len(saved_tasks) == 2
        assert saved_prd.reunion_id == "test-meeting"
```

---

## 6. Documentación y Mejores Prácticas

### 6.1. Code Documentation Standards

```python
from typing import Protocol, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ProcessingResult:
    """
    ✅ DOCUMENTATION - Resultado del procesamiento de una reunión.
    
    Esta clase encapsula el resultado completo del procesamiento de una reunión,
    incluyendo el PRD generado, las tareas asignadas y métricas de rendimiento.
    
    Attributes:
        success (bool): Indica si el procesamiento fue exitoso
        prd (PRD): Documento de requisitos de producto generado
        tasks (List[TareaAsignada]): Lista de tareas asignadas por rol
        processing_time_seconds (float): Tiempo total de procesamiento
        error_message (Optional[str]): Mensaje de error si el procesamiento falló
        
    Example:
        ```python
        result = ProcessingResult(
            success=True,
            prd=generated_prd,
            tasks=[task1, task2],
            processing_time_seconds=45.2
        )
        
        if result.success and result.meets_performance_requirement():
            notify_pm(result)
        ```
    """
    
    def __init__(
        self,
        success: bool,
        prd: Optional['PRD'] = None,
        tasks: Optional[List['TareaAsignada']] = None,
        processing_time_seconds: float = 0.0,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.prd = prd
        self.tasks = tasks or []
        self.processing_time_seconds = processing_time_seconds
        self.error_message = error_message
    
    def meets_performance_requirement(self) -> bool:
        """
        ✅ DOCUMENTATION - Verifica si cumple RNF1.0 (< 5 minutos).
        
        Returns:
            bool: True si el procesamiento tomó menos de 5 minutos (300 segundos)
            
        Note:
            Este método implementa la verificación del requisito no funcional
            RNF1.0 que especifica que el procesamiento debe completarse en
            menos de 5 minutos después de finalizar la reunión.
        """
        return self.processing_time_seconds < 300
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        ✅ DOCUMENTATION - Obtiene métricas de rendimiento del procesamiento.
        
        Returns:
            Dict[str, Any]: Diccionario con métricas de rendimiento:
                - processing_time_seconds: Tiempo total de procesamiento
                - tasks_created_count: Número de tareas creadas
                - meets_sla: Si cumple con el SLA de 5 minutos
                - efficiency_score: Puntuación de eficiencia (tasks/minute)
        """
        return {
            'processing_time_seconds': self.processing_time_seconds,
            'tasks_created_count': len(self.tasks),
            'meets_sla': self.meets_performance_requirement(),
            'efficiency_score': len(self.tasks) / max(self.processing_time_seconds / 60, 0.1)
        }
```

### 6.2. Configuration Management

```python
import os
from dataclasses import dataclass
from typing import Optional
import yaml

@dataclass
class ApplicationConfig:
    """
    ✅ CONFIGURATION - Configuración centralizada de la aplicación.
    
    Maneja toda la configuración de la aplicación siguiendo el principio
    de "Configuration as Code" y separando la configuración del código.
    """
    
    # Database Configuration
    database_url: str
    redis_url: str
    mongodb_url: Optional[str] = None
    
    # External API Configuration  
    deepgram_api_key: str
    openai_api_key: str
    jira_api_token: str
    trello_api_key: str
    linear_api_key: str
    
    # Performance Configuration (RNF1.0)
    max_processing_time_seconds: int = 300  # 5 minutes
    transcription_timeout_seconds: int = 120
    max_retry_attempts: int = 3
    retry_backoff_base_seconds: int = 2
    
    # Security Configuration (RNF2.0)
    secret_manager_type: str = "aws"  # aws, azure, hashicorp
    encryption_key: str = ""
    api_rate_limit_per_minute: int = 100
    
    # Feature Flags
    enable_mongodb_storage: bool = False
    enable_advanced_nlp: bool = True
    enable_slack_notifications: bool = False
    
    @classmethod
    def from_environment(cls) -> 'ApplicationConfig':
        """
        ✅ CONFIGURATION - Carga configuración desde variables de entorno.
        
        Esta función implementa el patrón "12-Factor App" para configuración,
        permitiendo diferentes configuraciones por ambiente sin cambiar código.
        
        Returns:
            ApplicationConfig: Instancia configurada desde variables de entorno
            
        Raises:
            ConfigurationException: Si faltan variables de entorno requeridas
        """
        required_vars = [
            'DATABASE_URL', 'REDIS_URL', 'DEEPGRAM_API_KEY', 
            'OPENAI_API_KEY', 'JIRA_API_TOKEN'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ConfigurationException(f"Missing required environment variables: {missing_vars}")
        
        return cls(
            database_url=os.getenv('DATABASE_URL'),
            redis_url=os.getenv('REDIS_URL'),
            mongodb_url=os.getenv('MONGODB_URL'),
            deepgram_api_key=os.getenv('DEEPGRAM_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            jira_api_token=os.getenv('JIRA_API_TOKEN'),
            trello_api_key=os.getenv('TRELLO_API_KEY', ''),
            linear_api_key=os.getenv('LINEAR_API_KEY', ''),
            max_processing_time_seconds=int(os.getenv('MAX_PROCESSING_TIME_SECONDS', '300')),
            secret_manager_type=os.getenv('SECRET_MANAGER_TYPE', 'aws'),
            enable_mongodb_storage=os.getenv('ENABLE_MONGODB_STORAGE', 'false').lower() == 'true',
            enable_advanced_nlp=os.getenv('ENABLE_ADVANCED_NLP', 'true').lower() == 'true'
        )
    
    @classmethod
    def from_yaml_file(cls, file_path: str) -> 'ApplicationConfig':
        """
        ✅ CONFIGURATION - Carga configuración desde archivo YAML.
        
        Útil para desarrollo local y testing con configuraciones complejas.
        """
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        return cls(**config_data)
    
    def validate(self) -> None:
        """
        ✅ CONFIGURATION - Valida la configuración cargada.
        
        Verifica que la configuración sea válida y consistente antes de
        inicializar la aplicación.
        
        Raises:
            ConfigurationException: Si la configuración es inválida
        """
        if self.max_processing_time_seconds < 60:
            raise ConfigurationException("Max processing time must be at least 60 seconds")
        
        if self.max_retry_attempts > 5:
            raise ConfigurationException("Max retry attempts should not exceed 5")
        
        if not self.database_url.startswith(('postgresql://', 'sqlite://')):
            raise ConfigurationException("Database URL must be PostgreSQL or SQLite")

# ✅ CONFIGURATION - Singleton para configuración global
class ConfigManager:
    _instance: Optional[ApplicationConfig] = None
    
    @classmethod
    def get_config(cls) -> ApplicationConfig:
        """Obtiene la configuración global de la aplicación (Singleton)."""
        if cls._instance is None:
            cls._instance = ApplicationConfig.from_environment()
            cls._instance.validate()
        return cls._instance
    
    @classmethod
    def set_config(cls, config: ApplicationConfig) -> None:
        """Establece la configuración global (útil para testing)."""
        config.validate()
        cls._instance = config
```

---

## 7. Implementación de Monitoreo y Alertas

### 7.1. Health Checks y Monitoring

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List
import asyncio
import aiohttp
from datetime import datetime, timedelta

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"  
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    """✅ MONITORING - Estado de salud de un componente."""
    component_name: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: datetime = datetime.utcnow()

class SystemHealthChecker:
    """
    ✅ MONITORING - Monitor de salud del sistema completo.
    
    Implementa health checks para todos los componentes críticos del sistema
    y proporciona una vista consolidada del estado de la aplicación.
    """
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.health_history: List[ComponentHealth] = []
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        ✅ MONITORING - Verifica la salud de todos los componentes.
        
        Returns:
            Dict con el estado de salud completo del sistema
        """
        checks = await asyncio.gather(
            self._check_database_health(),
            self._check_redis_health(),
            self._check_deepgram_health(),
            self._check_external_apis_health(),
            return_exceptions=True
        )
        
        component_healths = [check for check in checks if isinstance(check, ComponentHealth)]
        overall_status = self._determine_overall_health(component_healths)
        
        health_report = {
            'overall_status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {health.component_name: {
                'status': health.status.value,
                'response_time_ms': health.response_time_ms,
                'error_message': health.error_message
            } for health in component_healths},
            'system_metrics': await self._get_system_metrics()
        }
        
        return health_report
    
    async def _check_database_health(self) -> ComponentHealth:
        """✅ MONITORING - Verifica conectividad y rendimiento de BD."""
        start_time = time.time()
        
        try:
            # Simple query para verificar conectividad
            with self.db_manager.transaction() as session:
                result = session.execute(text("SELECT 1")).scalar()
                
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # > 1 segundo
                return ComponentHealth(
                    component_name="database",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="Database response time is slow"
                )
            
            return ComponentHealth(
                component_name="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time
            )
            
        except Exception as e:
            return ComponentHealth(
                component_name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def _check_deepgram_health(self) -> ComponentHealth:
        """✅ MONITORING - Verifica disponibilidad de servicio de transcripción."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.deepgram.com/v1/projects',
                    headers={'Authorization': f'Token {self.config.deepgram_api_key}'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return ComponentHealth(
                            component_name="deepgram",
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            component_name="deepgram",
                            status=HealthStatus.UNHEALTHY,
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return ComponentHealth(
                component_name="deepgram",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    def _determine_overall_health(self, component_healths: List[ComponentHealth]) -> HealthStatus:
        """✅ MONITORING - Determina el estado general del sistema."""
        if not component_healths:
            return HealthStatus.UNHEALTHY
        
        unhealthy_components = [h for h in component_healths if h.status == HealthStatus.UNHEALTHY]
        if unhealthy_components:
            return HealthStatus.UNHEALTHY
        
        degraded_components = [h for h in component_healths if h.status == HealthStatus.DEGRADED]
        if degraded_components:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """✅ MONITORING - Obtiene métricas del sistema."""
        return {
            'uptime_seconds': self._get_uptime_seconds(),
            'memory_usage_mb': self._get_memory_usage(),
            'active_processing_jobs': await self._get_active_jobs_count(),
            'average_response_time_ms': self._calculate_average_response_time(),
            'error_rate_percentage': self._calculate_error_rate()
        }
```

### 7.2. Alerting System

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    """✅ ALERTING - Estructura de una alerta."""
    id: str
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False
    metadata: Dict[str, Any] = None

class AlertingRule:
    """✅ ALERTING - Regla de alertas configurable."""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_minutes: int = 15
    ):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None

class AlertManager:
    """
    ✅ ALERTING - Gestor de alertas del sistema.
    
    Evalúa reglas de alertas, envía notificaciones y gestiona el ciclo
    de vida de las alertas del sistema.
    """
    
    def __init__(self, notification_services: List['NotificationService']):
        self.notification_services = notification_services
        self.active_alerts: Dict[str, Alert] = {}
        self.alerting_rules = self._setup_default_rules()
    
    def _setup_default_rules(self) -> List[AlertingRule]:
        """✅ ALERTING - Configuración de reglas por defecto."""
        return [
            # RNF1.0 - Performance Alert
            AlertingRule(
                name="processing_time_exceeded",
                condition=lambda metrics: metrics.get('average_response_time_ms', 0) > 300000,  # 5 min
                severity=AlertSeverity.HIGH,
                message_template="Processing time exceeded 5 minutes: {average_response_time_ms}ms",
                cooldown_minutes=5
            ),
            
            # Database Health Alert
            AlertingRule(
                name="database_unhealthy",
                condition=lambda health: health.get('components', {}).get('database', {}).get('status') == 'unhealthy',
                severity=AlertSeverity.CRITICAL,
                message_template="Database is unhealthy: {error_message}",
                cooldown_minutes=1
            ),
            
            # External API Alert
            AlertingRule(
                name="deepgram_unavailable",
                condition=lambda health: health.get('components', {}).get('deepgram', {}).get('status') == 'unhealthy',
                severity=AlertSeverity.HIGH,
                message_template="Deepgram service is unavailable: {error_message}",
                cooldown_minutes=10
            ),
            
            # Error Rate Alert
            AlertingRule(
                name="high_error_rate",
                condition=lambda metrics: metrics.get('error_rate_percentage', 0) > 10,
                severity=AlertSeverity.MEDIUM,
                message_template="Error rate is high: {error_rate_percentage}%",
                cooldown_minutes=30
            )
        ]
    
    async def evaluate_alerts(self, health_report: Dict[str, Any]) -> List[Alert]:
        """
        ✅ ALERTING - Evalúa todas las reglas de alertas.
        
        Args:
            health_report: Reporte de salud del sistema
            
        Returns:
            Lista de alertas nuevas generadas
        """
        new_alerts = []
        
        for rule in self.alerting_rules:
            if self._should_evaluate_rule(rule) and rule.condition(health_report):
                alert = self._create_alert_from_rule(rule, health_report)
                new_alerts.append(alert)
                self.active_alerts[alert.id] = alert
                
                # Enviar notificaciones
                await self._send_alert_notifications(alert)
        
        return new_alerts
    
    def _should_evaluate_rule(self, rule: AlertingRule) -> bool:
        """✅ ALERTING - Verifica si debe evaluar la regla (cooldown)."""
        if rule.last_triggered is None:
            return True
        
        cooldown_threshold = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
        return rule.last_triggered < cooldown_threshold
    
    def _create_alert_from_rule(self, rule: AlertingRule, context: Dict[str, Any]) -> Alert:
        """✅ ALERTING - Crea alerta a partir de regla y contexto."""
        import uuid
        
        alert_id = f"{rule.name}-{uuid.uuid4().hex[:8]}"
        message = rule.message_template.format(**context.get('system_metrics', {}))
        
        rule.last_triggered = datetime.utcnow()
        
        return Alert(
            id=alert_id,
            severity=rule.severity,
            component=rule.name,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=context
        )
    
    async def _send_alert_notifications(self, alert: Alert) -> None:
        """✅ ALERTING - Envía notificaciones de alerta."""
        for service in self.notification_services:
            try:
                await service.send_alert_notification(alert)
            except Exception as e:
                # Log error pero no fallar por notificaciones
                logger.error(f"Failed to send alert notification via {service.__class__.__name__}: {e}")

class SlackAlertNotificationService:
    """✅ ALERTING - Servicio de notificaciones por Slack."""
    
    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def send_alert_notification(self, alert: Alert) -> None:
        """Envía alerta a canal de Slack."""
        
        color_map = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning", 
            AlertSeverity.HIGH: "danger",
            AlertSeverity.CRITICAL: "danger"
        }
        
        payload = {
            "channel": self.channel,
            "username": "M2PRD Alert Bot",
            "icon_emoji": ":rotating_light:",
            "attachments": [{
                "color": color_map.get(alert.severity, "warning"),
                "title": f"{alert.severity.value.upper()} Alert: {alert.component}",
                "text": alert.message,
                "timestamp": alert.timestamp.timestamp(),
                "fields": [
                    {"title": "Component", "value": alert.component, "short": True},
                    {"title": "Severity", "value": alert.severity.value, "short": True}
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack notification failed: {response.status}")
```

---

## 8. Deployment y DevOps Practices

### 8.1. Infrastructure as Code

```yaml
# ✅ DEVOPS - docker-compose.yml para desarrollo local
version: '3.8'

services:
  # PostgreSQL para metadata y auditoría (ACID compliance)
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: m2prd_db
      POSTGRES_USER: m2prd_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U m2prd_user -d m2prd_db"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis para caché y gestión de tokens (RNF2.0)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # n8n para orquestación (Requirement PRD)
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n_db
      - DB_POSTGRESDB_USER=n8n_user
      - DB_POSTGRESDB_PASSWORD=${N8N_POSTGRES_PASSWORD}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - WEBHOOK_URL=http://localhost:5678
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/home/node/.n8n/workflows
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Python AI/NLP Service (Serverless locally with container)
  nlp-service:
    build:
      context: ./services/nlp
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://m2prd_user:${POSTGRES_PASSWORD}@postgres:5432/m2prd_db
      - REDIS_URL=redis://default:${REDIS_PASSWORD}@redis:6379
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./services/nlp:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Monitoring con Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

volumes:
  postgres_data:
  redis_data:
  n8n_data:
  prometheus_data:
```

### 8.2. CI/CD Pipeline

```yaml
# ✅ DEVOPS - .github/workflows/ci-cd.yml
name: M2PRD-001 CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"

jobs:
  # ✅ QUALITY ASSURANCE - Linting y análisis estático
  lint-and-format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Python dependencies
        run: |
          pip install black isort flake8 mypy pytest-cov
          pip install -r requirements.txt
      
      - name: Format code with Black
        run: black --check --diff services/nlp/
      
      - name: Sort imports with isort
        run: isort --check-only --diff services/nlp/
      
      - name: Lint with flake8
        run: |
          flake8 services/nlp/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 services/nlp/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      
      - name: Type check with mypy
        run: mypy services/nlp/ --strict

  # ✅ TESTING - Suite completa de tests
  test:
    runs-on: ubuntu-latest
    needs: lint-and-format
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/unit/ -v --cov=services/nlp --cov-report=xml --cov-report=html
      
      - name: Run integration tests  
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/integration/ -v --cov-append --cov=services/nlp --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  # ✅ SECURITY - Análisis de vulnerabilidades
  security-scan:
    runs-on: ubuntu-latest
    needs: lint-and-format
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run security scan with Bandit
        run: |
          pip install bandit[toml]
          bandit -r services/nlp/ -f json -o bandit-report.json
      
      - name: Run dependency vulnerability check
        run: |
          pip install safety
          safety check --json --output safety-report.json
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json

  # ✅ PERFORMANCE - Tests de rendimiento (RNF1.0)
  performance-test:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install performance testing dependencies
        run: |
          pip install -r requirements.txt
          pip install locust pytest-benchmark
      
      - name: Run performance benchmarks
        run: |
          pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json
      
      - name: Validate RNF1.0 (< 5 minutes processing time)
        run: |
          python scripts/validate_performance_requirements.py --benchmark-file=benchmark.json

  # ✅ DEPLOYMENT - Deploy to staging/production
  deploy:
    runs-on: ubuntu-latest
    needs: [test, security-scan, performance-test]
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          docker build -t m2prd-nlp-service:${{ github.sha }} services/nlp/
          docker tag m2prd-nlp-service:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/m2prd-nlp-service:${{ github.sha }}
          docker tag m2prd-nlp-service:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/m2prd-nlp-service:latest
          docker push ${{ secrets.ECR_REGISTRY }}/m2prd-nlp-service:${{ github.sha }}
          docker push ${{ secrets.ECR_REGISTRY }}/m2prd-nlp-service:latest
      
      - name: Deploy to AWS Lambda (Serverless)
        run: |
          # Deploy Python NLP service as Lambda function
          aws lambda update-function-code \
            --function-name m2prd-nlp-processor \
            --image-uri ${{ secrets.ECR_REGISTRY }}/m2prd-nlp-service:${{ github.sha }}
      
      - name: Update Lambda environment variables
        run: |
          aws lambda update-function-configuration \
            --function-name m2prd-nlp-processor \
            --environment Variables="{
              DATABASE_URL=${{ secrets.PROD_DATABASE_URL }},
              REDIS_URL=${{ secrets.PROD_REDIS_URL }},
              DEEPGRAM_API_KEY=${{ secrets.DEEPGRAM_API_KEY }},
              OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}
            }"
      
      - name: Run post-deployment health checks
        run: |
          python scripts/health_check.py --environment=production --timeout=300
      
      - name: Notify deployment success
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: '#deployments'
          text: "✅ M2PRD-001 deployed successfully to production"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 9. Resumen de Implementación

### 9.1. Checklist de Principios Aplicados

| Principio/Patrón | ✅ Implementado | Descripción de Aplicación |
|------------------|----------------|---------------------------|
| **SRP (Single Responsibility)** | ✅ | Cada clase tiene una responsabilidad única (AudioCaptureService, TranscriptionService, etc.) |
| **OCP (Open/Closed)** | ✅ | Extensible vía PMSIntegrationFactory sin modificar código existente |
| **LSP (Liskov Substitution)** | ✅ | Jerarquía de Requisito permite sustitución sin romper comportamiento |
| **ISP (Interface Segregation)** | ✅ | Interfaces específicas (AudioProcessable, TextAnalyzable, etc.) |
| **DIP (Dependency Inversion)** | ✅ | Dependencias por abstracción con inversión de control |
| **KISS Principle** | ✅ | Implementaciones directas sin complejidad innecesaria |
| **Clean Architecture** | ✅ | Capas bien definidas con dependencias hacia adentro |
| **Factory Pattern** | ✅ | RoleAssignmentFactory para RF4.0 - Asignación Inteligente |
| **Strategy Pattern** | ✅ | Múltiples algoritmos de NLP intercambiables |
| **Observer Pattern** | ✅ | Sistema de notificaciones para alertas del PM |
| **Circuit Breaker** | ✅ | Protección para RNF5.0 - Tolerancia a Fallos |
| **ACID Principles** | ✅ | Transacciones atómicas con PostgreSQL |
| **Ports & Adapters** | ✅ | Abstracciones para servicios externos (Deepgram, APIs PMS) |

### 9.2. Mapeo a Requisitos del Proyecto

| Requisito | Principio/Patrón Aplicado | Implementación |
|-----------|---------------------------|----------------|
| **RF4.0 - Asignación Inteligente** | Factory Pattern + Strategy Pattern | RoleAssignmentFactory con clasificadores intercambiables |
| **RF5.0 - Integración PMS** | Open/Closed + Factory Pattern | PMSIntegrationFactory extensible (Jira, Trello, Linear) |
| **RNF1.0 - Rendimiento < 5min** | Circuit Breaker + Monitoring | Health checks y alertas de rendimiento |
| **RNF2.0 - Seguridad** | Configuration Management + DIP | Gestores de secretos externos por inversión de dependencias |
| **RNF5.0 - Tolerancia a Fallos** | Circuit Breaker + Retry Pattern | Reintentos exponenciales con circuit breaker |

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