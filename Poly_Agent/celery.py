import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Poly_Agent.settings')

app = Celery('Poly_Agent')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Define the beat schedule to run periodic tasks
app.conf.beat_schedule = {
    'check-health-checks-every-5-minutes': {
        'task': 'health_check.tasks.check_health_checks',
        'schedule': 60 * 5,  # every 5 minutes
    },
    'cleanup-old-health-check-logs': {
        'task': 'health_check.tasks.cleanup_old_logs',
        'schedule': crontab(minute=0, hour=0),  # every day at midnight
        'kwargs': {'days': 30},
    },
    'sync-github-profiles-daily': {
        'task': 'codetrack.tasks.sync_all_github_profiles',
        'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM every day
        'args': (),
    },
    'check-repository-access-weekly': {
        'task': 'codetrack.tasks.check_removed_repository_access',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Run at 3:00 AM every Monday
        'args': (),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 