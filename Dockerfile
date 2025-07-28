# Usar Python 3.11 slim
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY src/ ./src/

# Exponer puerto
EXPOSE 8080

# Variable de entorno para Flask
ENV FLASK_ENV=production
ENV PORT=8080

# Comando para ejecutar la aplicación
CMD ["python", "src/app.py"] 