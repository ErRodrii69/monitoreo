# Mapeo de requisitos del PDF

| Requisito | Estado | Implementacion |
| --- | --- | --- |
| Backend Django + DRF | Hecho | `backend/server_monitor`, `backend/monitoring` |
| Frontend React o HTML/CSS | Hecho | `frontend/templates`, `frontend/static` |
| PostgreSQL | Hecho | Servicio `db` en `docker-compose.yml` |
| ORM Django | Hecho | Modelos `Server`, `CheckLog`, `Incident`, `AppSetting` |
| Gestion de servidores | Hecho | `/api/servers/` y vista Servidores |
| Ping ICMP | Hecho | `monitoring/services/checks.py` |
| SSH | Hecho | Check TCP sobre puerto SSH configurable |
| HTTP/HTTPS | Hecho | Checks HEAD/GET con timeout configurable |
| Puertos personalizados | Hecho | Campo `custom_ports` por servidor |
| Alertas visibles | Hecho | Dashboard e incidencias abiertas |
| Email automatico | Hecho | `monitoring/services/emailing.py` |
| Registro de incidencias | Hecho | Modelo `Incident` y endpoint `/api/incidents/` |
| Historial | Hecho | Modelo `CheckLog` y endpoint `/api/checks/` |
| Dockerizacion | Hecho | Web, worker y PostgreSQL separados |

Notas:

- El frontend se ha dejado en HTML/CSS/JS, tal como se pidio.
- El worker `monitor` ejecuta las comprobaciones periodicas. El backend web no carga el scheduler para evitar duplicados.
- El sistema de usuarios queda disponible mediante el admin de Django (`/admin/`) si se crea un superusuario.
