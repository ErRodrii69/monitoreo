COMPOSE = docker compose

.PHONY: up down build logs logs-web logs-monitor ps migrate superuser shell dump-db db

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build --no-cache

logs:
	$(COMPOSE) logs -f

logs-web:
	$(COMPOSE) logs -f backend

logs-monitor:
	$(COMPOSE) logs -f monitor

ps:
	$(COMPOSE) ps

db:
	$(COMPOSE) up -d db

migrate:
	$(COMPOSE) exec backend python manage.py migrate

superuser:
	$(COMPOSE) exec backend python manage.py createsuperuser

shell:
	$(COMPOSE) exec backend python manage.py shell

dump-db:
	$(COMPOSE) exec db pg_dump -U monitor servermonitor > database_export.sql
