# 🔄 ALEMBIC MIGRATIONS - GUÍA COMPLETA

## ✅ **ESTADO**: MIGRACIONES 100% IMPLEMENTADAS Y TESTEADAS

Sistema de gestión de migraciones de base de datos con **Alembic** completamente configurado, integrado con Docker y validado mediante **17 tests TDD** (100% passing).

---

## 📋 **ÍNDICE**

1. [Introducción](#introducción)
2. [Arquitectura de Migraciones](#arquitectura-de-migraciones)
3. [Configuración Completa](#configuración-completa)
4. [Comandos Esenciales](#comandos-esenciales)
5. [Flujo de Desarrollo](#flujo-de-desarrollo)
6. [Auto-Migración en Docker](#auto-migración-en-docker)
7. [Testing TDD](#testing-tdd)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 **INTRODUCCIÓN**

### ¿Qué es Alembic?

**Alembic** es una herramienta de **migraciones de base de datos** para **SQLAlchemy** que permite:

- ✅ **Versionado del schema**: Control de cambios en la estructura de la BD
- ✅ **Migraciones automáticas**: Detecta cambios en modelos y genera SQL
- ✅ **Rollback seguro**: Revertir cambios con función `downgrade()`
- ✅ **Historial auditable**: Tabla `alembic_version` rastrea versión actual

### ¿Por qué Alembic en M2PRD-001?

1. **Clean Architecture**: Separación clara entre Domain Models y Database Schema
2. **ACID Compliance**: Migraciones transaccionales que garantizan consistencia
3. **CI/CD Ready**: Auto-aplicación de migraciones en deployment
4. **Team Collaboration**: Evita conflictos en schema entre desarrolladores

---

## 🏗️ **ARQUITECTURA DE MIGRACIONES**

### **Estructura de Directorios**

```
backend/
├── alembic.ini                      # ✅ Configuración principal de Alembic
├── alembic/
│   ├── env.py                       # ✅ Configuración de environment (auto-detect models)
│   ├── script.py.mako               # ✅ Template para nuevas migraciones
│   ├── README                       # ✅ Documentación básica
│   └── versions/                    # ✅ Directorio de migraciones
│       └── 164cf67dea8e_initial_schema_meeting_prd_task_models.py
├── app/
│   ├── models/
│   │   ├── meeting.py               # ✅ Meeting model (detectado por env.py)
│   │   ├── prd.py                   # ✅ PRD model
│   │   └── task.py                  # ✅ Task model
│   └── database/
│       ├── base.py                  # ✅ Base declarativa SQLAlchemy
│       └── session_manager.py       # ✅ Transaction manager ACID
└── entrypoint.sh                    # ✅ Script de auto-migración en startup
```

### **Flujo de Migración Automático**

```mermaid
graph LR
    A[Docker Compose Up] --> B[entrypoint.sh]
    B --> C{PostgreSQL Ready?}
    C -->|No| D[Wait 2s]
    D --> C
    C -->|Yes| E[alembic upgrade head]
    E --> F{Migraciones OK?}
    F -->|No| G[Exit 1 - Abortar]
    F -->|Yes| H[uvicorn app:main]
    H --> I[API Ready]
```

---

## ⚙️ **CONFIGURACIÓN COMPLETA**

### **1. alembic.ini**

```ini
# backend/alembic.ini
[alembic]
script_location = backend/alembic
prepend_sys_path = .

# ✅ URL se obtiene de DATABASE_URL en env.py
# sqlalchemy.url = postgresql://user:pass@host:port/db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### **2. env.py - Configuración Crítica**

```python path=/home/pellax/Documents/memorymeet/backend/alembic/env.py start=1
from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ✅ Añadir el directorio app al path para importar modelos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# ✅ Importar Base y todos los modelos para autogenerate
from app.database.base import Base
from app.models.meeting import Meeting
from app.models.prd import PRD
from app.models.task import Task

config = context.config

# ✅ Obtener DATABASE_URL de variable de entorno
if not config.get_main_option("sqlalchemy.url"):
    database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Configurar metadata para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### **3. entrypoint.sh - Auto-Migración**

```bash path=/home/pellax/Documents/memorymeet/backend/entrypoint.sh start=1
#!/bin/bash
# Auto-migration script ejecutado en startup del contenedor

set -e

echo "🔍 [ENTRYPOINT] Verificando conexión a PostgreSQL..."

# Esperar a que PostgreSQL esté listo
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  >&2 echo "⏳ [ENTRYPOINT] PostgreSQL no está listo - esperando..."
  sleep 2
done

echo "✅ [ENTRYPOINT] PostgreSQL está listo"

echo "🔄 [ENTRYPOINT] Ejecutando migraciones de Alembic..."

cd /app
alembic -c backend/alembic.ini upgrade head

if [ $? -eq 0 ]; then
    echo "✅ [ENTRYPOINT] Migraciones aplicadas exitosamente"
else
    echo "❌ [ENTRYPOINT] Error al aplicar migraciones - Abortando"
    exit 1
fi

echo "🚀 [ENTRYPOINT] Iniciando aplicación FastAPI..."

exec "$@"
```

---

## 🛠️ **COMANDOS ESENCIALES**

### **Comandos de Desarrollo Local**

```bash
# ===== INICIALIZACIÓN (YA HECHO) =====
# Inicializar Alembic en proyecto nuevo
alembic init backend/alembic

# ===== CREAR MIGRACIONES =====
# Generar migración automática (detecta cambios en modelos)
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini revision --autogenerate -m "Descripción del cambio"

# Crear migración vacía manual
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini revision -m "Custom migration"

# ===== APLICAR MIGRACIONES =====
# Aplicar todas las migraciones pendientes (upgrade to head)
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head

# Aplicar siguiente migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade +1

# Aplicar hasta versión específica
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade <revision_id>

# ===== ROLLBACK =====
# Revertir última migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini downgrade -1

# Revertir a versión específica
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini downgrade <revision_id>

# Revertir todas (CUIDADO: borra todo el schema)
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini downgrade base

# ===== INFORMACIÓN =====
# Ver historial de migraciones
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini history

# Ver versión actual aplicada
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini current

# Ver SQL que se ejecutaría (sin aplicar)
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head --sql
```

### **Comandos de Verificación**

```bash
# Ver tablas en PostgreSQL
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "\dt"

# Ver índices
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "\di"

# Ver versión de Alembic aplicada
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "SELECT * FROM alembic_version;"

# Ver estructura de tabla específica
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "\d meetings"
```

---

## 🔄 **FLUJO DE DESARROLLO**

### **Escenario 1: Añadir Nueva Columna a Model**

```python
# 1. Modificar model (ejemplo: añadir campo 'rating' a PRD)
# backend/app/models/prd.py

from sqlalchemy import Column, Float

class PRD(Base):
    # ... campos existentes ...
    
    # ✅ Nueva columna
    rating = Column(Float, nullable=True, default=0.0)
    comment="Rating de calidad del PRD generado (0.0 - 5.0)"
```

```bash
# 2. Generar migración automática
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini revision --autogenerate -m "Add rating column to PRD"

# 3. Revisar migración generada
cat backend/alembic/versions/<revision_id>_add_rating_column_to_prd.py

# 4. Aplicar migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head

# 5. Verificar en PostgreSQL
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "\d prds"
```

### **Escenario 2: Crear Nueva Tabla**

```python
# 1. Crear nuevo model
# backend/app/models/notification.py

from sqlalchemy import Column, String, DateTime, Boolean
from app.database.base import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

```python
# 2. Importar en env.py
# backend/alembic/env.py

# ... imports existentes ...
from app.models.notification import Notification  # ✅ Añadir import
```

```bash
# 3. Generar migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini revision --autogenerate -m "Create notifications table"

# 4. Aplicar
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head
```

### **Escenario 3: Rollback de Migración Problemática**

```bash
# 1. Ver historial
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini history

# 2. Revertir última migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini downgrade -1

# 3. Verificar estado
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini current

# 4. Editar migración problemática
vim backend/alembic/versions/<revision_id>_problematic_migration.py

# 5. Re-aplicar corregida
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head
```

---

## 🐳 **AUTO-MIGRACIÓN EN DOCKER**

### **Dockerfile - Integración**

El `Dockerfile` está configurado para incluir Alembic y ejecutar migraciones automáticamente:

```dockerfile
# ===== DEPENDENCIES STAGE =====
FROM base as dependencies

# Instalar postgresql-client para entrypoint
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ... dependencias Python ...

# ===== DEVELOPMENT STAGE =====
FROM dependencies as development

# Copiar Alembic
COPY backend/alembic.ini /app/backend/alembic.ini
COPY backend/alembic /app/backend/alembic

# Copiar entrypoint de auto-migración
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Configurar entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### **docker-compose.yml - Dependencias**

```yaml
services:
  backend:
    # ...
    depends_on:
      postgres:
        condition: service_healthy  # ✅ Espera a PostgreSQL
      redis:
        condition: service_healthy
    
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

### **Logs de Startup**

```bash
docker logs m2prd_backend_gatekeeper

# Output esperado:
🔍 [ENTRYPOINT] Verificando conexión a PostgreSQL...
✅ [ENTRYPOINT] PostgreSQL está listo
🔄 [ENTRYPOINT] Ejecutando migraciones de Alembic...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
✅ [ENTRYPOINT] Migraciones aplicadas exitosamente
🚀 [ENTRYPOINT] Iniciando aplicación FastAPI...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 **TESTING TDD**

### **Suite de Tests de Migraciones**

Ubicación: `tests/test_alembic/test_schema_migrations.py`

**17 tests TDD que validan:**

#### **1. Existencia de Tablas (4 tests)**
- ✅ `test_should_have_meetings_table`
- ✅ `test_should_have_prds_table`
- ✅ `test_should_have_tasks_table`
- ✅ `test_should_have_alembic_version_table`

#### **2. Estructura de Columnas (3 tests)**
- ✅ `test_meetings_table_should_have_required_columns` - Valida 12 columnas + tipos
- ✅ `test_prds_table_should_have_required_columns` - Valida JSON column
- ✅ `test_tasks_table_should_have_required_columns` - Valida ENUMs

#### **3. Primary Keys (3 tests)**
- ✅ `test_meetings_table_should_have_primary_key`
- ✅ `test_prds_table_should_have_primary_key`
- ✅ `test_tasks_table_should_have_primary_key`

#### **4. Foreign Keys - ACID Compliance (2 tests)**
- ✅ `test_prds_table_should_have_foreign_key_to_meetings` - prds.meeting_id → meetings.id
- ✅ `test_tasks_table_should_have_foreign_key_to_prds` - tasks.prd_id → prds.id

#### **5. Índices de Performance (2 tests)**
- ✅ `test_meetings_table_should_have_indexes` - 3 índices
- ✅ `test_tasks_table_should_have_indexes` - 5 índices

#### **6. Unique Constraints (1 test)**
- ✅ `test_prds_table_should_have_unique_meeting_id` - 1 PRD por reunión

#### **7. Versión Actual (1 test)**
- ✅ `test_alembic_version_should_be_latest` - Versión `164cf67dea8e` aplicada

#### **8. Integridad End-to-End (1 test)**
- ✅ `test_should_insert_data_respecting_foreign_keys` - Test E2E completo

### **Ejecutar Tests**

```bash
# Tests de migraciones
docker exec m2prd_backend_gatekeeper pytest /app/tests_root/test_alembic/test_schema_migrations.py -v

# Con coverage
docker exec m2prd_backend_gatekeeper pytest /app/tests_root/test_alembic/ --cov=app.models --cov-report=html

# Resultado esperado: 17 passed in <1s
```

---

## 🚨 **TROUBLESHOOTING**

### **Problema 1: Migración No Detecta Cambios**

```bash
# Síntoma
INFO  [alembic.autogenerate.compare] No changes detected

# Causa: Model no importado en env.py
# Solución:
# 1. Editar backend/alembic/env.py
from app.models.nuevo_model import NuevoModel  # ✅ Añadir import

# 2. Regenerar migración
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini revision --autogenerate -m "Add nuevo model"
```

### **Problema 2: Error "relation already exists"**

```bash
# Síntoma
ERROR: relation "meetings" already exists

# Causa: Schema desincronizado con Alembic
# Solución 1: Stamp current state
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini stamp head

# Solución 2: Drop y recrear (SOLO DESARROLLO)
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose restart backend  # Auto-aplica migraciones
```

### **Problema 3: Entrypoint Falla**

```bash
# Síntoma
❌ [ENTRYPOINT] Error al aplicar migraciones - Abortando

# Causa: PostgreSQL no listo o migración errónea
# Solución:
# 1. Ver logs completos
docker logs m2prd_backend_gatekeeper

# 2. Verificar PostgreSQL
docker exec m2prd_postgres_acid psql -U m2prd_user -d m2prd_main -c "SELECT 1;"

# 3. Aplicar manualmente para ver error
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head
```

### **Problema 4: Migrations Out of Sync**

```bash
# Síntoma
WARNING: Current revision does not match database

# Solución: Ver diferencia
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini current
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini history

# Aplicar pendientes
docker exec m2prd_backend_gatekeeper alembic -c backend/alembic.ini upgrade head
```

---

## 📊 **RESUMEN EJECUTIVO**

### ✅ **Sistema Completado**

| Componente | Estado | Tests |
|------------|--------|-------|
| **Alembic Config** | ✅ | N/A |
| **env.py Auto-detect** | ✅ | N/A |
| **Migración Inicial** | ✅ | Schema aplicado |
| **Auto-Migration Docker** | ✅ | Logs verificados |
| **Tests TDD** | ✅ | **17/17 passing** |
| **Documentación** | ✅ | Esta guía |

### 🎯 **Próximos Pasos Recomendados**

1. ✅ **Integrar con CI/CD**: Tests de migraciones en pipeline
2. ✅ **Backup Strategy**: Backup pre-migration en producción
3. ✅ **Rollback Plan**: Procedimiento documentado de rollback
4. ⏳ **Multi-Environment**: Migraciones separadas dev/staging/prod

### 📚 **Referencias**

- [Alembic Official Docs](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/)
- Fase 3 Completada: `docs/FASE_3_COMPLETADA.md`
- WARP Principles: `WARP.md`

---

**Fecha de Completado**: 2025-12-04  
**Versión Inicial**: `164cf67dea8e`  
**Tests Pasando**: 17/17 (100%)  
**Auto-Migration**: ✅ Funcional
