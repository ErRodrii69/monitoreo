# ServerWatch

Sistema web de monitorizacion de servidores basado en Django, Django REST Framework, PostgreSQL y un frontend estatico HTML/CSS/JS.

## Requisitos cubiertos

- CRUD de servidores con activacion y desactivacion.
- Comprobaciones automaticas de Ping ICMP, SSH, HTTP, HTTPS y puertos personalizados.
- Dashboard con estado general e incidencias abiertas.
- Registro historico de comprobaciones en base de datos.
- Registro de incidencias abiertas y resueltas.
- Notificaciones por email ante caidas y, opcionalmente, recuperaciones.
- Dockerizacion con PostgreSQL, backend web y worker de monitorizacion separados.

## Arranque con Docker

Desde la carpeta `server-monitor`:

```bash
docker compose up -d --build
```

La aplicacion queda disponible en:

```text
http://localhost:8000
```

Logs utiles:

```bash
docker compose logs -f backend
docker compose logs -f monitor
```

Parar todo:

```bash
docker compose down
```

## Variables de entorno

El proyecto funciona con valores por defecto. Para configurar correo o credenciales, crea un `.env` tomando como base `.env.example`.

Campos SMTP principales:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_usuario
SMTP_PASSWORD=tu_password_o_app_password
SMTP_FROM=monitor@empresa.com
ALERT_EMAIL_TO=admin@empresa.com
```

## Comandos habituales

```bash
make up
make logs
make logs-monitor
make superuser
make dump-db
```

Si no tienes `make` en Windows, usa directamente los comandos `docker compose`.

## Desarrollo local sin Docker

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

En otra terminal puedes lanzar el worker:

```bash
cd backend
.venv\Scripts\activate
python manage.py monitor_scheduler
```

## Exportar la base de datos

```bash
docker compose exec db pg_dump -U monitor servermonitor > database_export.sql
```

El fichero `database_export.sql` queda en la raiz del proyecto.
