# 🚀 Quick Start - Sistema de Monitorización

## ✅ Inicio Rápido (5 minutos)

### 1️⃣ Instalar Dependencias

```bash
# Instalar nuevas dependencias de Prometheus
pip install -r requirements.txt
cd ia_module && pip install -r requirements.txt && cd ..
```

### 2️⃣ Levantar Stack Completo

```bash
# Levantar todos los servicios (incluye Prometheus + Grafana)
docker-compose up --build
```

### 3️⃣ Verificar que todo funciona

```bash
# Backend Gatekeeper metrics
curl http://localhost:8000/metrics

# IA/NLP Module metrics  
curl http://localhost:8003/metrics

# Prometheus UI
open http://localhost:9090

# Grafana Dashboard
open http://localhost:3001
# Login: admin / grafana_admin_123
```

---

## 📊 Accesos Rápidos

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin / grafana_admin_123 |
| **Backend Metrics** | http://localhost:8000/metrics | - |
| **IA/NLP Metrics** | http://localhost:8003/metrics | - |
| **Backend Docs** | http://localhost:8000/docs | - |
| **IA/NLP Docs** | http://localhost:8003/docs | - |

---

## 🧪 Ejecutar Tests de Métricas

```bash
# Todos los tests de métricas
pytest tests/test_metrics.py -v

# Solo backend
pytest tests/test_metrics.py::TestBackendMetrics -v

# Solo IA/NLP
pytest tests/test_metrics.py::TestIANLPMetrics -v
```

---

## 📊 Queries Prometheus de Ejemplo

Abre http://localhost:9090 y prueba estas queries:

```prometheus
# Ver todos los servicios activos
up

# Rate de requests por servicio
rate(http_requests_total[5m])

# Latencia P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Verificaciones de consumo (RF8.0)
sum by(result) (consumption_verifications_total)

# Requisitos extraídos (RF3.0)
sum by(type) (requirements_extracted_total)

# Tareas asignadas por rol (RF4.0)
sum by(role) (tasks_assigned_total)
```

---

## 📈 Dashboard en Grafana

1. Abre http://localhost:3001
2. Login: `admin` / `grafana_admin_123`
3. Navega a **Dashboards** → **M2PRD-001 - System Overview**
4. ¡Disfruta de las métricas en tiempo real! 🎉

---

## 🔍 Troubleshooting Rápido

### Servicios no arrancan

```bash
# Ver logs
docker-compose logs backend
docker-compose logs ia_module
docker-compose logs prometheus
docker-compose logs grafana
```

### Métricas no aparecen

```bash
# Verificar instrumentación
docker-compose logs backend | grep "Prometheus"
docker-compose logs ia_module | grep "Prometheus"

# Verificar que Prometheus scrapia
curl http://localhost:9090/api/v1/targets | jq
```

### Grafana no muestra datos

```bash
# Verificar datasource
curl http://localhost:3001/api/datasources

# Reiniciar Grafana
docker-compose restart grafana
```

---

## 📚 Documentación Completa

Para más detalles, ver: [`MONITORING_SETUP.md`](./MONITORING_SETUP.md)

---

**🎉 ¡Sistema de Monitorización Listo para Usar!**
