# Utilizar imagen ligera de Python 3.11/3.12
FROM python:3.11-slim

# Evitar escritura de archivos .pyc y habilitar logs en tiempo real (unbuffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas para compilación (si aplica)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# Exponer el puerto por defecto de Flask
EXPOSE 5000

# Comando por defecto para arrancar la API
CMD ["python", "run.py"]
