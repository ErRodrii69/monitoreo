# Manual de instalacion

## 1. Preparar entorno

Instala Docker Desktop y verifica:

```bash
docker --version
docker compose version
```

## 2. Configurar variables

Opcionalmente copia `.env.example` a `.env` y ajusta credenciales SMTP.

## 3. Levantar servicios

```bash
docker compose up -d --build
```

Servicios creados:

- `serverwatch-db`: PostgreSQL.
- `serverwatch-backend`: Django + DRF + frontend estatico.
- `serverwatch-monitor`: worker de comprobaciones periodicas.

## 4. Abrir la aplicacion

```text
http://localhost:8000
```

## 5. Crear usuario admin

```bash
docker compose exec backend python manage.py createsuperuser
```

Panel admin:

```text
http://localhost:8000/admin/
```

## 6. Comprobar logs

```bash
docker compose logs -f backend
docker compose logs -f monitor
```

## 7. Exportar base de datos

```bash
docker compose exec db pg_dump -U monitor servermonitor > database_export.sql
```
