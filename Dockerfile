FROM python:3.12-slim

# Kein .pyc-Schreiben, Logs sofort ausgeben
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies zuerst installieren (Layer-Cache)
COPY requirements.txt .
# pywin32 ist Windows-only – wird im Linux-Image herausgefiltert
RUN grep -v "^pywin32" requirements.txt > requirements.linux.txt && \
    pip install --no-cache-dir -r requirements.linux.txt && \
    rm requirements.linux.txt

# Quellcode kopieren
COPY . .

# Entrypoint ausführbar machen
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
