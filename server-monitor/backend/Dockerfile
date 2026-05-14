# =============================================================
# backend/Dockerfile
# Imagen del backend FastAPI
# =============================================================

FROM python:3.12-slim

# Instalamos iputils-ping para poder ejecutar ping ICMP
RUN apt-get update && apt-get install -y --no-install-recommends \
      iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Copiamos e instalamos dependencias primero (capa cacheada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente
COPY . .

# Puerto de la aplicación
EXPOSE 8000

# Arrancamos con Uvicorn; --host 0.0.0.0 para aceptar conexiones externas
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
