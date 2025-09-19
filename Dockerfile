# Dockerfile

FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/ ./src/

# Copiar archivo .env (si usas para la API key)
COPY .env .

# Comando por defecto (ejemplo ejecutando core_agent.py)
CMD ["python", "src/agent/core_agent.py"]
