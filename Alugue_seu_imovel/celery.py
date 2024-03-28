import os

from datetime import timedelta
from celery.schedules import crontab
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Alugue_seu_imovel.settings')

app = Celery('Alugue_seu_imovel')
app.conf.update(timezone='America/Sao_Paulo')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Settings:

# Gabarito e exemplo \/:
# 'schedule': timedelta(minutes=1)
# 'schedule': crontab(hour=0, minute=1)
# app.conf.beat_schedule = {
#     'print-cavalo-every-10-second': {
#         'task': 'core.tasks.print_cavalo',
#         'schedule': timedelta(seconds=10),
#         'args': ('Argumento 1!', 'Argumento 2!'),
#     }
# }

app.conf.beat_schedule = {
    '1-apagar-validacoes-vencidas': {
        'task': 'core.tasks.temp_activations_tokens_deletions',
        'schedule': timedelta(hours=6),
    },
    '2-apagar-usuarios-inativos': {
        'task': 'core.tasks.temp_inative_users_deletions',
        'schedule': timedelta(hours=6),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
