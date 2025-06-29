from django.db import models
from django.utils import timezone
from django.conf import settings

class GitHubProfile(models.Model):
    """
    Stores GitHub profile information for a user
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='github_profile')
    github_username = models.CharField(max_length=255)
    github_email = models.EmailField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    last_synced = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"GitHub Profile: {self.user.username} ({self.github_username})"

class Repository(models.Model):
    """
    Stores repository information
    """
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.full_name

class UserRepositoryStats(models.Model):
    """
    Stores repository statistics for a specific user
    """
    profile = models.ForeignKey(GitHubProfile, on_delete=models.CASCADE, related_name='repo_stats')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='user_stats')
    commits = models.IntegerField(default=0)
    lines_added = models.IntegerField(default=0)
    lines_deleted = models.IntegerField(default=0)
    net_lines = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('profile', 'repository')
        verbose_name_plural = 'User repository statistics'
    
    def __str__(self):
        return f"{self.profile.github_username} - {self.repository.name} Stats"

class CommitHistory(models.Model):
    """
    Stores commit history for a user and repository
    """
    profile = models.ForeignKey(GitHubProfile, on_delete=models.CASCADE, related_name='commits')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    commit_hash = models.CharField(max_length=40)
    commit_message = models.TextField()
    commit_date = models.DateTimeField()
    lines_added = models.IntegerField(default=0)
    lines_deleted = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('repository', 'commit_hash')
    
    def __str__(self):
        return f"{self.repository.name} - {self.commit_hash[:7]}"
