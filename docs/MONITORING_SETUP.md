# 📊 Sistema de Monitorización M2PRD-001

## ✅ Stack de Monitorización Implementado

**Stack**: Prometheus + Grafana  
**Status**: ✅ Completamente Funcional  
**Última Actualización**: 2025-12-05

---

## 🎯 Componentes Implementados

### 1. **Prometheus** (Recolección de Métricas)
- **Puerto**: 9090
- **Endpoint**: http://localhost:9090
- **Configuración**: `infra/monitoring/prometheus.yml`
- **Scrape Interval**: 15s (10s para servicios críticos)
- **Retención**: 15 días / 10GB

### 2. **Grafana** (Visualización)
- **Puerto**: 3001
- **Endpoint**: http://localhost:3001
- **Credenciales**: admin / ${GRAFANA_ADMIN_PASSWORD}
- **Datasource**: Prometheus (auto-provisionado)
- **Dashboards**: Auto-provisionados en `/var/lib/grafana/dashboards`

### 3. **Instrumentación FastAPI**
- **Librería**: `prometheus-fastapi-instrumentator==6.1.0`
- **Backend Gatekeeper**: http://localhost:8000/metrics
- **IA/NLP Module**: http://localhost:8003/metrics

---

## 📊 Métricas Disponibles

### **Backend Gatekeeper (RF8.0 - Crítico)**

#### Métricas HTTP Estándar
```prometheus
http_requests_total{job="backend-gatekeeper"}
http_request_duration_seconds{job="backend-gatekeeper"}
http_requests_inprogress{job="backend-gatekeeper"}
```

#### Métricas Custom de Negocio
```prometheus
# Verificaciones de consumo (CRÍTICO RF8.0)
consumption_verifications_total{result="authorized|rejected"}

# Horas procesadas por usuario
consumption_hours_processed_total{user_id="..."}

# Actualizaciones de consumo
consumption_updates_total{status="success|failed"}

# Requests activos
active_processing_requests

# Estado de suscripciones
user_subscription_status{user_id="...", plan_type="free|pro|enterprise"}

# Duración de autorizaciones (crítico para UX)
processing_authorization_duration_seconds
```

### **IA/NLP Module (RF3.0 & RF4.0)**

#### Métricas HTTP Estándar
```prometheus
http_requests_total{job="ia-nlp-module"}
http_request_duration_seconds{job="ia-nlp-module"}
http_requests_inprogress_nlp{job="ia-nlp-module"}
```

#### Métricas Custom de Procesamiento NLP
```prometheus
# Procesamiento NLP total
nlp_processing_total{status="success|failed", language="es|en|auto"}

# Requisitos extraídos (RF3.0)
requirements_extracted_total{type="functional|non_functional"}

# Tareas asignadas (RF4.0)
tasks_assigned_total{role="backend_developer|frontend_developer|..."}

# Duración de procesamiento NLP
nlp_processing_duration_seconds

# Scores de confianza
requirement_extraction_confidence_score
task_assignment_confidence_score

# Longitud de transcripciones
transcription_text_length_chars

# Requests NLP activos
active_nlp_processing_requests
```

---

## 🚀 Uso del Sistema

### **1. Levantar Stack Completo**
```bash
# Levantar todos los servicios con monitorización
docker-compose up --build

# Verificar que Prometheus está scraping
curl http://localhost:9090/targets

# Verificar que Grafana está activo
curl http://localhost:3001/api/health
```

### **2. Acceder a Interfaces**

#### Prometheus UI
```bash
# Abrir Prometheus
open http://localhost:9090

# Query de ejemplo: Rate de requests por servicio
rate(http_requests_total[5m])

# Query de ejemplo: P95 de latencia
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Grafana
```bash
# Abrir Grafana
open http://localhost:3001

# Login: admin / ${GRAFANA_ADMIN_PASSWORD}
# Dashboard: "M2PRD-001 - System Overview"
```

### **3. Ver Métricas Raw**

```bash
# Backend Gatekeeper
curl http://localhost:8000/metrics

# IA/NLP Module
curl http://localhost:8003/metrics

# Verificar métricas específicas
curl http://localhost:8000/metrics | grep consumption_verifications_total
curl http://localhost:8003/metrics | grep requirements_extracted_total
```

---

## 📈 Dashboards Disponibles

### **M2PRD-001 - System Overview**
**UID**: `m2prd-overview`  
**Ubicación**: `infra/monitoring/grafana/dashboards/m2prd-overview.json`

#### Paneles Incluidos:

1. **📊 Request Rate per Service**
   - Rate de requests/segundo para Backend y IA/NLP
   - Visualización: Time Series

2. **⏱️ Response Time P95**
   - Latencia P95 de ambos servicios
   - Visualización: Gauge
   - Thresholds: Verde (<0.5s), Amarillo (0.5-1s), Rojo (>1s)

3. **💰 Consumption Verifications (RF8.0)**
   - Total de verificaciones autorizadas vs rechazadas
   - Visualización: Time Series
   - Crítico para monitoreo de monetización

4. **📋 Requirements Extracted (RF3.0)**
   - Total de requisitos extraídos por tipo (funcional/no-funcional)
   - Visualización: Bar Chart

5. **👥 Tasks Assigned by Role (RF4.0)**
   - Distribución de tareas asignadas por rol de desarrollador
   - Visualización: Time Series

---

## 🧪 Tests TDD para Métricas

**Archivo**: `tests/test_metrics.py`

### Ejecutar Tests
```bash
# Tests de métricas del backend
pytest tests/test_metrics.py::TestBackendMetrics -v

# Tests de métricas IA/NLP
pytest tests/test_metrics.py::TestIANLPMetrics -v

# Tests de integración
pytest tests/test_metrics.py::TestMetricsIntegration -v

# Todos los tests de métricas
pytest tests/test_metrics.py -v
```

### Cobertura de Tests
- ✅ Existencia de endpoints `/metrics`
- ✅ Formato Prometheus válido
- ✅ Métricas HTTP estándar
- ✅ Métricas custom de negocio
- ✅ Performance del endpoint
- ✅ Unicidad de métricas por servicio

---

## 🔧 Configuración Avanzada

### **Añadir Nueva Métrica Custom**

#### Backend (Python)
```python
from prometheus_client import Counter, Histogram, Gauge

# Definir métrica
my_custom_metric = Counter(
    'my_custom_metric_total',
    'Descripción de la métrica',
    ['label1', 'label2']
)

# Usar en código
my_custom_metric.labels(label1='value1', label2='value2').inc()
```

### **Añadir Nuevo Dashboard**

1. Crear archivo JSON en `infra/monitoring/grafana/dashboards/`
2. Usar datasource `Prometheus`
3. Reiniciar Grafana o esperar auto-reload (10s)

### **Configurar Alertas (Futuro)**

Descomentar en `prometheus.yml`:
```yaml
rule_files:
  - "alerts/*.yml"
```

Crear `infra/monitoring/alerts/critical.yml`:
```yaml
groups:
  - name: m2prd_critical
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

---

## 📊 Queries Prometheus Útiles

### Performance
```prometheus
# P50, P95, P99 de latencia
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Negocio (RF8.0)
```prometheus
# Tasa de rechazo de consumo
rate(consumption_verifications_total{result="rejected"}[5m]) / 
rate(consumption_verifications_total[5m])

# Horas totales procesadas
sum(consumption_hours_processed_total)
```

### IA/NLP (RF3.0, RF4.0)
```prometheus
# Tasa de éxito de procesamiento NLP
rate(nlp_processing_total{status="success"}[5m]) / 
rate(nlp_processing_total[5m])

# Requisitos promedio por meeting
rate(requirements_extracted_total[5m]) / 
rate(nlp_processing_total{status="success"}[5m])

# Distribución de roles asignados
sum by(role) (tasks_assigned_total)
```

---

## 🔍 Troubleshooting

### Prometheus no scrapia targets

```bash
# Verificar configuración
docker exec -it m2prd_prometheus promtool check config /etc/prometheus/prometheus.yml

# Ver targets activos
curl http://localhost:9090/api/v1/targets

# Reiniciar Prometheus
docker-compose restart prometheus
```

### Grafana no muestra datos

```bash
# Verificar datasource
curl http://localhost:3001/api/datasources

# Verificar que Prometheus responde
curl http://prometheus:9090/api/v1/query?query=up

# Reiniciar Grafana
docker-compose restart grafana
```

### Métricas no aparecen

```bash
# Verificar que servicios exponen /metrics
curl http://localhost:8000/metrics
curl http://localhost:8003/metrics

# Ver logs de instrumentación
docker-compose logs backend | grep "Prometheus"
docker-compose logs ia_module | grep "Prometheus"
```

---

## 📚 Referencias

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **FastAPI Instrumentator**: https://github.com/trallnag/prometheus-fastapi-instrumentator
- **Prometheus Best Practices**: https://prometheus.io/docs/practices/naming/

---

## 🎯 Roadmap Futuro

- [ ] **Alertmanager**: Configurar alertas críticas (RNF1.0, RNF5.0)
- [ ] **Loki**: Añadir logs estructurados centralizados
- [ ] **Jaeger**: Distributed tracing para requests complejos
- [ ] **Exporters**: PostgreSQL, Redis, n8n metrics
- [ ] **Dashboards**: Crear dashboard específico por servicio
- [ ] **SLI/SLO**: Definir Service Level Indicators y Objectives

---

**✅ Sistema de Monitorización Completamente Funcional y Productivo**
