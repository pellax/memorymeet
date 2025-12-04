#!/bin/bash
# ================================================================================================
# 🚀 ENTRYPOINT SCRIPT - BACKEND SERVICE CON ALEMBIC AUTO-MIGRATION
# ================================================================================================
# Este script ejecuta migraciones de Alembic automáticamente al iniciar el contenedor
# Garantiza que el schema de PostgreSQL esté siempre actualizado antes de levantar la API

set -e  # Exit on error

echo "🔍 [ENTRYPOINT] Verificando conexión a PostgreSQL..."

# Esperar a que PostgreSQL esté listo
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  >&2 echo "⏳ [ENTRYPOINT] PostgreSQL no está listo - esperando..."
  sleep 2
done

echo "✅ [ENTRYPOINT] PostgreSQL está listo"

echo "🔄 [ENTRYPOINT] Ejecutando migraciones de Alembic..."

# Ejecutar migraciones (upgrade to head)
cd /app
alembic -c backend/alembic.ini upgrade head

if [ $? -eq 0 ]; then
    echo "✅ [ENTRYPOINT] Migraciones aplicadas exitosamente"
else
    echo "❌ [ENTRYPOINT] Error al aplicar migraciones - Abortando"
    exit 1
fi

echo "🚀 [ENTRYPOINT] Iniciando aplicación FastAPI..."

# Ejecutar el comando original del Dockerfile
exec "$@"
