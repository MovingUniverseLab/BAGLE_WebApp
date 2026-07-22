# Dockerfile
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get install -y g++ git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip
RUN python3 -m pip install --no-cache-dir numpy "cython<3.0.0" pybind11
RUN python3 -m pip install --no-cache-dir celerite
RUN python3 -m pip install --no-cache-dir --user -r requirements.txt
RUN python3 -m pip install git+https://github.com/MovingUniverseLab/BAGLE_Microlensing

COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Documenting target service port allocation
EXPOSE 8080

# Panel runtime serving configurations:
# 1. --address 0.0.0.0 binds to all available network host interfaces
# 2. --port 8080 targets the default Cloud Run application route configuration
# 3. --allow-websocket-origin=* avoids origin connection drop-offs on GCP proxy layers
CMD ["panel", "serve", "/app/app.py", "--address", "0.0.0.0", "--port", "8080", "--allow-websocket-origin=*"]

RUN mkdir /.cache
RUN chmod 777 /.cache

