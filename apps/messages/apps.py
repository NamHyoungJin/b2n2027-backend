from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messages"
    label = "b2n_messages"
    verbose_name = "관리자 문자·이메일"
