# ================================================================================================
# 🧪 TESTS TDD - Prometheus Metrics Exposition
# ================================================================================================
# Tests para verificar que los endpoints /metrics exponen métricas correctamente

import pytest
from fastapi.testclient import TestClient
import re


class TestBackendMetrics:
    """✅ TDD - Tests para métricas del Backend Gatekeeper."""
    
    def test_metrics_endpoint_exists(self):
        """RED: El endpoint /metrics debe existir."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        
        # Then
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
    
    def test_metrics_contain_http_requests_total(self):
        """RED: Las métricas deben incluir http_requests_total."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        assert "http_requests_total" in metrics_text
        assert 'job="backend-gatekeeper"' in metrics_text or "http_requests_total" in metrics_text
    
    def test_metrics_contain_consumption_custom_metrics(self):
        """RED: Las métricas deben incluir métricas custom de consumo (RF8.0)."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        # Verificar métricas custom de RF8.0
        assert "consumption_verifications_total" in metrics_text
        assert "consumption_hours_processed_total" in metrics_text
        assert "active_processing_requests" in metrics_text
    
    def test_metrics_format_is_valid_prometheus(self):
        """RED: Las métricas deben estar en formato Prometheus válido."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        # Formato básico de Prometheus: # HELP, # TYPE, metric_name value
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # Verificar que hay al menos una métrica con valor numérico
        metric_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(\{[^}]+\})?\s+[\d\.]+$'
        lines = metrics_text.split('\n')
        metric_lines = [line for line in lines if line and not line.startswith('#')]
        assert len(metric_lines) > 0, "Debe haber al menos una métrica expuesta"


class TestIANLPMetrics:
    """✅ TDD - Tests para métricas del módulo IA/NLP."""
    
    def test_nlp_metrics_endpoint_exists(self):
        """RED: El endpoint /metrics del módulo IA/NLP debe existir."""
        # Given
        from ia_module.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        
        # Then
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
    
    def test_nlp_metrics_contain_processing_metrics(self):
        """RED: Las métricas NLP deben incluir métricas de procesamiento (RF3.0, RF4.0)."""
        # Given
        from ia_module.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        # Métricas específicas de IA/NLP
        assert "nlp_processing_total" in metrics_text
        assert "requirements_extracted_total" in metrics_text
        assert "tasks_assigned_total" in metrics_text
        assert "nlp_processing_duration_seconds" in metrics_text
    
    def test_nlp_metrics_contain_confidence_scores(self):
        """RED: Las métricas NLP deben incluir scores de confianza."""
        # Given
        from ia_module.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        assert "requirement_extraction_confidence_score" in metrics_text
        assert "task_assignment_confidence_score" in metrics_text
    
    def test_nlp_metrics_contain_service_info(self):
        """RED: Las métricas deben incluir información del servicio."""
        # Given
        from ia_module.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        metrics_text = response.text
        
        # Then
        # Info metric con metadata del servicio
        assert "ia_nlp_service" in metrics_text
        # Verificar que contiene RF3.0+RF4.0 en alguna forma
        assert "RF3" in metrics_text or "requirement_extraction" in metrics_text


class TestMetricsIntegration:
    """✅ TDD - Tests de integración para el sistema de métricas."""
    
    def test_metrics_are_prometheus_scrapable(self):
        """RED: Las métricas deben ser compatibles con scraping de Prometheus."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        
        # When
        response = client.get("/metrics")
        
        # Then
        # Verificar headers correctos para Prometheus
        assert response.status_code == 200
        content_type = response.headers["content-type"]
        assert "text/plain" in content_type or "text/plain; charset=utf-8" in content_type
    
    def test_metrics_endpoint_does_not_affect_performance(self):
        """RED: El endpoint /metrics no debe afectar significativamente el rendimiento."""
        # Given
        from backend.app.main import app
        client = TestClient(app)
        import time
        
        # When - Medir tiempo de respuesta
        start_time = time.time()
        response = client.get("/metrics")
        response_time = time.time() - start_time
        
        # Then
        assert response.status_code == 200
        # El endpoint debe responder en menos de 1 segundo
        assert response_time < 1.0, f"Metrics endpoint too slow: {response_time:.3f}s"
    
    def test_both_services_expose_unique_metrics(self):
        """RED: Cada servicio debe exponer sus métricas específicas."""
        # Given
        from backend.app.main import app as backend_app
        from ia_module.app.main import app as nlp_app
        
        backend_client = TestClient(backend_app)
        nlp_client = TestClient(nlp_app)
        
        # When
        backend_metrics = backend_client.get("/metrics").text
        nlp_metrics = nlp_client.get("/metrics").text
        
        # Then
        # Backend debe tener métricas de consumo
        assert "consumption_verifications_total" in backend_metrics
        assert "consumption_verifications_total" not in nlp_metrics
        
        # NLP debe tener métricas de procesamiento
        assert "requirements_extracted_total" in nlp_metrics
        assert "requirements_extracted_total" not in backend_metrics


# ================================================================================================
# 🎯 PYTEST FIXTURES
# ================================================================================================

@pytest.fixture
def backend_client():
    """Fixture para cliente de test del backend."""
    from backend.app.main import app
    return TestClient(app)


@pytest.fixture
def nlp_client():
    """Fixture para cliente de test del módulo NLP."""
    from ia_module.app.main import app
    return TestClient(app)
