# ============================================================
# Prixio — Dockerfile multi-stage
# ============================================================
# Cible : Linux slim + WeasyPrint + Gunicorn
# Build en 2 étapes pour réduire la taille finale de ~60%
# ============================================================

# ============================================================
# STAGE 1 — Builder
# ============================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système nécessaires à la COMPILATION
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python dans un dossier isolé
WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ============================================================
# STAGE 2 — Runtime
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=ProjectPrixio.settings

# Dépendances système nécessaires à l'EXÉCUTION
# - WeasyPrint : pango, harfbuzz, cairo, gdk-pixbuf
# - Pillow     : libjpeg, libopenjp2
# - fonts      : DejaVu (fallback pour les PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libjpeg62-turbo \
    libopenjp2-7 \
    shared-mime-info \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root
RUN groupadd --system --gid 1000 prixio && \
    useradd --system --uid 1000 --gid prixio --create-home prixio

# Récupérer le venv du builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copier le code
COPY --chown=prixio:prixio . .

# Créer les dossiers runtime (avec les bons droits)
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R prixio:prixio /app/staticfiles /app/media /app/logs

USER prixio

# Collecter les statiques (nécessite SECRET_KEY pour ne pas crasher)
RUN DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
    python manage.py collectstatic --noinput --clear

EXPOSE 8000

# Healthcheck (Render / Kubernetes peuvent s'en servir)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz/ || exit 1

# Gunicorn avec config de prod
CMD ["gunicorn", "ProjectPrixio.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]