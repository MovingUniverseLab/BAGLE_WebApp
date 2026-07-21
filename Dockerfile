# Dockerfile
# Stage 1: Build & dependency compilation environment
FROM python:3.14-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime execution container
FROM python:3.14-slim AS runner

WORKDIR /app

# Copy installed site-packages dependencies from the builder stage
COPY --from=builder /root/.local /root/.local
COPY app.py .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Documenting target service port allocation
EXPOSE 8080

# Panel runtime serving configurations:
# 1. --address 0.0.0.0 binds to all available network host interfaces
# 2. --port 8080 targets the default Cloud Run application route configuration
# 3. --allow-websocket-origin=* avoids origin connection drop-offs on GCP proxy layers
CMD ["panel", "serve", "app.py", "--address", "0.0.0.0", "--port", "8080", "--allow-websocket-origin=*"]

