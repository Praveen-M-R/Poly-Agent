from rest_framework import serializers
from .models import GitHubProfile, Repository, UserRepositoryStats, CommitHistory

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ['id', 'name', 'owner', 'full_name', 'url', 'description', 'is_private', 'created_at']

class GitHubProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = GitHubProfile
        fields = ['id', 'username', 'github_username', 'github_email', 'avatar_url', 'last_synced']

class UserRepositoryStatsSerializer(serializers.ModelSerializer):
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    repository_url = serializers.URLField(source='repository.url', read_only=True)
    repository_description = serializers.CharField(source='repository.description', read_only=True)
    repository_is_private = serializers.BooleanField(source='repository.is_private', read_only=True)
    
    class Meta:
        model = UserRepositoryStats
        fields = [
            'id', 'repository', 'repository_name', 'repository_url', 'repository_description', 
            'repository_is_private', 'commits', 'lines_added', 'lines_deleted', 
            'net_lines', 'last_updated'
        ]

class CommitHistorySerializer(serializers.ModelSerializer):
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    github_username = serializers.CharField(source='profile.github_username', read_only=True)
    
    class Meta:
        model = CommitHistory
        fields = [
            'id', 'repository', 'repository_name', 'github_username',
            'commit_hash', 'commit_message', 'commit_date', 
            'lines_added', 'lines_deleted'
        ]

class UserGitHubStatsSerializer(serializers.Serializer):
    username = serializers.CharField()
    github_username = serializers.CharField()
    avatar_url = serializers.URLField(allow_null=True)
    total_commits = serializers.IntegerField()
    total_lines_added = serializers.IntegerField()
    total_lines_deleted = serializers.IntegerField()
    net_lines = serializers.IntegerField()
    repositories_count = serializers.IntegerField()
    last_synced = serializers.DateTimeField() 