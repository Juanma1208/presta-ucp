FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# Fila 19 · Semgrep missing-user: la app corre con un usuario sin privilegios, no como root.
RUN useradd --system --uid 10001 --no-create-home app && mkdir -p /data && chown app /data
USER app

EXPOSE 8000
# --no-server-header: la respuesta no anuncia qué servidor se usa.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
