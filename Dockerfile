FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects the PORT environment variable (defaults to 8080)
EXPOSE 8080

CMD ["panel", "serve", "app.py", "--address", "0.0.0.0", "--port", "8080", "--allow-websocket-origin=*"]
