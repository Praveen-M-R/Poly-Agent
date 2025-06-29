from django.urls import path
from .views import OrganizationMembersView, OrganizationRepositoriesView, MemberProfileView, RepositoryContributorsView, TriggerSyncView

urlpatterns = [
    path('members/', OrganizationMembersView.as_view(), name='organization-members'),
    path('members/<str:username>/', MemberProfileView.as_view(), name='member-profile'),
    path('repositories/', OrganizationRepositoriesView.as_view(), name='organization-repositories'),
    path('repositories/<str:repository_name>/contributors/', RepositoryContributorsView.as_view(), name='repository-contributors'),
    path('sync/', TriggerSyncView.as_view(), name='trigger-sync'),
]
