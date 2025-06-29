from django.contrib import admin
from .models import GitHubProfile, Repository, UserRepositoryStats, CommitHistory
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

@admin.register(GitHubProfile)
class GitHubProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'github_username', 'github_email', 'last_synced', 'get_repository_count')
    search_fields = ('user__username', 'github_username', 'github_email')
    list_filter = ('last_synced',)
    ordering = ('-last_synced',)
    actions = ['sync_selected_profiles', 'check_repository_access']
    
    def get_repository_count(self, obj):
        return UserRepositoryStats.objects.filter(profile=obj).count()
    get_repository_count.short_description = 'Repositories'
    
    def sync_selected_profiles(self, request, queryset):
        from .services import GitHubService
        
        github_service = GitHubService()
        success_count = 0
        error_count = 0
        
        for profile in queryset:
            try:
                github_service.sync_user_repositories(profile)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f"Error syncing {profile.github_username}: {str(e)}", 
                    level=messages.ERROR
                )
        
        if success_count > 0:
            self.message_user(
                request, 
                f"Successfully synced {success_count} profiles.", 
                level=messages.SUCCESS
            )
        
        if error_count == 0 and success_count == 0:
            self.message_user(
                request, 
                "No profiles were synced.", 
                level=messages.WARNING
            )
    sync_selected_profiles.short_description = "Sync selected GitHub profiles"
    
    def check_repository_access(self, request, queryset):
        from .services import GitHubService
        
        github_service = GitHubService()
        success_count = 0
        error_count = 0
        removed_count = 0
        
        for profile in queryset:
            try:
                # Get current repositories
                repositories = github_service.get_user_org_repositories(profile.github_username)
                
                # Extract repository IDs
                if repositories:
                    repo_full_names = [repo.get('nameWithOwner') for repo in repositories]
                    repo_ids = list(Repository.objects.filter(full_name__in=repo_full_names).values_list('id', flat=True))
                else:
                    repo_ids = []
                
                # Clean up repository access
                before_count = UserRepositoryStats.objects.filter(profile=profile).count()
                github_service.clean_up_removed_repositories(profile, repo_ids)
                after_count = UserRepositoryStats.objects.filter(profile=profile).count()
                
                # Calculate how many were removed
                removed = before_count - after_count
                removed_count += removed
                
                success_count += 1
                
                if removed > 0:
                    self.message_user(
                        request, 
                        f"Removed {removed} repository access records for {profile.github_username}.", 
                        level=messages.INFO
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f"Error checking repository access for {profile.github_username}: {str(e)}", 
                    level=messages.ERROR
                )
        
        if success_count > 0:
            self.message_user(
                request, 
                f"Successfully checked {success_count} profiles. Removed {removed_count} repository access records total.", 
                level=messages.SUCCESS
            )
        
        if error_count == 0 and success_count == 0:
            self.message_user(
                request, 
                "No profiles were checked.", 
                level=messages.WARNING
            )
    check_repository_access.short_description = "Check repository access for selected profiles"

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'full_name', 'is_private', 'get_contributor_count')
    search_fields = ('name', 'owner', 'full_name')
    list_filter = ('owner', 'is_private')
    ordering = ('owner', 'name')
    
    def get_contributor_count(self, obj):
        return UserRepositoryStats.objects.filter(repository=obj).count()
    get_contributor_count.short_description = 'Contributors'

@admin.register(UserRepositoryStats)
class UserRepositoryStatsAdmin(admin.ModelAdmin):
    list_display = ('profile', 'repository_link', 'commits', 'lines_added', 'lines_deleted', 'net_lines', 'last_updated')
    search_fields = ('profile__github_username', 'repository__name', 'repository__owner')
    list_filter = ('repository__owner', 'last_updated')
    ordering = ('-last_updated',)
    
    def repository_link(self, obj):
        return format_html('<a href="{}">{}</a>', obj.repository.url, obj.repository.full_name)
    repository_link.short_description = 'Repository'

@admin.register(CommitHistory)
class CommitHistoryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'repository', 'short_commit_hash', 'commit_message_preview', 'commit_date', 'lines_added', 'lines_deleted')
    search_fields = ('profile__github_username', 'repository__name', 'commit_hash', 'commit_message')
    list_filter = ('commit_date', 'repository__owner')
    ordering = ('-commit_date',)
    
    def short_commit_hash(self, obj):
        return obj.commit_hash[:7]
    short_commit_hash.short_description = 'Commit'
    
    def commit_message_preview(self, obj):
        if len(obj.commit_message) > 50:
            return obj.commit_message[:50] + '...'
        return obj.commit_message
    commit_message_preview.short_description = 'Message'
