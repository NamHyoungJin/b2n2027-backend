# apps/participants/apps.py
from django.apps import AppConfig


class ParticipantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.participants'
    verbose_name = '참여자 관리'
