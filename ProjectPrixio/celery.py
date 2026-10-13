# ProjectPrixio/celery.py
"""
Configuration Celery pour Prixio.

Ce fichier est importé au démarrage de Django (via __init__.py),
ce qui garantit que les tasks sont enregistrées dès le boot.
"""
import os

from celery import Celery

# Django doit être configuré AVANT que Celery ne cherche les tasks.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ProjectPrixio.settings")

app = Celery("prixio")

# Lit la config depuis settings.py, uniquement les clés préfixées CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-découvre les tasks.py dans chaque app installée
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de test : celery -A ProjectPrixio call ProjectPrixio.celery.debug_task"""
    print(f"Request: {self.request!r}")





    """# Sur Linux/macOS
celery -A ProjectPrixio worker -l info -Q batch,collect,default

# Sur Windows (nécessite --pool=solo)
celery -A ProjectPrixio worker -l info --pool=solo -Q batch,collect,default




celery -A ProjectPrixio flower --port=5555



celery -A ProjectPrixio call ProjectPrixio.celery.debug_task


"""