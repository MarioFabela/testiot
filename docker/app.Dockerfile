FROM debian:bookworm-slim

# Evita que el sistema pregunte cosas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instalamos Python, pip y OpenCV nativo
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Instalamos MQTT, Numpy y LGPIO (OpenCV ya está instalado por apt)
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY src/ ./src/

CMD ["python3", "src/main.py"]