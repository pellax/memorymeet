# 🐳 Docker Quick Start Guide - M2PRD-001 SaaS

## Resumen

¡Ahora TODO el sistema está dockerizado! Puedes levantar el entorno completo con un solo comando.

---

## 🚀 Inicio Rápido (3 Opciones)

### Opción 1: Usando Makefile (Recomendado) ⭐

```bash
# Ver todos los comandos disponibles
make help

# Iniciar todo (PostgreSQL + Redis + Mock n8n + Gatekeeper)
make up

# Ver logs en tiempo real
make logs

# Detener todo
make down
```

### Opción 2: Usando docker-compose directamente

```bash
# Iniciar todo
docker-compose -f docker-compose.dev.yml up --build -d

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f

# Detener
docker-compose -f docker-compose.dev.yml down
```

### Opción 3: Usando docker-compose.yml (Completo con n8n real, Prometheus, Grafana)

```bash
# Iniciar todo el stack completo
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

---

## 📦 ¿Qué Se Levanta?

### Con `docker-compose.dev.yml` (Desarrollo Rápido)

```
✅ PostgreSQL (puerto 5432)     - Base de datos ACID
✅ Redis (puerto 6379)           - Cache y sesiones
✅ Mock n8n (puerto 5678)        - Simula n8n sin configurarlo
✅ Gatekeeper (puerto 8002)      - Backend de consumo
```

### Con `docker-compose.yml` (Stack Completo)

```
✅ PostgreSQL
✅ Redis  
✅ n8n real (puerto 5678)        - Workflow real
✅ Gatekeeper (puerto 8000)
✅ IA/NLP Module (puerto 8003)   - Si está implementado
✅ Prometheus (puerto 9090)      - Métricas
✅ Grafana (puerto 3001)         - Dashboards
```

---

## 🎯 Comandos Útiles del Makefile

### Gestión de Servicios

```bash
make up              # 🚀 Iniciar todos los servicios
make down            # 🛑 Detener todos los servicios
make restart         # 🔄 Reiniciar todos los servicios
make status          # 📊 Ver estado y URLs
make logs            # 📊 Ver logs de todos
make logs-gatekeeper # 📊 Solo logs del Gatekeeper
make logs-mock       # 📊 Solo logs del Mock n8n
```

### Building y Limpieza

```bash
make build           # 🔨 Reconstruir imágenes
make clean           # 🧹 Limpiar contenedores y volúmenes
make prune           # 🧹 Limpieza completa del sistema Docker
```

### Testing

```bash
make test            # 🧪 Ejecutar tests
make test-cov        # 📊 Tests con coverage
```

### Debugging

```bash
make shell-gatekeeper # 🐚 Shell en el contenedor
make shell-postgres   # 🐚 psql en PostgreSQL
make shell-redis      # 🐚 redis-cli
make health           # 🏥 Health check de servicios
```

### Monitoring

```bash
make ps              # 📋 Listar contenedores
make images          # 📦 Listar imágenes
make volumes         # 💾 Listar volúmenes
make watch           # 👀 Monitorear en tiempo real
```

---

## 📍 URLs Disponibles

Una vez levantado el sistema:

```
🧪 Mock n8n Server:
   • http://localhost:5678
   • http://localhost:5678/health
   • http://localhost:5678/webhook/process-meeting

💰 Gatekeeper Backend:
   • http://localhost:8002
   • http://localhost:8002/docs (Swagger UI)
   • http://localhost:8002/redoc
   • http://localhost:8002/health

💾 PostgreSQL:
   • localhost:5432
   • User: memorymeet
   • Password: dev_password_change_in_prod
   • Database: memorymeet_dev

⚡ Redis:
   • localhost:6379
```

---

## 🧪 Testing End-to-End

### 1. Iniciar el sistema

```bash
make up
```

### 2. Verificar que todo está corriendo

```bash
make status
```

### 3. Probar el flujo completo

```bash
# Desde tu máquina local
curl -X POST http://localhost:8002/api/v1/consumption/process/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "meeting_id": "meeting-456",
    "meeting_url": "https://meet.google.com/abc",
    "estimated_duration_minutes": 60,
    "transcription_text": "Necesitamos implementar autenticación JWT para el sistema...",
    "language": "es"
  }'
```

### 4. Ver logs en tiempo real

```bash
# En una terminal
make logs-gatekeeper

# En otra terminal
make logs-mock
```

---

## 🔧 Desarrollo con Hot Reload

El Gatekeeper está configurado con **hot reload** en desarrollo:

1. Edita archivos en `backend/app/`
2. Los cambios se reflejan automáticamente en el contenedor
3. No necesitas reiniciar el contenedor

```bash
# Ver logs mientras desarrollas
make logs-gatekeeper
```

---

## 🐛 Troubleshooting

### Problema: Puertos ya en uso

```bash
# Ver qué está usando los puertos
sudo lsof -i :8002
sudo lsof -i :5678
sudo lsof -i :5432

# Matar proceso si es necesario
sudo kill -9 <PID>
```

### Problema: Contenedor no inicia

```bash
# Ver logs del contenedor específico
docker-compose -f docker-compose.dev.yml logs gatekeeper

# Ver logs de todos
docker-compose -f docker-compose.dev.yml logs

# Reconstruir desde cero
make clean
make build
make up
```

### Problema: Base de datos con errores

```bash
# Eliminar volumen de PostgreSQL
docker volume rm memorymeet-postgres-dev-data

# Reiniciar todo
make restart
```

### Problema: Quiero empezar desde cero

```bash
# Limpiar todo
make clean

# O limpieza completa del sistema
make prune

# Volver a iniciar
make up
```

---

## 📊 Health Checks

### Verificar health de servicios

```bash
# Verificar todos
make health

# O manualmente
curl http://localhost:5678/health  # Mock n8n
curl http://localhost:8002/health  # Gatekeeper
```

### Respuesta esperada

```json
{
  "status": "healthy",
  "service": "consumption-service",
  "version": "1.0.0",
  "timestamp": 1234567890.123
}
```

---

## 🔐 Variables de Entorno

Las variables están hardcoded en `docker-compose.dev.yml` para desarrollo.

Para cambiarlas, puedes:

1. **Editar docker-compose.dev.yml** directamente
2. **Crear archivo .env** en la raíz:

```bash
# .env
POSTGRES_USER=memorymeet
POSTGRES_PASSWORD=mi_password_seguro
POSTGRES_DB=memorymeet_dev
```

3. **Usar el docker-compose.yml original** que lee `.env`

---

## 📦 Persistencia de Datos

Los datos persisten en **Docker volumes**:

```bash
# Ver volúmenes
make volumes

# Eliminar volúmenes (⚠️ borra datos)
docker volume rm memorymeet-postgres-dev-data
docker volume rm memorymeet-redis-dev-data
```

---

## 🚀 Workflow de Desarrollo

### Día a día

```bash
# 1. Iniciar sistema
make up

# 2. Desarrollar (hot reload activo)
# Editar código en backend/app/

# 3. Ver logs
make logs-gatekeeper

# 4. Ejecutar tests
make test

# 5. Al final del día
make down
```

### Cuando cambias dependencias

```bash
# Si modificas requirements.txt
make build
make restart
```

### Cuando quieres limpiar

```bash
# Limpiar volúmenes y contenedores
make clean

# Limpiar todo el sistema Docker
make prune  # ⚠️ CUIDADO
```

---

## 🎯 Comparación: Scripts vs Docker

### Scripts Bash (`./scripts/start_dev.sh`)

✅ Más rápido para cambios pequeños  
✅ No requiere Docker  
❌ Dependencias en tu máquina  
❌ Diferencias entre entornos  

### Docker (`make up`)

✅ Entorno idéntico para todos  
✅ Aislamiento completo  
✅ Incluye PostgreSQL y Redis  
✅ Production-like  
❌ Más lento para rebuild  

**Recomendación:** Usa Docker para desarrollo serio y scripts para pruebas rápidas.

---

## 📚 Más Información

- `docker-compose.dev.yml` - Configuración simplificada de desarrollo
- `docker-compose.yml` - Configuración completa con n8n, Prometheus, Grafana
- `Makefile` - Todos los comandos disponibles
- `backend/Dockerfile` - Dockerfile del Gatekeeper
- `backend/tests/mocks/Dockerfile.mock-n8n` - Dockerfile del Mock n8n

---

## ✅ Checklist de Verificación

Después de `make up`, verifica:

- [ ] `make status` muestra todos los servicios "Up"
- [ ] http://localhost:8002/health retorna 200
- [ ] http://localhost:5678/health retorna 200
- [ ] http://localhost:8002/docs abre Swagger UI
- [ ] PostgreSQL responde en puerto 5432
- [ ] Redis responde en puerto 6379

---

**¡Listo!** 🎉

Ahora tienes TODO dockerizado y listo para usar con `make up`

**Comando más importante:**
```bash
make help  # Ver todos los comandos disponibles
```
