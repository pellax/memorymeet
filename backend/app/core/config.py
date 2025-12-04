# ================================================================================================
# ⚙️ CONFIGURATION MANAGEMENT - Variables de Entorno y Configuración
# ================================================================================================
# Gestión centralizada de configuración del sistema siguiendo 12-Factor App

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """
    ✅ Configuración centralizada de la aplicación.
    
    Sigue el principio de 12-Factor App: toda configuración viene de variables de entorno.
    Usa Pydantic para validación automática de tipos y valores.
    """
    
    # ================================================================================================
    # 🏗️ CONFIGURACIÓN GENERAL DE LA APLICACIÓN
    # ================================================================================================
    
    APP_NAME: str = "Consumption Service - Gatekeeper"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # ================================================================================================
    # 🌐 CONFIGURACIÓN DE RED
    # ================================================================================================
    
    HOST: str = Field(default="0.0.0.0", description="Host to bind the server")
    PORT: int = Field(default=8002, description="Port to bind the server")
    
    # CORS Origins
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000"
        ],
        description="Allowed CORS origins"
    )
    
    # ================================================================================================
    # 💾 CONFIGURACIÓN DE BASE DE DATOS
    # ================================================================================================
    
    DATABASE_URL: Optional[str] = Field(
        default="postgresql://user:password@localhost:5432/memorymeet_dev",
        description="PostgreSQL connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    
    # ================================================================================================
    # ⚡ CONFIGURACIÓN DE REDIS (Cache)
    # ================================================================================================
    
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")
    REDIS_TTL_SECONDS: int = Field(default=300, description="Default TTL for cache entries")
    
    # ================================================================================================
    # 🔗 CONFIGURACIÓN DE WEBHOOK N8N
    # ================================================================================================
    
    N8N_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="n8n webhook URL for workflow triggering"
    )
    N8N_API_KEY: Optional[str] = Field(
        default=None,
        description="n8n API key for authentication"
    )
    N8N_TIMEOUT_SECONDS: int = Field(
        default=30,
        ge=10,
        le=300,
        description="Timeout for n8n webhook calls"
    )
    N8N_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retries for failed webhook calls"
    )
    N8N_RETRY_DELAY_SECONDS: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Initial delay between retries (exponential backoff)"
    )
    
    # ================================================================================================
    # 🤖 CONFIGURACIÓN DE SERVICIO IA/NLP
    # ================================================================================================
    
    NLP_SERVICE_URL: str = Field(
        default="http://localhost:8003",
        description="URL of the IA/NLP microservice"
    )
    NLP_TIMEOUT_SECONDS: int = Field(default=60, description="Timeout for NLP service calls")
    
    # ================================================================================================
    # 🔐 CONFIGURACIÓN DE SEGURIDAD
    # ================================================================================================
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_MINUTES: int = Field(default=60, description="JWT token expiration in minutes")
    
    # API Key for n8n callbacks
    N8N_CALLBACK_API_KEY: Optional[str] = Field(
        default=None,
        description="API key that n8n must send in callback requests"
    )
    
    # Allowed IPs for callbacks (whitelist)
    ALLOWED_CALLBACK_IPS: List[str] = Field(
        default=["127.0.0.1", "::1"],
        description="Whitelist of IPs allowed to call callback endpoints"
    )
    
    # ================================================================================================
    # 📊 CONFIGURACIÓN DE LOGGING
    # ================================================================================================
    
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json or text"
    )
    
    # ================================================================================================
    # 🔄 CONFIGURACIÓN DE CIRCUIT BREAKER
    # ================================================================================================
    
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(
        default=5,
        description="Number of failures before opening circuit"
    )
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Timeout before attempting to close circuit"
    )
    
    # ================================================================================================
    # 💰 CONFIGURACIÓN DE NEGOCIO (SaaS)
    # ================================================================================================
    
    # Consumption limits
    DEFAULT_FREE_HOURS: float = Field(
        default=2.0,
        description="Default free hours for new users"
    )
    MAX_PROCESSING_HOURS_PER_REQUEST: float = Field(
        default=8.0,
        description="Maximum hours per single processing request"
    )
    
    # Stripe Configuration (for future payment integration)
    STRIPE_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Stripe secret key for payment processing"
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        description="Stripe webhook secret for signature verification"
    )
    
    # ================================================================================================
    # 📈 CONFIGURACIÓN DE MONITORING
    # ================================================================================================
    
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Port for metrics endpoint")
    
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    
    # ================================================================================================
    # 🧪 CONFIGURACIÓN DE TESTING
    # ================================================================================================
    
    TESTING: bool = Field(default=False, description="Enable testing mode")
    TEST_DATABASE_URL: Optional[str] = Field(
        default="sqlite:///./test.db",
        description="Test database URL"
    )
    
    # ================================================================================================
    # 🔧 VALIDATORS
    # ================================================================================================
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validar que el entorno sea válido."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validar nivel de logging."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parsear CORS origins desde string separado por comas."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_CALLBACK_IPS", pre=True)
    def parse_allowed_ips(cls, v):
        """Parsear lista de IPs permitidas."""
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",")]
        return v
    
    # ================================================================================================
    # 🛠️ COMPUTED PROPERTIES
    # ================================================================================================
    
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo."""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url_sync(self) -> Optional[str]:
        """Database URL para conexiones síncronas."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return None
    
    @property
    def n8n_webhook_configured(self) -> bool:
        """Verificar si n8n está configurado."""
        return self.N8N_WEBHOOK_URL is not None
    
    # ================================================================================================
    # 📋 CONFIGURATION SUMMARY
    # ================================================================================================
    
    def get_config_summary(self) -> dict:
        """Obtener resumen de configuración (sin secretos)."""
        return {
            "app_name": self.APP_NAME,
            "version": self.APP_VERSION,
            "environment": self.ENVIRONMENT,
            "host": self.HOST,
            "port": self.PORT,
            "debug": self.DEBUG,
            "n8n_configured": self.n8n_webhook_configured,
            "database_configured": self.DATABASE_URL is not None,
            "redis_configured": self.REDIS_URL is not None,
            "testing_mode": self.TESTING
        }
    
    class Config:
        """Configuración de Pydantic Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ================================================================================================
# 🏭 SINGLETON FACTORY
# ================================================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    ✅ Factory para obtener instancia singleton de configuración.
    
    Usa LRU cache para garantizar que solo se cree una instancia.
    """
    return Settings()


# ================================================================================================
# 🧪 TESTING UTILITIES
# ================================================================================================

def override_settings(**kwargs) -> Settings:
    """
    ✅ Override de settings para testing.
    
    Útil para tests unitarios y de integración.
    """
    return Settings(**kwargs)


# ================================================================================================
# 📊 CONFIGURATION VALIDATION
# ================================================================================================

def validate_production_config(settings: Settings) -> List[str]:
    """
    ✅ Validar configuración de producción.
    
    Retorna lista de errores/advertencias de configuración.
    """
    errors = []
    
    if settings.ENVIRONMENT == "production":
        # Validaciones críticas para producción
        if settings.DEBUG:
            errors.append("⚠️ DEBUG should be False in production")
        
        if settings.JWT_SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("🚨 CRITICAL: JWT_SECRET_KEY must be changed in production")
        
        if not settings.N8N_WEBHOOK_URL:
            errors.append("⚠️ N8N_WEBHOOK_URL is not configured")
        
        if not settings.N8N_CALLBACK_API_KEY:
            errors.append("🚨 CRITICAL: N8N_CALLBACK_API_KEY must be set in production")
        
        if not settings.DATABASE_URL or "localhost" in settings.DATABASE_URL:
            errors.append("🚨 CRITICAL: DATABASE_URL must point to production database")
        
        if not settings.SENTRY_DSN:
            errors.append("⚠️ SENTRY_DSN not configured - error tracking disabled")
        
        if "localhost" in settings.CORS_ORIGINS:
            errors.append("⚠️ CORS_ORIGINS contains localhost - security risk")
    
    return errors


# ================================================================================================
# 🚀 STARTUP CONFIGURATION CHECK
# ================================================================================================

def print_configuration_status():
    """
    ✅ Imprimir estado de configuración al inicio.
    
    Útil para debugging y verificación de deployment.
    """
    settings = get_settings()
    
    print("=" * 80)
    print("⚙️  CONFIGURATION STATUS")
    print("=" * 80)
    
    for key, value in settings.get_config_summary().items():
        icon = "✅" if value else "❌"
        if isinstance(value, bool):
            print(f"{icon} {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    # Validar configuración de producción
    if settings.is_production:
        print("\n" + "=" * 80)
        print("🔍 PRODUCTION VALIDATION")
        print("=" * 80)
        
        errors = validate_production_config(settings)
        if errors:
            print("\n⚠️  Configuration Issues Found:")
            for error in errors:
                print(f"   {error}")
        else:
            print("✅ All production checks passed")
    
    print("=" * 80 + "\n")


# Exportar para facilitar importación
__all__ = [
    "Settings",
    "get_settings",
    "override_settings",
    "validate_production_config",
    "print_configuration_status"
]
