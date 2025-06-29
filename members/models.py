from django.db import models
from django.utils import timezone

class Member(models.Model):
    username = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.username})"

class Repository(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        privacy = "Private" if self.is_private else "Public"
        return f"{self.name} ({privacy})"

class ProjectContribution(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='contributions')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='contributions')
    contributions = models.IntegerField(default=0)  # Number of commits
    lines_added = models.IntegerField(default=0)
    lines_deleted = models.IntegerField(default=0)
    net_lines = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('member', 'repository')

    def __str__(self):
        return f"{self.member.username} → {self.repository.name} ({self.contributions} commits)"

class RepositoryCollaborator(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='collaborations')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='collaborators')
    role = models.CharField(max_length=100, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('member', 'repository')

    def __str__(self):
        return f"{self.member.username} → {self.repository.name} ({self.role or 'Collaborator'})"

class SyncStatus(models.Model):
    """Tracks the last successful sync of GitHub data"""
    last_members_sync = models.DateTimeField(default=timezone.now)
    last_repositories_sync = models.DateTimeField(default=timezone.now)
    last_contributions_sync = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "GitHub Data Sync Status"
