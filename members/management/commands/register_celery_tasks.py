import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from members.tasks import (
    sync_members,
    sync_repositories,
    sync_repository_data,
    sync_all_github_data,
)


class Command(BaseCommand):
    help = "Register periodic tasks for all members.* tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Interval in minutes (default: 5)',
        )

    def handle(self, *args, **options):
        interval_minutes = options['minutes']
        self.stdout.write(self.style.SUCCESS(f"Registering tasks with {interval_minutes}-minute interval"))
        
        # Create (or reuse) an interval schedule
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=interval_minutes,
            period=IntervalSchedule.MINUTES,
        )

        # Map task objects to a friendly beat name
        task_map = {
            sync_members: "Sync members",
            sync_repositories: "Sync repositories",
            sync_repository_data: "Sync repository data",
            sync_all_github_data: "Sync all GitHub data",
        }

        # Create one PeriodicTask per Celery task
        for task_obj, beat_name in task_map.items():
            PeriodicTask.objects.update_or_create(
                task=task_obj.name,  # eg. "members.tasks.sync_members"
                defaults={
                    "name": f"[Auto] {beat_name}",
                    "interval": schedule,
                    "args": json.dumps([]),
                    "enabled": True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Registered {beat_name}"))

        self.stdout.write(self.style.SUCCESS("✅ All tasks registered!")) 