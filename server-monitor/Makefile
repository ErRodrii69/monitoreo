# =============================================================
# Makefile — Atajos para tareas habituales del proyecto
# =============================================================

COMPOSE_FILES = -f docker-compose.base.yml -f docker-compose.yml

.PHONY: up down logs ps build restart shell-back

## Levanta todos los servicios (BD + backend)
up:
	docker compose $(COMPOSE_FILES) up -d --build

## Detiene todos los servicios
down:
	docker compose $(COMPOSE_FILES) down

## Solo la base de datos
db:
	docker compose -f docker-compose.base.yml up -d

## Muestra los logs del backend en tiempo real
logs:
	docker compose $(COMPOSE_FILES) logs -f backend

## Estado de los contenedores
ps:
	docker compose $(COMPOSE_FILES) ps

## Reconstruye las imágenes sin caché
build:
	docker compose $(COMPOSE_FILES) build --no-cache

## Reinicia solo el backend
restart:
	docker compose $(COMPOSE_FILES) restart backend

## Abre una shell en el contenedor del backend
shell-back:
	docker compose $(COMPOSE_FILES) exec backend bash
