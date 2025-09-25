# Usa una sola imagen base. Python:3.12-slim es más ligera que ubuntu:latest y ya incluye lo necesario.
FROM python:3.12-slim as base

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema en una sola capa
# El '&& rm -rf /var/lib/apt/lists/*' es una buena práctica para reducir el tamaño de la imagen.
RUN apt clean all && apt-get update\
    && apt-get install -y --no-install-recommends \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxrender1 \
    libx11-xcb1 \
    libfontconfig1 \
    libgl1 \
    libglx-mesa0 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia los requirements.txt y los instala antes que el resto del código
# Esto aprovecha el cache de Docker, así que si los requirements no cambian,
# no se reinstalarán las dependencias.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Etapa de construcción final ---
# Esto es opcional, pero ayuda a crear una imagen aún más pequeña
# eliminando las herramientas de compilación (`build-essential`, `cmake`).
FROM python:3.12-slim
WORKDIR /app
COPY --from=base /app .

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]