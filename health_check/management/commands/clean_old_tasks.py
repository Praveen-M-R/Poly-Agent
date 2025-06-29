from django.core.management.base import BaseCommand, CommandError
from django_celery_beat.models import PeriodicTask

class Command(BaseCommand):
    help = 'Clean up old periodic tasks that are no longer needed'

    def handle(self, *args, **options):
        # Delete tasks from the members app
        tasks_to_remove = PeriodicTask.objects.filter(task__startswith='members.tasks.')
        count = tasks_to_remove.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(f'Found {count} tasks from members app to remove'))
            tasks_to_remove.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully removed {count} tasks'))
        else:
            self.stdout.write(self.style.SUCCESS('No member tasks found to remove'))
        
        # Delete tasks from the checks app
        checks_tasks = PeriodicTask.objects.filter(task__startswith='checks.tasks.')
        count = checks_tasks.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(f'Found {count} tasks from checks app to remove'))
            checks_tasks.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully removed {count} tasks'))
        else:
            self.stdout.write(self.style.SUCCESS('No checks tasks found to remove'))
            
        # List remaining tasks
        remaining_tasks = PeriodicTask.objects.all()
        if remaining_tasks.exists():
            self.stdout.write(self.style.SUCCESS('Remaining periodic tasks:'))
            for task in remaining_tasks:
                self.stdout.write(f'- {task.name}: {task.task}')
        else:
            self.stdout.write(self.style.SUCCESS('No periodic tasks remaining')) 