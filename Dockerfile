FROM python:3.12-slim

# Kein .pyc-Schreiben, Logs sofort ausgeben
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies zuerst installieren (Layer-Cache)
COPY requirements.txt .
# pywin32 ist Windows-only – wird herausgefiltert.
# Python übernimmt das Parsen, damit UTF-16-kodierte requirements.txt korrekt verarbeitet werden.
RUN python - <<'EOF'
with open("requirements.txt", "rb") as f:
    raw = f.read()
if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
    content = raw.decode("utf-16")
elif raw[:3] == b"\xef\xbb\xbf":
    content = raw.decode("utf-8-sig")
else:
    content = raw.decode("utf-8")
lines = [l for l in content.splitlines() if not l.lower().startswith("pywin32")]
with open("requirements.linux.txt", "w") as f:
    f.write("\n".join(lines))
EOF
RUN pip install --no-cache-dir -r requirements.linux.txt && rm requirements.linux.txt

# Quellcode kopieren
COPY . .

# Entrypoint ausführbar machen
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
