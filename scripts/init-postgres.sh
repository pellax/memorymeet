#!/bin/bash
# ================================================================================================
# 🐘 PostgreSQL Multi-Database Initialization Script
# ================================================================================================
# Crea múltiples bases de datos en PostgreSQL para separación de responsabilidades
# 
# Databases:
# - auth_db: Servicio de Autenticación (RF6.0)
# - consumption_db: Servicio de Consumo/Suscripciones (RF8.0)
# - main_db: Backend Principal
# - n8n_db: Orquestador n8n

set -e
set -u

function create_database() {
    local database=$1
    echo "🔧 Creating database '$database'..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
    echo "✅ Database '$database' created successfully"
}

echo "================================================================================================"
echo "🚀 Starting PostgreSQL Multi-Database Initialization"
echo "================================================================================================"

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "📋 Databases to create: $POSTGRES_MULTIPLE_DATABASES"
    
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_database $db
    done
    
    echo "================================================================================================"
    echo "✅ All databases created successfully!"
    echo "================================================================================================"
else
    echo "⚠️  Warning: POSTGRES_MULTIPLE_DATABASES not set. Skipping multi-database creation."
fi
