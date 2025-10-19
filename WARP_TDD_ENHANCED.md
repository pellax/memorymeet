# Proyecto Warp: Principios de Arquitectura y Buenas Prácticas y Metodología TDD

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Contexto del Proyecto

[INICIO CONTEXTO DEL PROYECTO]
**M2PRD-001: Meet-Teams-to-PRD** es un sistema distribuido Python/JavaScript que transforma grabaciones de audio de reuniones en documentos PRD estructurados y tareas asignadas automáticamente. Utiliza una arquitectura de microservicios con orquestación centralizada (n8n/Make), procesamiento IA/NLP (Python), persistencia políglota (PostgreSQL/Redis/MongoDB) y despliegue híbrido (Serverless/Contenedores).

**Stack principal**: Python 3.11+, JavaScript/TypeScript, PostgreSQL, Redis, MongoDB, n8n/Make, AWS Lambda, Docker/Kubernetes.
**Dependencias clave**: FastAPI, SQLAlchemy, spaCy, OpenAI, Deepgram SDK, pytest, black, mypy.
[FIN CONTEXTO DEL PROYECTO]

---

## 1. Metodología de Desarrollo: TDD (Test-Driven Development)

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

## 2. Principios de Diseño: SOLID y KISS (Potenciados por TDD)

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

---

## 3. Estrategias de Arquitectura: Clean Architecture (Guiada por TDD)

### 3.1. TDD para Use Cases (Application Layer)

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

### 3.2. TDD para Domain Entities (Domain Layer)

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

---

## 4. Bases de Datos: Principios ACID (Validados con TDD)

### 4.1. TDD para Transacciones ACID

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

---

## 5. Gestión de Calidad de Código (Clean Code + TDD)

### 5.1. TDD para Clean Code Practices

```python path=null start=null
# ✅ TDD que promueve Clean Code
class TestMeetingAudioProcessor:
    """TDD para procesador con principios de Clean Code."""
    
    def test_should_process_valid_google_meet_url(self):
        """RED: Test con nombre descriptivo (Clean Code)."""
        # Given - Setup claro y expresivo
        processor = MeetingAudioProcessor(
            transcription_service=Mock(spec=TranscriptionService),
            audio_extractor=Mock(spec=AudioExtractor)
        )
        valid_google_meet_url = "https://meet.google.com/abc-defg-hij"
        
        # When - Acción clara
        result = processor.process_meeting_audio(valid_google_meet_url)
        
        # Then - Expectativas claras
        assert result.success is True
        assert result.processing_time_seconds < 300  # RNF1.0
    
    def test_should_reject_malformed_meeting_url_with_clear_message(self):
        """RED: Test para manejo de errores con mensajes claros."""
        # Given
        processor = MeetingAudioProcessor(Mock(), Mock())
        malformed_url = "not-a-valid-url"
        
        # When & Then
        with pytest.raises(InvalidMeetingUrlException) as exc_info:
            processor.process_meeting_audio(malformed_url)
        
        # Clean Code: Mensaje de error claro y específico
        assert "Invalid meeting URL format" in str(exc_info.value)
        assert malformed_url in str(exc_info.value)
    
    def test_should_handle_transcription_service_timeout_gracefully(self):
        """RED: Test para manejo robusto de timeouts."""
        # Given
        mock_transcription_service = Mock()
        mock_transcription_service.transcribe.side_effect = TimeoutError("Service timeout")
        
        processor = MeetingAudioProcessor(
            transcription_service=mock_transcription_service,
            audio_extractor=Mock()
        )
        
        # When
        result = processor.process_meeting_audio("https://meet.google.com/valid-url")
        
        # Then
        assert result.success is False
        assert "timeout" in result.error_message.lower()

# GREEN & REFACTOR: Implementación Clean Code
import re
import logging
from typing import Optional
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """✅ Clean Code - Clase de resultado clara y expresiva."""
    success: bool
    processing_time_seconds: float = 0.0
    error_message: Optional[str] = None
    transcription: Optional[str] = None

class MeetingAudioProcessor:
    """
    ✅ Clean Code + TDD - Procesador con nombres descriptivos y funciones pequeñas.
    
    Esta clase sigue principios de Clean Code:
    - Nombres descriptivos
    - Funciones pequeñas (una responsabilidad)
    - Manejo claro de errores
    - Logging apropiado
    """
    
    # Clean Code: Constantes con nombres descriptivos
    GOOGLE_MEET_PATTERN = r'https://meet\.google\.com/[a-z-]+'
    TEAMS_PATTERN = r'https://teams\.microsoft\.com/.+'
    ZOOM_PATTERN = r'https://zoom\.us/.+'
    
    MAX_PROCESSING_TIME_SECONDS = 300  # RNF1.0: 5 minutos
    
    def __init__(
        self, 
        transcription_service: TranscriptionService,
        audio_extractor: AudioExtractor,
        logger: Optional[logging.Logger] = None
    ):
        self.transcription_service = transcription_service
        self.audio_extractor = audio_extractor
        self.logger = logger or logging.getLogger(__name__)
    
    def process_meeting_audio(self, meeting_url: str) -> ProcessingResult:
        """
        ✅ Clean Code - Función principal con nombre descriptivo y responsabilidad clara.
        
        Args:
            meeting_url: URL de la reunión a procesar
            
        Returns:
            ProcessingResult: Resultado del procesamiento con detalles
            
        Raises:
            InvalidMeetingUrlException: Si la URL no es válida
        """
        start_time = time.time()
        
        try:
            # Clean Code: Validación extraída a método específico
            self._validate_meeting_url(meeting_url)
            
            # Clean Code: Procesamiento dividido en pasos claros
            audio_file = self._extract_audio_safely(meeting_url)
            transcription = self._transcribe_audio_safely(audio_file)
            
            processing_time = time.time() - start_time
            
            # Clean Code: Validación de requisitos no funcionales
            self._validate_processing_time(processing_time)
            
            self.logger.info(
                f"Meeting processed successfully in {processing_time:.2f}s",
                extra={'meeting_url': meeting_url, 'processing_time': processing_time}
            )
            
            return ProcessingResult(
                success=True,
                processing_time_seconds=processing_time,
                transcription=transcription
            )
            
        except Exception as e:
            # Clean Code: Manejo de errores específico y logging
            processing_time = time.time() - start_time
            error_message = self._format_error_message(e, meeting_url)
            
            self.logger.error(
                f"Meeting processing failed: {error_message}",
                extra={'meeting_url': meeting_url, 'error': str(e)}
            )
            
            return ProcessingResult(
                success=False,
                processing_time_seconds=processing_time,
                error_message=error_message
            )
    
    def _validate_meeting_url(self, url: str) -> None:
        """✅ Clean Code - Función pequeña con propósito específico."""
        if not url:
            raise InvalidMeetingUrlException("Meeting URL cannot be empty")
        
        if not self._is_supported_meeting_platform(url):
            raise InvalidMeetingUrlException(
                f"Unsupported meeting platform. URL: {url}. "
                f"Supported platforms: Google Meet, Microsoft Teams, Zoom"
            )
    
    def _is_supported_meeting_platform(self, url: str) -> bool:
        """✅ Clean Code - Función booleana con nombre claro."""
        supported_patterns = [
            self.GOOGLE_MEET_PATTERN,
            self.TEAMS_PATTERN, 
            self.ZOOM_PATTERN
        ]
        
        return any(re.match(pattern, url) for pattern in supported_patterns)
    
    def _extract_audio_safely(self, meeting_url: str) -> AudioFile:
        """✅ Clean Code - Extracción de audio con manejo de errores."""
        try:
            return self.audio_extractor.extract_audio(meeting_url)
        except Exception as e:
            raise AudioExtractionException(f"Failed to extract audio from {meeting_url}: {str(e)}")
    
    def _transcribe_audio_safely(self, audio_file: AudioFile) -> str:
        """✅ Clean Code - Transcripción con reintentos y manejo de errores."""
        max_retries = 3  # RNF5.0
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return self.transcription_service.transcribe(audio_file)
            except TimeoutError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise TranscriptionFailedException(
                        f"Transcription failed after {max_retries} attempts: {str(e)}"
                    )
                
                # Clean Code: Logging del reintento
                self.logger.warning(
                    f"Transcription timeout, retrying ({retry_count}/{max_retries})",
                    extra={'audio_file': audio_file.url, 'attempt': retry_count}
                )
                
                self._wait_before_retry(retry_count)
    
    def _wait_before_retry(self, retry_count: int) -> None:
        """✅ Clean Code - Función específica para espera entre reintentos."""
        wait_time = min(60, 2 ** retry_count)  # Exponential backoff, max 60s
        time.sleep(wait_time)
    
    def _validate_processing_time(self, processing_time: float) -> None:
        """✅ Clean Code - Validación de RNF1.0."""
        if processing_time > self.MAX_PROCESSING_TIME_SECONDS:
            self.logger.warning(
                f"Processing time exceeded limit: {processing_time}s > {self.MAX_PROCESSING_TIME_SECONDS}s",
                extra={'processing_time': processing_time, 'limit': self.MAX_PROCESSING_TIME_SECONDS}
            )
    
    def _format_error_message(self, error: Exception, meeting_url: str) -> str:
        """✅ Clean Code - Formateo consistente de mensajes de error."""
        error_type = type(error).__name__
        return f"{error_type} while processing {meeting_url}: {str(error)}"

# Clean Code: Excepciones específicas con nombres descriptivos
class InvalidMeetingUrlException(Exception):
    """Excepción para URLs de reunión inválidas."""
    pass

class AudioExtractionException(Exception):
    """Excepción para fallos en extracción de audio."""
    pass

class TranscriptionFailedException(Exception):
    """Excepción para fallos en transcripción tras reintentos."""
    pass
```

### 5.2. TDD para Configuration Management

```python path=null start=null
# ✅ TDD para gestión de configuración
class TestApplicationConfig:
    """TDD para configuración siguiendo 12-Factor App."""
    
    def test_should_load_config_from_environment_variables(self):
        """RED: Test para carga desde variables de entorno."""
        # Given - Mock de variables de entorno
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db',
            'REDIS_URL': 'redis://localhost:6379',
            'DEEPGRAM_API_KEY': 'test-key-123',
            'OPENAI_API_KEY': 'openai-key-456',
            'MAX_PROCESSING_TIME_SECONDS': '180'
        }):
            # When
            config = ApplicationConfig.from_environment()
            
            # Then
            assert config.database_url == 'postgresql://user:pass@localhost/db'
            assert config.deepgram_api_key == 'test-key-123'
            assert config.max_processing_time_seconds == 180
    
    def test_should_raise_error_for_missing_required_variables(self):
        """RED: Test para validación de variables requeridas."""
        # Given - Environment sin variables requeridas
        with patch.dict(os.environ, {}, clear=True):
            # When & Then
            with pytest.raises(ConfigurationException) as exc_info:
                ApplicationConfig.from_environment()
            
            assert "Missing required environment variables" in str(exc_info.value)
            assert "DATABASE_URL" in str(exc_info.value)
    
    def test_should_validate_configuration_constraints(self):
        """RED: Test para validación de configuración."""
        # Given - Configuración inválida
        config = ApplicationConfig(
            database_url="postgresql://localhost/test",
            max_processing_time_seconds=30,  # < 60 segundos (inválido)
            max_retry_attempts=10,           # > 5 (inválido)
            deepgram_api_key="test-key"
        )
        
        # When & Then
        with pytest.raises(ConfigurationException) as exc_info:
            config.validate()
        
        assert "Max processing time must be at least 60 seconds" in str(exc_info.value)

# GREEN: Implementación de Configuration Management
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApplicationConfig:
    """
    ✅ TDD - Configuración centralizada siguiendo 12-Factor App.
    
    Gestiona toda la configuración de la aplicación separando
    configuración del código y permitiendo diferentes configuraciones
    por ambiente.
    """
    
    # Database Configuration
    database_url: str
    redis_url: str = "redis://localhost:6379"
    mongodb_url: Optional[str] = None
    
    # External API Configuration
    deepgram_api_key: str = ""
    openai_api_key: str = ""
    jira_api_token: str = ""
    trello_api_key: str = ""
    linear_api_key: str = ""
    
    # Performance Configuration (RNF1.0)
    max_processing_time_seconds: int = 300  # 5 minutes
    transcription_timeout_seconds: int = 120
    max_retry_attempts: int = 3  # RNF5.0
    retry_backoff_base_seconds: int = 2
    
    # Security Configuration (RNF2.0)
    secret_manager_type: str = "aws"
    api_rate_limit_per_minute: int = 100
    
    @classmethod
    def from_environment(cls) -> 'ApplicationConfig':
        """
        ✅ TDD - Carga configuración desde variables de entorno.
        
        Implementa el patrón 12-Factor App para configuración.
        """
        # Variables requeridas
        required_vars = [
            'DATABASE_URL', 'DEEPGRAM_API_KEY', 'OPENAI_API_KEY'
        ]
        
        # Validar variables requeridas
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ConfigurationException(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        return cls(
            database_url=os.getenv('DATABASE_URL'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
            mongodb_url=os.getenv('MONGODB_URL'),
            deepgram_api_key=os.getenv('DEEPGRAM_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            jira_api_token=os.getenv('JIRA_API_TOKEN', ''),
            trello_api_key=os.getenv('TRELLO_API_KEY', ''),
            linear_api_key=os.getenv('LINEAR_API_KEY', ''),
            max_processing_time_seconds=int(os.getenv('MAX_PROCESSING_TIME_SECONDS', '300')),
            max_retry_attempts=int(os.getenv('MAX_RETRY_ATTEMPTS', '3')),
            secret_manager_type=os.getenv('SECRET_MANAGER_TYPE', 'aws')
        )
    
    def validate(self) -> None:
        """
        ✅ TDD - Validación de configuración cargada.
        
        Verifica que la configuración sea válida antes de inicializar
        la aplicación.
        """
        validation_errors = []
        
        # Validar tiempos de procesamiento (RNF1.0)
        if self.max_processing_time_seconds < 60:
            validation_errors.append("Max processing time must be at least 60 seconds")
        
        # Validar reintentos (RNF5.0)  
        if self.max_retry_attempts > 5:
            validation_errors.append("Max retry attempts should not exceed 5")
        
        if self.max_retry_attempts < 1:
            validation_errors.append("Max retry attempts must be at least 1")
        
        # Validar URL de base de datos
        if not self.database_url.startswith(('postgresql://', 'sqlite://')):
            validation_errors.append("Database URL must be PostgreSQL or SQLite")
        
        # Validar claves de API
        if not self.deepgram_api_key:
            validation_errors.append("Deepgram API key is required")
        
        if not self.openai_api_key:
            validation_errors.append("OpenAI API key is required")
        
        if validation_errors:
            raise ConfigurationException(
                f"Configuration validation failed: {'; '.join(validation_errors)}"
            )

class ConfigurationException(Exception):
    """Excepción específica para errores de configuración."""
    pass
```

---

## 6. Resumen de Implementación TDD + Arquitectura

### 6.1. Checklist de Principios Aplicados con TDD

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

### 6.2. Flujo de Desarrollo TDD Recomendado

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

### 6.3. Scripts de Desarrollo TDD

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

## ⚠️ Advertencias Críticas sobre Implementación TDD

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