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

# ============================================================
# ENTRYPOINT — migrations + superuser + Gunicorn
# ============================================================
# On génère le script avec printf (pas de heredoc, non supporté
# proprement par Dockerfile). Chaque ligne est ajoutée via %s\n.
RUN printf '%s\n' \
    '#!/usr/bin/env sh' \
    'set -e' \
    '' \
    'echo "▶ Running migrations..."' \
    'python manage.py migrate --noinput' \
    '' \
    'echo "▶ Ensuring superuser exists..."' \
    'python manage.py shell << PYEOF' \
    'import os' \
    'from django.contrib.auth import get_user_model' \
    'User = get_user_model()' \
    'username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")' \
    'email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")' \
    'password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")' \
    'if username and password:' \
    '    if not User.objects.filter(username=username).exists():' \
    '        User.objects.create_superuser(username, email, password)' \
    '        print(f"✓ Superuser {username!r} créé")' \
    '    else:' \
    '        print(f"✓ Superuser {username!r} existe déjà")' \
    'else:' \
    '    print("⏭ Variables DJANGO_SUPERUSER_* absentes → skip")' \
    'PYEOF' \
    '' \
    'echo "▶ Starting Gunicorn on port ${PORT:-8000}..."' \
    'exec gunicorn ProjectPrixio.wsgi:application \' \
    '    --bind "0.0.0.0:${PORT:-8000}" \' \
    '    --workers 3 \' \
    '    --worker-class gthread \' \
    '    --threads 2 \' \
    '    --timeout 60 \' \
    '    --graceful-timeout 30 \' \
    '    --keep-alive 5 \' \
    '    --max-requests 1000 \' \
    '    --max-requests-jitter 100 \' \
    '    --access-logfile - \' \
    '    --error-logfile -' \
    > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown prixio:prixio /app/entrypoint.sh

USER prixio

# Collecter les statiques (DEBUG=False pour générer le manifest)
RUN DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
    DEBUG=False \
    python manage.py collectstatic --noinput --clear

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]