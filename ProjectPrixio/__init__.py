# ProjectPrixio/__init__.py
"""
Importe l'app Celery dès le démarrage de Django.

Sans cet import, le décorateur @shared_task ne serait pas enregistré
au moment où Django charge les apps, et les workers Celery ne
verraient aucune tâche.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)