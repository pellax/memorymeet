"""
✅ Configuration Management - Módulo IA/NLP M2PRD-001
Configuración centralizada siguiendo principios de 12-Factor App.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    ✅ Configuration as Code - Configuración type-safe de la aplicación.
    
    Todas las configuraciones se cargan desde variables de entorno
    siguiendo el principio de 12-Factor App.
    """
    
    # ================================
    # 🚀 APPLICATION SETTINGS
    # ================================
    app_name: str = "M2PRD-001 IA/NLP Module"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # ================================
    # 🌐 SERVER CONFIGURATION
    # ================================
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8003, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # ================================
    # 🔐 API KEYS (RNF2.0 - Secrets Management)
    # ================================
    deepgram_api_key: Optional[str] = Field(default=None, env="DEEPGRAM_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # ================================
    # 🤖 DEEPGRAM CONFIGURATION (RF2.0)
    # ================================
    deepgram_model: str = Field(default="nova-2", env="DEEPGRAM_MODEL")
    deepgram_language: str = Field(default="es", env="DEEPGRAM_LANGUAGE")
    deepgram_punctuate: bool = Field(default=True, env="DEEPGRAM_PUNCTUATE")
    deepgram_diarize: bool = Field(default=True, env="DEEPGRAM_DIARIZE")
    
    # ================================
    # 🧠 OPENAI CONFIGURATION (RF3.0, RF4.0)
    # ================================
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # ================================
    # 📊 NLP PROCESSING SETTINGS
    # ================================
    spacy_model: str = Field(default="es_core_news_sm", env="SPACY_MODEL")
    min_requirement_confidence: float = Field(default=0.6, env="MIN_REQUIREMENT_CONFIDENCE")
    max_requirements_per_meeting: int = Field(default=50, env="MAX_REQUIREMENTS_PER_MEETING")
    
    # ================================
    # ⚡ PERFORMANCE SETTINGS (RNF1.0)
    # ================================
    max_processing_time_seconds: int = Field(default=300, env="MAX_PROCESSING_TIME_SECONDS")
    max_audio_file_size_mb: int = Field(default=100, env="MAX_AUDIO_FILE_SIZE_MB")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # ================================
    # 🔄 CIRCUIT BREAKER SETTINGS (RNF5.0)
    # ================================
    circuit_breaker_failure_threshold: int = Field(default=3, env="CB_FAILURE_THRESHOLD")
    circuit_breaker_timeout_seconds: int = Field(default=60, env="CB_TIMEOUT_SECONDS")
    circuit_breaker_recovery_timeout: int = Field(default=30, env="CB_RECOVERY_TIMEOUT")
    
    # ================================
    # 🔍 LOGGING & OBSERVABILITY
    # ================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")
    enable_prometheus_metrics: bool = Field(default=True, env="ENABLE_PROMETHEUS_METRICS")
    
    # ================================
    # 🌐 EXTERNAL SERVICES URLs
    # ================================
    backend_api_url: Optional[str] = Field(default="http://backend:8000", env="BACKEND_API_URL")
    consumption_service_url: Optional[str] = Field(default="http://consumption-service:8002", env="CONSUMPTION_SERVICE_URL")
    
    # ================================
    # 🧪 TESTING CONFIGURATION
    # ================================
    testing: bool = Field(default=False, env="TESTING")
    mock_external_services: bool = Field(default=False, env="MOCK_EXTERNAL_SERVICES")
    
    class Config:
        """Configuración de Pydantic Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def validate_required_secrets(self) -> None:
        """
        ✅ Validation - Valida que los secretos críticos estén presentes.
        
        Raises:
            ValueError: Si faltan secretos requeridos en producción.
        """
        if self.environment == "production":
            missing_secrets = []
            
            if not self.deepgram_api_key:
                missing_secrets.append("DEEPGRAM_API_KEY")
            
            if not self.openai_api_key:
                missing_secrets.append("OPENAI_API_KEY")
            
            if missing_secrets:
                raise ValueError(
                    f"Missing required secrets in production: {', '.join(missing_secrets)}"
                )
    
    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo."""
        return self.environment.lower() in ["development", "dev", "local"]
    
    def is_production(self) -> bool:
        """Verifica si está en modo producción."""
        return self.environment.lower() in ["production", "prod"]
    
    def get_deepgram_config(self) -> dict:
        """
        ✅ Factory Method - Retorna configuración de Deepgram.
        """
        return {
            "model": self.deepgram_model,
            "language": self.deepgram_language,
            "punctuate": self.deepgram_punctuate,
            "diarize": self.deepgram_diarize
        }
    
    def get_openai_config(self) -> dict:
        """
        ✅ Factory Method - Retorna configuración de OpenAI.
        """
        return {
            "model": self.openai_model,
            "temperature": self.openai_temperature,
            "max_tokens": self.openai_max_tokens
        }
    
    def get_circuit_breaker_config(self) -> dict:
        """
        ✅ Factory Method - Retorna configuración de Circuit Breaker.
        """
        return {
            "failure_threshold": self.circuit_breaker_failure_threshold,
            "timeout": self.circuit_breaker_timeout_seconds,
            "recovery_timeout": self.circuit_breaker_recovery_timeout
        }


# ✅ Singleton Pattern - Instancia global de configuración
settings = Settings()

# Validar secretos al inicializar
if not settings.testing:
    try:
        settings.validate_required_secrets()
    except ValueError as e:
        if settings.is_production():
            raise e
        else:
            # En desarrollo, solo advertir
            print(f"⚠️ Warning: {str(e)}")
