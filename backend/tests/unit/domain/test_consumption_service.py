# ================================================================================================
# 🔴 TDD RED - TEST PARA SUBSCRIPTION CONSUMPTION SERVICE (RF8.0)
# ================================================================================================
# Tests unitarios que DEBEN FALLAR primero (TDD Red Phase)
# El servicio aún NO está completamente implementado, por lo que estos tests fallarán

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

# Import del servicio a testear
from app.domain.services.subscription_consumption_service import (
    SubscriptionConsumptionService,
    ConsumptionVerificationResult,
    ConsumptionResult
)

# Import de entidades
from app.domain.entities.user import User
from app.domain.entities.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlan
)

# Import de excepciones
from app.domain.exceptions.consumption_exceptions import (
    InsufficientHoursException,
    UserNotFoundException,
    SubscriptionNotFoundException,
    InvalidConsumptionException
)

# Import de interfaces (mocks)
from app.domain.repositories.subscription_repository import (
    SubscriptionRepository,
    UserRepository
)


class TestSubscriptionConsumptionService:
    """
    🔴 TDD RED PHASE - Tests para el Gatekeeper Service (RF8.0).
    
    Estos tests definen el comportamiento esperado del servicio crítico
    de control de consumo. Inicialmente DEBEN FALLAR porque la 
    implementación está incompleta o no existe.
    
    Metodología TDD:
    1. RED: Escribir test que falle
    2. GREEN: Implementación mínima que pase
    3. REFACTOR: Mejorar código manteniendo tests verdes
    """
    
    @pytest.fixture
    def mock_subscription_repository(self):
        """🎭 Mock del repositorio de suscripciones."""
        return Mock(spec=SubscriptionRepository)
    
    @pytest.fixture
    def mock_user_repository(self):
        """👤 Mock del repositorio de usuarios."""
        return Mock(spec=UserRepository)
    
    @pytest.fixture
    def consumption_service(self, mock_subscription_repository, mock_user_repository):
        """🔧 Fixture del servicio con dependencias mockeadas (DIP)."""
        return SubscriptionConsumptionService(
            subscription_repository=mock_subscription_repository,
            user_repository=mock_user_repository
        )
    
    @pytest.fixture
    def valid_user(self):
        """👤 Usuario válido para tests."""
        return User(
            id="user-123",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def active_subscription_with_hours(self):
        """💰 Suscripción activa con horas disponibles."""
        now = datetime.utcnow()
        return Subscription(
            id="sub-456",
            user_id="user-123",
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            monthly_hours_limit=100.0,
            available_hours=75.0,
            consumed_hours=25.0,
            monthly_price=99.99,
            created_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30)
        )
    
    # ========================================
    # 🔴 RED PHASE TESTS - DEBEN FALLAR
    # ========================================
    
    @pytest.mark.asyncio
    async def test_verificar_consumo_disponible_should_allow_when_user_has_sufficient_hours(
        self,
        consumption_service,
        mock_user_repository,
        mock_subscription_repository,
        valid_user,
        active_subscription_with_hours
    ):
        """
        🔴 TDD RED: Test que define el comportamiento principal (DEBE FALLAR).
        
        COMPORTAMIENTO ESPERADO:
        - Usuario válido con 75 horas disponibles
        - Requiere 10 horas para procesamiento
        - DEBE permitir el consumo
        - DEBE retornar información completa del estado
        
        Este test FALLARÁ porque:
        1. El servicio puede no estar completamente implementado
        2. Los mocks necesitan configuración específica
        3. La lógica de negocio puede tener bugs
        """
        # ===== GIVEN (Preparar mocks y datos) =====
        user_id = "user-123"
        required_hours = 10.0
        
        # Configurar mocks para simular comportamiento exitoso
        mock_user_repository.get_user_by_id = AsyncMock(return_value=valid_user)
        mock_subscription_repository.get_active_subscription_by_user_id = AsyncMock(
            return_value=active_subscription_with_hours
        )
        
        # ===== WHEN (Ejecutar función bajo test) =====
        result = await consumption_service.verificar_consumo_disponible(user_id, required_hours)
        
        # ===== THEN (Verificar comportamiento esperado) =====
        # 🎯 Verificaciones CRÍTICAS para RF8.0
        assert result.can_consume is True, "Debe permitir consumo cuando hay horas suficientes"
        assert result.user.id == user_id, "Debe retornar el usuario correcto"
        assert result.subscription.id == "sub-456", "Debe retornar la suscripción correcta"
        assert result.remaining_hours == 65.0, f"Debe calcular horas restantes: 75 - 10 = 65, got {result.remaining_hours}"
        assert result.consumption_percentage > 0, "Debe calcular porcentaje de consumo"
        
        # 🔍 Verificar que se llamaron los métodos correctos (behavior verification)
        mock_user_repository.get_user_by_id.assert_called_once_with(user_id)
        mock_subscription_repository.get_active_subscription_by_user_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_verificar_consumo_disponible_should_raise_insufficient_hours_when_not_enough(
        self,
        consumption_service,
        mock_user_repository,
        mock_subscription_repository,
        valid_user,
        active_subscription_with_hours
    ):
        """
        🔴 TDD RED: Test para rechazo por horas insuficientes (DEBE FALLAR).
        
        COMPORTAMIENTO ESPERADO:
        - Usuario con 75 horas disponibles
        - Requiere 100 horas (más de las disponibles)
        - DEBE lanzar InsufficientHoursException
        - DEBE incluir información detallada del error
        """
        # ===== GIVEN =====
        user_id = "user-123"
        required_hours = 100.0  # Más de las 75 disponibles
        
        mock_user_repository.get_user_by_id = AsyncMock(return_value=valid_user)
        mock_subscription_repository.get_active_subscription_by_user_id = AsyncMock(
            return_value=active_subscription_with_hours
        )
        
        # ===== WHEN & THEN (Verificar que lanza excepción) =====
        with pytest.raises(InsufficientHoursException) as exc_info:
            await consumption_service.verificar_consumo_disponible(user_id, required_hours)
        
        # 🔍 Verificar detalles de la excepción
        exception = exc_info.value
        assert exception.user_id == user_id
        assert exception.required_hours == required_hours
        assert exception.available_hours == 75.0
        assert exception.subscription_status == "active"
        assert "Insufficient hours" in str(exception)
    
    @pytest.mark.asyncio
    async def test_verificar_consumo_disponible_should_raise_user_not_found_when_user_missing(
        self,
        consumption_service,
        mock_user_repository,
        mock_subscription_repository
    ):
        """
        🔴 TDD RED: Test para usuario inexistente (DEBE FALLAR).
        
        COMPORTAMIENTO ESPERADO:
        - Usuario que no existe en el sistema
        - DEBE lanzar UserNotFoundException
        - NO debe llamar al repositorio de suscripciones
        """
        # ===== GIVEN =====
        user_id = "non-existent-user"
        required_hours = 10.0
        
        # Mock retorna None (usuario no encontrado)
        mock_user_repository.get_user_by_id = AsyncMock(return_value=None)
        
        # ===== WHEN & THEN =====
        with pytest.raises(UserNotFoundException) as exc_info:
            await consumption_service.verificar_consumo_disponible(user_id, required_hours)
        
        # 🔍 Verificar que no se llamó al repositorio de suscripciones
        mock_subscription_repository.get_active_subscription_by_user_id.assert_not_called()
        
        # 🔍 Verificar detalles de la excepción
        exception = exc_info.value
        assert exception.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_verificar_consumo_disponible_should_raise_subscription_not_found_when_no_active_subscription(
        self,
        consumption_service,
        mock_user_repository,
        mock_subscription_repository,
        valid_user
    ):
        """
        🔴 TDD RED: Test para usuario sin suscripción activa (DEBE FALLAR).
        
        COMPORTAMIENTO ESPERADO:
        - Usuario válido pero sin suscripción activa
        - DEBE lanzar SubscriptionNotFoundException
        """
        # ===== GIVEN =====
        user_id = "user-123"
        required_hours = 10.0
        
        mock_user_repository.get_user_by_id = AsyncMock(return_value=valid_user)
        # Mock retorna None (sin suscripción activa)
        mock_subscription_repository.get_active_subscription_by_user_id = AsyncMock(return_value=None)
        
        # ===== WHEN & THEN =====
        with pytest.raises(SubscriptionNotFoundException) as exc_info:
            await consumption_service.verificar_consumo_disponible(user_id, required_hours)
        
        # 🔍 Verificar detalles de la excepción
        exception = exc_info.value
        assert exception.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_verificar_consumo_disponible_should_raise_invalid_consumption_for_negative_hours(
        self,
        consumption_service,
        mock_user_repository,
        mock_subscription_repository
    ):
        """
        🔴 TDD RED: Test para validación de horas negativas (DEBE FALLAR).
        
        COMPORTAMIENTO ESPERADO:
        - Horas requeridas negativas o cero
        - DEBE lanzar InvalidConsumptionException
        - NO debe acceder a los repositorios
        """
        # ===== GIVEN =====
        user_id = "user-123"
        invalid_hours = -5.0  # Horas negativas
        
        # ===== WHEN & THEN =====
        with pytest.raises(InvalidConsumptionException) as exc_info:
            await consumption_service.verificar_consumo_disponible(user_id, invalid_hours)
        
        # 🔍 Verificar que no se accedió a los repositorios
        mock_user_repository.get_user_by_id.assert_not_called()
        mock_subscription_repository.get_active_subscription_by_user_id.assert_not_called()
        
        # 🔍 Verificar detalles de la excepción
        exception = exc_info.value
        assert exception.user_id == user_id
        assert exception.invalid_hours == invalid_hours
        assert "positive" in exception.reason.lower()


# ====================================
# 🧪 TEST FIXTURES ADICIONALES
# ====================================

@pytest.fixture
def subscription_with_no_hours():
    """💸 Suscripción sin horas disponibles."""
    now = datetime.utcnow()
    return Subscription(
        id="sub-no-hours",
        user_id="user-123",
        plan=SubscriptionPlan.BASIC,
        status=SubscriptionStatus.ACTIVE,
        monthly_hours_limit=10.0,
        available_hours=0.0,  # Sin horas disponibles
        consumed_hours=10.0,
        monthly_price=29.99,
        created_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30)
    )

@pytest.fixture  
def suspended_subscription():
    """🚫 Suscripción suspendida."""
    now = datetime.utcnow()
    return Subscription(
        id="sub-suspended",
        user_id="user-123", 
        plan=SubscriptionPlan.PROFESSIONAL,
        status=SubscriptionStatus.SUSPENDED,  # Suspendida
        monthly_hours_limit=100.0,
        available_hours=50.0,
        consumed_hours=50.0,
        monthly_price=99.99,
        created_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30)
    )