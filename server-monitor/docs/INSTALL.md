# Manual de Instalación — ServerWatch

## Requisitos previos

| Herramienta | Versión mínima |
|-------------|----------------|
| Docker      | 24.x           |
| Docker Compose | 2.20 (plugin integrado en Docker Desktop) |
| Git         | Cualquiera     |

> **Linux**: asegúrate de que tu usuario pertenece al grupo `docker` para no necesitar `sudo`.

---

## 1. Clonar el repositorio

```bash
git clone <url-del-repositorio> serverwatch
cd serverwatch
```

---

## 2. Configurar el entorno

Copia el fichero de ejemplo y edita los valores:

```bash
cp .env.example .env
nano .env          # o cualquier editor de texto
```

**Campos obligatorios:**

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_PASSWORD` | Contraseña de la BD (cámbiala siempre) |
| `ALERT_EMAIL_TO` | Correo al que llegan las alertas de caída |
| `SMTP_USER` | Usuario de tu cuenta de correo saliente |
| `SMTP_PASSWORD` | Contraseña o App Password de la cuenta SMTP |

**Nota para Gmail:** Google requiere una *App Password* (contraseña de aplicación), no la contraseña normal. Puedes generarla en: Cuenta de Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicación.

---

## 3. Levantar la aplicación

### Opción A — Todo en un comando (recomendado)

```bash
make up
```

Esto construye las imágenes y levanta los contenedores en segundo plano.

### Opción B — Paso a paso

```bash
# 1. Levantar primero la BD
docker compose -f docker-compose.base.yml up -d

# 2. Levantar el backend (espera a que la BD esté sana)
docker compose -f docker-compose.base.yml -f docker-compose.yml up -d --build
```

---

## 4. Verificar que todo funciona

```bash
# Ver el estado de los contenedores
make ps

# Ver los logs del backend en tiempo real
make logs
```

Deberías ver algo como:
```
INFO:     Application startup complete.
INFO:     Scheduler iniciado. Intervalo: 60 segundos.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 5. Acceder a la aplicación

Abre el navegador en:

```
http://localhost:8000
```

La documentación interactiva de la API está disponible en:

```
http://localhost:8000/docs
```

---

## 6. Añadir el primer servidor

1. Haz clic en la pestaña **Servidores**.
2. Pulsa **+ Añadir servidor**.
3. Introduce el nombre y la IP (privada o pública).
4. Guarda. El servidor aparecerá en el Dashboard.
5. En la siguiente ronda de ping (según el intervalo configurado) verás su estado actualizarse.

---

## 7. Configurar el intervalo de monitorización

1. Ve a la pestaña **Ajustes**.
2. Cambia el campo *Intervalo entre comprobaciones*.
3. Pulsa **Guardar ajustes**. El cambio es inmediato, sin reiniciar.

---

## 8. Comandos útiles

```bash
make logs          # Logs del backend en tiempo real
make restart       # Reiniciar solo el backend
make down          # Detener todos los servicios
make shell-back    # Shell interactiva en el contenedor del backend
```

---

## 9. Detener la aplicación

```bash
make down
```

Los datos de PostgreSQL se conservan en el volumen `pgdata` y estarán disponibles la próxima vez que arranques.

---

## 10. Desarrollo local (sin Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Levanta solo la BD con Docker
docker compose -f ../docker-compose.base.yml up -d

# Copia y edita el .env
cp ../.env.example .env

# Arranca el servidor
uvicorn main:app --reload
```

### Frontend

El frontend es HTML/CSS/JS puro, servido por FastAPI como ficheros estáticos. No necesita compilación ni Node.js. Con el backend arrancado, accede directamente a `http://localhost:8000`.
