from django.urls import path
from .views import (
    UserStatsView,
    UserRepositoriesView,
    CommitHistoryView,
    SyncGitHubDataView,
    link_github_user
)

app_name = 'codetrack'

urlpatterns = [
    # Get GitHub stats for the current user
    path('stats/', UserStatsView.as_view(), name='user_stats'),
    
    # Get repositories and their stats for the current user
    path('repositories/', UserRepositoriesView.as_view(), name='user_repositories'),
    
    # Get commit history for a specific repository
    path('repositories/<int:repository_id>/commits/', CommitHistoryView.as_view(), name='commit_history'),
    
    # Sync GitHub data for the current user
    path('sync/', SyncGitHubDataView.as_view(), name='sync_github_data'),
    
    # Admin tools
    path('admin/link-github-user/', link_github_user, name='link_github_user'),
] 