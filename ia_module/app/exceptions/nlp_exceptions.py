# ================================================================================================
# 🚨 NLP DOMAIN EXCEPTIONS - Excepciones específicas para IA/NLP (RF3.0, RF4.0)
# ================================================================================================
# Excepciones de dominio para el módulo de procesamiento de lenguaje natural

from typing import Optional, List


class NLPDomainException(Exception):
    """
    🔴 Base exception para todas las excepciones del dominio NLP.
    
    Representa violaciones de reglas de negocio específicas del procesamiento
    de lenguaje natural que no deben tratarse como errores técnicos.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "NLP_DOMAIN_ERROR"


class InvalidTranscriptionException(NLPDomainException):
    """
    📝 EXCEPCIÓN DE NEGOCIO - Transcripción inválida o vacía.
    
    Se lanza cuando la transcripción proporcionada no cumple con los
    requisitos mínimos para ser procesada por el módulo NLP.
    """
    
    def __init__(
        self, 
        message: str,
        transcription_length: int = 0,
        min_required_length: int = 10
    ):
        super().__init__(message, "INVALID_TRANSCRIPTION")
        self.transcription_length = transcription_length
        self.min_required_length = min_required_length


class ProcessingFailedException(NLPDomainException):
    """
    ⚠️ EXCEPCIÓN TÉCNICA - Fallo en el procesamiento NLP.
    
    Se lanza cuando ocurre un error durante el procesamiento de la transcripción
    que impide completar la extracción de requisitos.
    """
    
    def __init__(
        self,
        message: str,
        meeting_id: str = "",
        processing_stage: str = "unknown",
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message, "PROCESSING_FAILED")
        self.meeting_id = meeting_id
        self.processing_stage = processing_stage
        self.original_exception = original_exception


class RequirementExtractionException(NLPDomainException):
    """
    📋 EXCEPCIÓN DE EXTRACCIÓN - Error específico en extracción de requisitos.
    
    Se lanza cuando el algoritmo de extracción no puede identificar
    requisitos válidos en la transcripción proporcionada.
    """
    
    def __init__(
        self,
        message: str,
        extracted_count: int = 0,
        min_expected_count: int = 1,
        confidence_scores: Optional[List[float]] = None
    ):
        super().__init__(message, "REQUIREMENT_EXTRACTION_FAILED")
        self.extracted_count = extracted_count
        self.min_expected_count = min_expected_count
        self.confidence_scores = confidence_scores or []


class TaskAssignmentException(NLPDomainException):
    """
    👩‍💻 EXCEPCIÓN DE ASIGNACIÓN - Error en asignación inteligente (RF4.0).
    
    Se lanza cuando el algoritmo de asignación inteligente no puede
    determinar roles apropiados para los requisitos identificados.
    """
    
    def __init__(
        self,
        message: str,
        requirement_id: str = "",
        available_roles: Optional[List[str]] = None,
        assignment_confidence: float = 0.0
    ):
        super().__init__(message, "TASK_ASSIGNMENT_FAILED")
        self.requirement_id = requirement_id
        self.available_roles = available_roles or []
        self.assignment_confidence = assignment_confidence


class LanguageDetectionException(NLPDomainException):
    """
    🌐 EXCEPCIÓN DE IDIOMA - Error en detección de idioma.
    
    Se lanza cuando no se puede determinar el idioma de la transcripción
    o cuando el idioma detectado no está soportado.
    """
    
    def __init__(
        self,
        message: str,
        detected_language: str = "unknown",
        supported_languages: Optional[List[str]] = None,
        confidence_score: float = 0.0
    ):
        super().__init__(message, "LANGUAGE_DETECTION_FAILED")
        self.detected_language = detected_language
        self.supported_languages = supported_languages or ["en", "es"]
        self.confidence_score = confidence_score


class ModelLoadException(NLPDomainException):
    """
    🤖 EXCEPCIÓN TÉCNICA - Error en carga de modelo NLP.
    
    Se lanza cuando no se puede cargar o inicializar el modelo de
    procesamiento de lenguaje natural requerido.
    """
    
    def __init__(
        self,
        message: str,
        model_name: str = "",
        model_version: str = "",
        error_details: Optional[str] = None
    ):
        super().__init__(message, "MODEL_LOAD_FAILED")
        self.model_name = model_name
        self.model_version = model_version
        self.error_details = error_details


class InsufficientDataException(NLPDomainException):
    """
    📊 EXCEPCIÓN DE DATOS - Datos insuficientes para procesamiento.
    
    Se lanza cuando la transcripción es demasiado corta o no contiene
    suficiente información para realizar un procesamiento confiable.
    """
    
    def __init__(
        self,
        message: str,
        word_count: int = 0,
        sentence_count: int = 0,
        min_word_threshold: int = 50
    ):
        super().__init__(message, "INSUFFICIENT_DATA")
        self.word_count = word_count
        self.sentence_count = sentence_count
        self.min_word_threshold = min_word_threshold


class ConfigurationException(NLPDomainException):
    """
    ⚙️ EXCEPCIÓN DE CONFIGURACIÓN - Error en configuración del sistema NLP.
    
    Se lanza cuando la configuración del sistema NLP es inválida o está
    incompleta, impidiendo el funcionamiento correcto.
    """
    
    def __init__(
        self,
        message: str,
        config_key: str = "",
        expected_type: str = "",
        actual_value: Optional[str] = None
    ):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key
        self.expected_type = expected_type
        self.actual_value = actual_value


class PriorityDetectionException(NLPDomainException):
    """
    🎯 EXCEPCIÓN DE PRIORIDAD - Error en detección de prioridades.
    
    Se lanza cuando no se pueden determinar las prioridades de los
    requisitos basándose en el análisis del lenguaje natural.
    """
    
    def __init__(
        self,
        message: str,
        requirement_text: str = "",
        detected_keywords: Optional[List[str]] = None
    ):
        super().__init__(message, "PRIORITY_DETECTION_FAILED")
        self.requirement_text = requirement_text
        self.detected_keywords = detected_keywords or []


class APITimeout(NLPDomainException):
    """
    ⏱️ EXCEPCIÓN DE TIMEOUT - Procesamiento excedió tiempo límite.
    
    Se lanza cuando el procesamiento NLP tarda más tiempo del permitido,
    generalmente para evitar timeouts en la API REST.
    """
    
    def __init__(
        self,
        message: str,
        processing_time_seconds: float = 0.0,
        max_allowed_time: float = 30.0,
        meeting_id: str = ""
    ):
        super().__init__(message, "API_TIMEOUT")
        self.processing_time_seconds = processing_time_seconds
        self.max_allowed_time = max_allowed_time
        self.meeting_id = meeting_id


# ================================================================================================
# 🛠️ UTILITY FUNCTIONS - Funciones auxiliares para manejo de excepciones
# ================================================================================================

def create_processing_error(
    stage: str,
    original_error: Exception,
    meeting_id: str = "",
    context: Optional[dict] = None
) -> ProcessingFailedException:
    """
    🏭 Factory function para crear excepción de procesamiento.
    
    Simplifica la creación de excepciones con contexto completo.
    """
    context_str = f" Context: {context}" if context else ""
    message = f"Processing failed at stage '{stage}': {str(original_error)}{context_str}"
    
    return ProcessingFailedException(
        message=message,
        meeting_id=meeting_id,
        processing_stage=stage,
        original_exception=original_error
    )


def is_recoverable_error(exception: Exception) -> bool:
    """
    🔄 Determinar si un error es recuperable.
    
    Ayuda a decidir si se debe reintentar el procesamiento o fallar completamente.
    """
    recoverable_errors = [
        APITimeout,
        ModelLoadException,
        ConfigurationException
    ]
    
    return any(isinstance(exception, error_type) for error_type in recoverable_errors)


def get_user_friendly_message(exception: NLPDomainException) -> str:
    """
    👤 Obtener mensaje amigable para el usuario final.
    
    Convierte excepciones técnicas en mensajes comprensibles para usuarios.
    """
    user_messages = {
        "INVALID_TRANSCRIPTION": "La transcripción proporcionada está vacía o es demasiado corta para procesar.",
        "PROCESSING_FAILED": "Ocurrió un error durante el procesamiento. Por favor, inténtelo nuevamente.",
        "REQUIREMENT_EXTRACTION_FAILED": "No se pudieron extraer requisitos de esta transcripción. Verifique que contenga información técnica relevante.",
        "TASK_ASSIGNMENT_FAILED": "Se extrajeron los requisitos pero no se pudieron asignar tareas automáticamente.",
        "LANGUAGE_DETECTION_FAILED": "No se pudo detectar el idioma de la transcripción o el idioma no está soportado.",
        "MODEL_LOAD_FAILED": "Error técnico en el sistema de procesamiento. Contacte al administrador.",
        "INSUFFICIENT_DATA": "La transcripción es muy breve para realizar un análisis completo. Proporcione más contenido.",
        "API_TIMEOUT": "El procesamiento está tardando más de lo esperado. Intente con una transcripción más corta.",
        "PRIORITY_DETECTION_FAILED": "Se extrajeron los requisitos pero no se pudieron determinar las prioridades automáticamente."
    }
    
    return user_messages.get(
        exception.error_code,
        "Ocurrió un error inesperado durante el procesamiento."
    )