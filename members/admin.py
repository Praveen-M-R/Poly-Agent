from django.contrib import admin
from .models import Member, Repository, ProjectContribution, RepositoryCollaborator, SyncStatus

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'email', 'last_updated')
    search_fields = ('username', 'name', 'email')

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_private', 'last_updated')
    list_filter = ('is_private',)
    search_fields = ('name', 'description')

@admin.register(ProjectContribution)
class ProjectContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'repository', 'contributions', 'lines_added', 'lines_deleted', 'net_lines')
    list_filter = ('repository',)
    search_fields = ('member__username', 'repository__name')

@admin.register(RepositoryCollaborator)
class RepositoryCollaboratorAdmin(admin.ModelAdmin):
    list_display = ('member', 'repository', 'role')
    list_filter = ('repository', 'role')
    search_fields = ('member__username', 'repository__name')

@admin.register(SyncStatus)
class SyncStatusAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'last_members_sync', 'last_repositories_sync', 'last_contributions_sync')
    def has_add_permission(self, request):
        # Check if any SyncStatus objects exist
        return SyncStatus.objects.count() == 0
