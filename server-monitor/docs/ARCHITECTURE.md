# Documento de Arquitectura y Lógica — ServerWatch

## ¿Qué hace esta aplicación?

ServerWatch es un sistema de monitorización de servidores que comprueba periódicamente
si una lista de hosts (IP o hostname) responde al ping ICMP. Cuando un servidor deja de
responder, envía automáticamente un correo de alerta a una dirección configurada.

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────┐
│                    NAVEGADOR                        │
│  HTML + CSS + JS vanilla  (frontend/templates/)     │
│  fetch() → llama a la API REST del backend          │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / JSON
┌────────────────────▼────────────────────────────────┐
│                  BACKEND (FastAPI)                  │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  API REST   │  │  Scheduler   │  │  Servicios│  │
│  │  /api/...   │  │  (asyncio)   │  │  ping     │  │
│  └─────────────┘  └──────┬───────┘  │  email    │  │
│                           │          │  monitor  │  │
│  SQLAlchemy (async ORM)   │          └───────────┘  │
└───────────────────────────┼─────────────────────────┘
                            │ asyncpg
┌───────────────────────────▼─────────────────────────┐
│               PostgreSQL (Docker separado)          │
│  Tablas: servers, check_logs                        │
└─────────────────────────────────────────────────────┘
```

---

## Flujo de una ronda de monitorización

```
Scheduler (cada N segundos)
   │
   ▼
_run_check_round()
   │
   ├─ Consulta BD: todos los servers con is_active=True
   │
   └─ Para cada servidor (en paralelo con asyncio.gather):
         │
         ▼
      check_server(server, db)          ← monitor_service.py
         │
         ├─ ping_host(ip, ...)           ← ping_service.py
         │     └─ Ejecuta: ping -c 1 -W 3 <ip>
         │     └─ Parsea la salida: latencia en ms
         │     └─ Devuelve PingResult(success, response_ms, error)
         │
         ├─ _save_check_log(db, ...)     → INSERT en check_logs
         │
         ├─ _update_server_status(db, ...)  → UPDATE en servers
         │
         └─ Si status cambió a "down" (primera vez que cae):
               send_alert_email(...)     ← email_service.py
```

---

## Estructura de ficheros

```
server-monitor/
│
├── backend/
│   ├── main.py                  # Punto de entrada FastAPI + lifecycle
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── core/
│       │   ├── config.py        # Variables de entorno (Pydantic Settings)
│       │   └── database.py      # Motor SQLAlchemy async + sesión
│       ├── models/
│       │   └── __init__.py      # Modelos ORM: Server, CheckLog
│       ├── api/
│       │   ├── schemas.py       # Esquemas Pydantic (request/response)
│       │   ├── servers.py       # CRUD de servidores
│       │   ├── checks.py        # Historial de comprobaciones
│       │   └── settings.py      # Ajustes en tiempo real
│       ├── services/
│       │   ├── ping_service.py  # Lógica ICMP (solo ping)
│       │   ├── email_service.py # Envío de alertas (solo email)
│       │   └── monitor_service.py # Orquestador: ping + BD + email
│       └── tasks/
│           └── scheduler.py     # Bucle asíncrono de monitorización
│
├── frontend/
│   ├── templates/
│   │   └── index.html           # SPA de página única
│   └── static/
│       ├── css/
│       │   └── main.css         # Estilos (tema oscuro industrial)
│       └── js/
│           ├── api.js           # Cliente HTTP (todas las llamadas fetch)
│           ├── dashboard.js     # Vista Dashboard
│           ├── servers.js       # Vista Servidores (CRUD)
│           ├── logs.js          # Vista Registros
│           ├── settings.js      # Vista Ajustes
│           └── app.js           # Orquestador: navegación, toasts, utils
│
├── docker-compose.base.yml      # Solo PostgreSQL
├── docker-compose.yml           # Backend (extiende base)
├── .env.example                 # Plantilla de variables de entorno
└── Makefile                     # Atajos de comandos
```

---

## Principios de diseño aplicados

### Responsabilidad única por función y módulo

Cada función tiene una sola tarea:
- `ping_host()` → solo lanza el ping y devuelve el resultado.
- `send_alert_email()` → solo envía el correo.
- `_save_check_log()` → solo escribe el log en BD.
- `_update_server_status()` → solo actualiza el estado del servidor.
- `check_server()` → coordina las anteriores (orquestador).

### Separación backend / frontend

El frontend es HTML/CSS/JS puro. No conoce la BD ni la lógica de negocio. Solo habla con la API REST a través de `api.js`. Toda la lógica vive en el backend.

### Docker con extends

La BD corre en un compose separado (`docker-compose.base.yml`). El compose de la aplicación (`docker-compose.yml`) lo incluye con `include:`. Esto permite arrancar solo la BD durante el desarrollo, o añadir nuevos servicios sin tocar la configuración de la BD.

### Intervalo editable en caliente

El scheduler no usa `time.sleep()` sino un bucle de `asyncio.sleep(1)` que comprueba en cada iteración si debe detenerse. Esto permite que un cambio de intervalo desde los ajustes surta efecto en menos de 1 segundo, sin reiniciar el proceso.

### Alertas sin spam

El correo de alerta solo se envía cuando el servidor **cambia** de estado a "down" (transición `cualquiera → down`). Si el servidor lleva varios ciclos caído, no se vuelve a enviar hasta que se recupere y vuelva a caer.

---

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /api/servers/ | Listar servidores |
| POST   | /api/servers/ | Crear servidor |
| GET    | /api/servers/{id} | Obtener servidor |
| PUT    | /api/servers/{id} | Actualizar servidor |
| DELETE | /api/servers/{id} | Eliminar servidor |
| POST   | /api/servers/{id}/ping | Ping manual |
| GET    | /api/checks/ | Últimas comprobaciones |
| GET    | /api/checks/server/{id} | Historial de un servidor |
| GET    | /api/settings/ | Ver ajustes |
| PATCH  | /api/settings/ | Actualizar ajustes |

Documentación interactiva (Swagger): `http://localhost:8000/docs`

---

## Base de datos

### Tabla `servers`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | Identificador |
| name | VARCHAR(128) | Nombre legible |
| ip_address | VARCHAR(64) | IP o hostname |
| description | TEXT | Descripción opcional |
| is_active | BOOLEAN | Si se monitoriza |
| last_status | ENUM(unknown,up,down) | Estado actual |
| last_checked_at | TIMESTAMPTZ | Última comprobación |
| last_response_ms | FLOAT | Latencia del último ping |
| created_at | TIMESTAMPTZ | Fecha de creación |
| updated_at | TIMESTAMPTZ | Última modificación |

### Tabla `check_logs`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | Identificador |
| server_id | FK → servers.id | Servidor |
| status | ENUM(up,down) | Resultado |
| response_ms | FLOAT | Latencia (NULL si caído) |
| error_message | TEXT | Descripción del error |
| checked_at | TIMESTAMPTZ | Momento de la comprobación |
