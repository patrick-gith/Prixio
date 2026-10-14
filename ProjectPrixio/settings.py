# ProjectPrixio/settings.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# SÉCURITÉ
# ==========================================================

LOCAL_SECRET_KEY = "django-insecure-local-dev-only-change-this"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", LOCAL_SECRET_KEY)

DEBUG = os.environ.get("DEBUG", "True").strip().lower() in ("true", "1", "yes")

if os.environ.get("RENDER"):
    if not os.environ.get("DJANGO_SECRET_KEY") or SECRET_KEY == LOCAL_SECRET_KEY:
        raise RuntimeError(
            "Configure une vraie DJANGO_SECRET_KEY dans les variables "
            "d'environnement de Render."
        )
    if DEBUG:
        raise RuntimeError("DEBUG doit être False en production sur Render.")

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,prixio.onrender.com",
    ).split(",") if h.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    auto_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if auto_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(auto_origin)

# ==========================================================
# APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "corsheaders",
    "rosetta",

    "CatalogApp",
    "PricingApp",
    "CoreApp",
    "PrixioApp",
]

# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==========================================================
# URLS ET TEMPLATES
# ==========================================================

ROOT_URLCONF = "ProjectPrixio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates",
                 BASE_DIR / "ProjectPrixio" / "templates",  # ajout
                 ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "PrixioApp.context_processors.prixio_context",
            ],
        },
    },
]

WSGI_APPLICATION = "ProjectPrixio.wsgi.application"

# ==========================================================
# BASE DE DONNÉES
# ==========================================================

DATABASE_URL = os.environ.get("RENDER_DATABASE_URL")

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL, conn_max_age=0, conn_health_checks=True,
        )
    }
else:
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Prixiodb',
        'USER': 'guizo',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# ==========================================================
# AUTHENTIFICATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ==========================================================
# INTERNATIONALISATION
# ==========================================================

USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Douala"

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# ==========================================================
# FICHIERS STATIQUES ET MÉDIAS
# ==========================================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# En DEV / tests : storage simple, pas de manifest, pas de hash.
# En PROD   : Manifest + compression via WhiteNoise.
if DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
# ==========================================================
# SPÉCIFIQUE PRIXIO
# ==========================================================

BASE_CURRENCY = os.environ.get("BASE_CURRENCY", "EUR")

COMPANY_NAME = os.environ.get("COMPANY_NAME", "Prixio")
COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "contact@prixio.app")
# ==========================================================
# SÉCURITÉ HTTPS
# ==========================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = DEBUG

# Remplace EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
    EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", COMPANY_EMAIL)



# Score d'opportunité minimum pour déclencher une alerte
DEFAULT_ALERT_THRESHOLD = 75

# ==========================================================
# AUTHENTIFICATION (login / logout)
# ==========================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")
EBAY_CLIENT_ID='ton_app_id'
EBAY_CLIENT_SECRET='ton_cert_id'
EBAY_MARKETPLACE_ID='EBAY_FR'

# ==========================================================
# CELERY — Traitement asynchrone
# ==========================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
# Compat Celery 6.0 — évite le warning de dépréciation
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Format des messages
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Fuseau horaire (hérite du TIME_ZONE Django)
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Suivi des tâches
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True

# Limites de temps
CELERY_TASK_TIME_LIMIT = 30 * 60          # 30 min hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60     # 25 min soft limit (lève une exception)
CELERY_TASK_ACKS_LATE = True              # acquitte après exécution (fiabilité)
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # remet en file si worker crash

# Worker
CELERY_WORKER_PREFETCH_MULTIPLIER = 1     # 1 tâche à la fois par worker
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100   # recycle après 100 tâches (fuites mémoire)
CELERY_WORKER_CONCURRENCY = int(os.environ.get("CELERY_CONCURRENCY", "2"))

# Files d'attente : on sépare batch (lourd) et collect (léger)
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    "default": {"exchange": "default", "routing_key": "default"},
    "batch":   {"exchange": "batch",   "routing_key": "batch"},
    "collect": {"exchange": "collect", "routing_key": "collect"},
}

# Retry par défaut
CELERY_TASK_ANNOTATIONS = {
    "*": {
        "max_retries": 2,
        "default_retry_delay": 60,
        "retry_backoff": True,
        "retry_backoff_max": 600,
        "retry_jitter": True,
    },
}

# Flower (dashboard)
CELERY_FLOWER_PORT = int(os.environ.get("FLOWER_PORT", "5555"))
CELERY_FLOWER_BASIC_AUTH = os.environ.get("FLOWER_BASIC_AUTH", "")  # "user:pass"
# ==========================================================
# CELERY — Worker state
# ==========================================================
# Nécessaire pour Celery 5.4+ : sinon AttributeError sur `worker_state_db`
CELERY_WORKER_STATE_DB = os.environ.get("CELERY_WORKER_STATE_DB", "")