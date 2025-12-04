# ================================================================================================
# 🛠️ MAKEFILE - M2PRD-001 SaaS Development Commands
# ================================================================================================
# Comandos simplificados para desarrollo con Docker

.PHONY: help up down logs build clean test restart status

# Colors for output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
RESET  := $(shell tput -Txterm sgr0)

help: ## 📖 Mostrar ayuda
	@echo ''
	@echo '${BLUE}M2PRD-001 SaaS - Comandos Disponibles${RESET}'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${RESET} %s\n", $$1, $$2}'
	@echo ''

# ================================================================================================
# 🐳 DOCKER COMMANDS - Development Environment
# ================================================================================================

up: ## 🚀 Iniciar todos los servicios (PostgreSQL + Redis + Mock n8n + Gatekeeper)
	@echo "${BLUE}🚀 Iniciando servicios...${RESET}"
	docker-compose -f docker-compose.dev.yml up --build -d
	@echo "${GREEN}✅ Servicios iniciados${RESET}"
	@echo ""
	@make status

down: ## 🛑 Detener todos los servicios
	@echo "${BLUE}🛑 Deteniendo servicios...${RESET}"
	docker-compose -f docker-compose.dev.yml down
	@echo "${GREEN}✅ Servicios detenidos${RESET}"

logs: ## 📊 Ver logs en tiempo real
	docker-compose -f docker-compose.dev.yml logs -f

logs-gatekeeper: ## 📊 Ver logs del Gatekeeper
	docker-compose -f docker-compose.dev.yml logs -f gatekeeper

logs-mock: ## 📊 Ver logs del Mock n8n
	docker-compose -f docker-compose.dev.yml logs -f mock-n8n

build: ## 🔨 Reconstruir imágenes Docker
	@echo "${BLUE}🔨 Reconstruyendo imágenes...${RESET}"
	docker-compose -f docker-compose.dev.yml build --no-cache
	@echo "${GREEN}✅ Imágenes reconstruidas${RESET}"

clean: ## 🧹 Limpiar contenedores, volúmenes y imágenes
	@echo "${YELLOW}⚠️  Limpiando contenedores, volúmenes e imágenes...${RESET}"
	docker-compose -f docker-compose.dev.yml down -v --rmi local
	@echo "${GREEN}✅ Limpieza completada${RESET}"

restart: ## 🔄 Reiniciar todos los servicios
	@echo "${BLUE}🔄 Reiniciando servicios...${RESET}"
	@make down
	@make up

status: ## 📊 Ver estado de los servicios
	@echo "${BLUE}📊 Estado de los servicios:${RESET}"
	@echo ""
	@docker-compose -f docker-compose.dev.yml ps
	@echo ""
	@echo "${BLUE}📍 URLs disponibles:${RESET}"
	@echo "  ${GREEN}Mock n8n Server:${RESET}     http://localhost:5678"
	@echo "  ${GREEN}Gatekeeper Backend:${RESET}  http://localhost:8002"
	@echo "  ${GREEN}API Docs (Swagger):${RESET}  http://localhost:8002/docs"
	@echo "  ${GREEN}PostgreSQL:${RESET}          localhost:5432 (user: memorymeet)"
	@echo "  ${GREEN}Redis:${RESET}               localhost:6379"
	@echo ""

# ================================================================================================
# 🧪 TESTING COMMANDS
# ================================================================================================

test: ## 🧪 Ejecutar tests dentro del contenedor
	@echo "${BLUE}🧪 Ejecutando tests...${RESET}"
	docker-compose -f docker-compose.dev.yml exec gatekeeper pytest tests/ -v
	@echo "${GREEN}✅ Tests completados${RESET}"

test-cov: ## 📊 Ejecutar tests con coverage
	@echo "${BLUE}📊 Ejecutando tests con coverage...${RESET}"
	docker-compose -f docker-compose.dev.yml exec gatekeeper pytest tests/ -v --cov=app --cov-report=html
	@echo "${GREEN}✅ Coverage report generado en htmlcov/${RESET}"

# ================================================================================================
# 🔍 DEBUGGING COMMANDS
# ================================================================================================

shell-gatekeeper: ## 🐚 Abrir shell en el contenedor del Gatekeeper
	docker-compose -f docker-compose.dev.yml exec gatekeeper /bin/bash

shell-postgres: ## 🐚 Abrir psql en PostgreSQL
	docker-compose -f docker-compose.dev.yml exec postgres psql -U memorymeet -d memorymeet_dev

shell-redis: ## 🐚 Abrir redis-cli
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# ================================================================================================
# 📊 MONITORING COMMANDS
# ================================================================================================

health: ## 🏥 Verificar health de todos los servicios
	@echo "${BLUE}🏥 Verificando health de servicios...${RESET}"
	@echo ""
	@echo "${BLUE}Mock n8n:${RESET}"
	@curl -s http://localhost:5678/health | python3 -m json.tool || echo "${YELLOW}  ⚠️  No disponible${RESET}"
	@echo ""
	@echo "${BLUE}Gatekeeper:${RESET}"
	@curl -s http://localhost:8002/health | python3 -m json.tool || echo "${YELLOW}  ⚠️  No disponible${RESET}"
	@echo ""

watch: ## 👀 Monitorear estado de contenedores (Ctrl+C para salir)
	@watch -n 2 'docker-compose -f docker-compose.dev.yml ps'

# ================================================================================================
# 🔧 UTILITY COMMANDS
# ================================================================================================

prune: ## 🧹 Limpiar sistema Docker completo (⚠️ CUIDADO)
	@echo "${YELLOW}⚠️  Esta operación eliminará TODOS los contenedores, imágenes, volúmenes y redes no usados${RESET}"
	@echo "${YELLOW}⚠️  Presiona Ctrl+C para cancelar o Enter para continuar...${RESET}"
	@read confirm
	docker system prune -a --volumes -f
	@echo "${GREEN}✅ Sistema Docker limpiado${RESET}"

ps: ## 📋 Listar todos los contenedores
	docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

images: ## 📦 Listar imágenes Docker del proyecto
	docker images | grep memorymeet

volumes: ## 💾 Listar volúmenes del proyecto
	docker volume ls | grep memorymeet

# ================================================================================================
# 🚀 QUICK START COMMANDS
# ================================================================================================

dev: up ## 🎯 Alias para 'make up' - Iniciar desarrollo
	@echo "${GREEN}💡 Tip: Usa 'make logs' para ver los logs${RESET}"

stop: down ## 🎯 Alias para 'make down' - Detener servicios

# Default target
.DEFAULT_GOAL := help
