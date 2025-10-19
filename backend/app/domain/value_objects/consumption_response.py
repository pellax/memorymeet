# ================================================================================================
# 💰 CONSUMPTION RESPONSE VALUE OBJECTS - Objetos de Respuesta para Consumo
# ================================================================================================
# Value Objects para respuestas del servicio de consumo

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConsumptionUpdateResult:
    """
    ✅ TDD GREEN - Value Object para resultado de actualización de consumo.
    
    Encapsula el resultado de la operación actualizar_registro_consumo.
    """
    success: bool
    hours_consumed: float
    remaining_hours: float
    timestamp: datetime
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Verificar si la operación fue exitosa"""
        return self.success and self.error_message is None


@dataclass
class ConsumptionVerificationResponse:
    """
    ✅ API Response para verificación de consumo.
    
    Response específico para endpoints de la API.
    """
    authorized: bool
    user_id: str
    remaining_hours: float
    plan_name: str
    message: str
    consumption_percentage: float = 0.0
    
    @classmethod
    def from_verification_result(cls, result, user_id: str, plan_name: str):
        """Factory method para crear desde ConsumptionVerificationResult"""
        return cls(
            authorized=result.can_consume,
            user_id=user_id,
            remaining_hours=result.remaining_hours,
            plan_name=plan_name,
            consumption_percentage=result.consumption_percentage,
            message="Consumption authorized" if result.can_consume else "Insufficient hours"
        )


@dataclass  
class ConsumptionUpdateResponse:
    """
    ✅ API Response para actualización de consumo.
    
    Response específico para endpoints de actualización.
    """
    success: bool
    hours_consumed: float
    remaining_hours: float
    message: str
    timestamp: datetime
    
    @classmethod
    def from_update_result(cls, result: ConsumptionUpdateResult):
        """Factory method para crear desde ConsumptionUpdateResult"""
        return cls(
            success=result.success,
            hours_consumed=result.hours_consumed,
            remaining_hours=result.remaining_hours,
            timestamp=result.timestamp,
            message="Consumption updated successfully" if result.success else result.error_message
        )