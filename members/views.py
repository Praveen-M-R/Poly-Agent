from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Member, Repository, ProjectContribution, RepositoryCollaborator, SyncStatus
from Poly_Agent.config import GIT_ACCESS_KEY, ORGANIZATION
from django.utils import timezone
from django.db.models import Sum, F
import logging

logger = logging.getLogger(__name__)

class OrganizationMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not GIT_ACCESS_KEY:
            logger.error(
                f"GitHub access key is not configured (Current value: {GIT_ACCESS_KEY})"
            )
            return Response(
                {
                    "error": "GitHub access key is not configured",
                    "solution": "Please set GIT_ACCESS_KEY in your .envvar file",
                    "current_value": str(GIT_ACCESS_KEY),
                },
                status=500,
            )

        if not ORGANIZATION:
            logger.error(
                f"GitHub organization is not configured (Current value: {ORGANIZATION})"
            )
            return Response(
                {
                    "error": "GitHub organization is not configured",
                    "solution": "Please set ORGANIZATION in your .envvar file",
                    "current_value": str(ORGANIZATION),
                },
                status=500,
            )

        try:
            # Get sync status
            try:
                sync_status = SyncStatus.objects.get(pk=1)
                last_sync = sync_status.last_members_sync
                sync_age = (timezone.now() - last_sync).total_seconds()
            except SyncStatus.DoesNotExist:
                last_sync = None
                sync_age = float('inf')
            
            # Check if we need to show a sync warning (data older than 15 minutes)
            sync_warning = None
            if last_sync is None:
                sync_warning = "Data has never been synchronized. Please run a sync task."
            elif sync_age > 900:  # 15 minutes in seconds
                sync_warning = f"Data may be outdated. Last sync was {int(sync_age / 60)} minutes ago."
            
            # Get members from database
            members = Member.objects.all()

            # For each member, get their contributor repos
            for member in members:
                member.contributor_repos = list(
                    ProjectContribution.objects.filter(member=member)
                    .values_list('repository__name', flat=True)
                )

            # Convert to list of dicts for response
            members_data = []
            for member in members:
                members_data.append({
                    'username': member.username,
                    'name': member.name,
                    'email': member.email,
                    'avatar_url': member.avatar_url,
                    'contributor_repos': member.contributor_repos,
                })

            return Response(
                {
                    "status": "success",
                    "members": members_data,
                    "sync_info": {
                        "last_sync": last_sync,
                        "sync_age_seconds": sync_age if last_sync else None,
                        "warning": sync_warning,
                    },
                    "stats": {
                        "total": len(members_data),
                    },
                }
            )
        except Exception as e:
            logger.exception("Error fetching organization members")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )


class OrganizationRepositoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not GIT_ACCESS_KEY:
            logger.error(
                f"GitHub access key is not configured (Current value: {GIT_ACCESS_KEY})"
            )
            return Response(
                {
                    "error": "GitHub access key is not configured",
                    "solution": "Please set GIT_ACCESS_KEY in your .envvar file",
                    "current_value": str(GIT_ACCESS_KEY),
                },
                status=500,
            )

        if not ORGANIZATION:
            logger.error(
                f"GitHub organization is not configured (Current value: {ORGANIZATION})"
            )
            return Response(
                {
                    "error": "GitHub organization is not configured",
                    "solution": "Please set ORGANIZATION in your .envvar file",
                    "current_value": str(ORGANIZATION),
                },
                status=500,
            )

        try:
            # Get sync status
            try:
                sync_status = SyncStatus.objects.get(pk=1)
                last_sync = sync_status.last_repositories_sync
                sync_age = (timezone.now() - last_sync).total_seconds()
            except SyncStatus.DoesNotExist:
                last_sync = None
                sync_age = float('inf')
            
            # Check if we need to show a sync warning (data older than 15 minutes)
            sync_warning = None
            if last_sync is None:
                sync_warning = "Data has never been synchronized. Please run a sync task."
            elif sync_age > 900:  # 15 minutes in seconds
                sync_warning = f"Data may be outdated. Last sync was {int(sync_age / 60)} minutes ago."
            
            # Get repositories from database
            repositories = Repository.objects.all()
            
            # Convert to list of dicts for response format
            repositories_data = []
            for repo in repositories:
                repositories_data.append({
                    'name': repo.name,
                    'url': repo.url,
                    'description': repo.description,
                    'isPrivate': repo.is_private,
                    'owner': {'login': ORGANIZATION}
                })

            return Response({
                "status": "success", 
                "repositories": repositories_data,
                "sync_info": {
                    "last_sync": last_sync,
                    "sync_age_seconds": sync_age if last_sync else None,
                    "warning": sync_warning,
                },
            })
        except Exception as e:
            logger.exception("Error fetching organization repositories")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )


class MemberProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        if not GIT_ACCESS_KEY:
            logger.error(
                f"GitHub access key is not configured (Current value: {GIT_ACCESS_KEY})"
            )
            return Response(
                {
                    "error": "GitHub access key is not configured",
                    "solution": "Please set GIT_ACCESS_KEY in your .envvar file",
                    "current_value": str(GIT_ACCESS_KEY[:5]),
                },
                status=500,
            )

        if not ORGANIZATION:
            logger.error(
                f"GitHub organization is not configured (Current value: {ORGANIZATION})"
            )
            return Response(
                {
                    "error": "GitHub organization is not configured",
                    "solution": "Please set ORGANIZATION in your .envvar file",
                    "current_value": str(ORGANIZATION),
                },
                status=500,
            )

        try:
            # Get sync status
            try:
                sync_status = SyncStatus.objects.get(pk=1)
                last_sync = sync_status.last_contributions_sync
                sync_age = (timezone.now() - last_sync).total_seconds()
            except SyncStatus.DoesNotExist:
                last_sync = None
                sync_age = float('inf')
            
            # Check if we need to show a sync warning (data older than 15 minutes)
            sync_warning = None
            if last_sync is None:
                sync_warning = "Data has never been synchronized. Please run a sync task."
            elif sync_age > 900:  # 15 minutes in seconds
                sync_warning = f"Data may be outdated. Last sync was {int(sync_age / 60)} minutes ago."
            
            # Get member from database
            try:
                member = Member.objects.get(username=username)
            except Member.DoesNotExist:
                return Response(
                    {"error": "Member not found"},
                    status=404,
                )
            
            # Get member's contributions
            contributions = ProjectContribution.objects.filter(member=member)
            
            # Get total contributions
            total_contributions = contributions.aggregate(total=Sum('contributions'))['total'] or 0
            
            # Get member's projects (repositories they contribute to)
            projects = []
            per_project_contributions = []
            
            for contribution in contributions:
                repo = contribution.repository
                projects.append({
                    'name': repo.name,
                    'url': repo.url,
                    'description': repo.description,
                    'isPrivate': repo.is_private,
                    'owner': {'login': ORGANIZATION}
                })
                
                per_project_contributions.append({
                    'project_name': repo.name,
                    'contributions': contribution.contributions,
                    'lines_added': contribution.lines_added,
                    'lines_deleted': contribution.lines_deleted,
                    'net_lines': contribution.net_lines,
                })
            
            # Build response
            member_data = {
                'username': member.username,
                'name': member.name,
                'email': member.email,
                'avatar_url': member.avatar_url,
            }
            
            return Response(
                {
                    "status": "success",
                    "member": member_data,
                    "projects": projects,
                    "total_contributions": total_contributions,
                    "per_project_contributions": per_project_contributions,
                    "sync_info": {
                        "last_sync": last_sync,
                        "sync_age_seconds": sync_age if last_sync else None,
                        "warning": sync_warning,
                    },
                }
            )
        except Exception as e:
            logger.exception("Error fetching member profile")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )


class RepositoryContributorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, repository_name):
        if not GIT_ACCESS_KEY:
            logger.error(
                f"GitHub access key is not configured (Current value: {GIT_ACCESS_KEY})"
            )
            return Response(
                {
                    "error": "GitHub access key is not configured",
                    "solution": "Please set GIT_ACCESS_KEY in your .envvar file",
                    "current_value": str(GIT_ACCESS_KEY[:5]),
                },
                status=500,
            )

        if not ORGANIZATION:
            logger.error(
                f"GitHub organization is not configured (Current value: {ORGANIZATION})"
            )
            return Response(
                {
                    "error": "GitHub organization is not configured",
                    "solution": "Please set ORGANIZATION in your .envvar file",
                    "current_value": str(ORGANIZATION),
                },
                status=500,
            )

        try:
            # Get sync status
            try:
                sync_status = SyncStatus.objects.get(pk=1)
                last_sync = sync_status.last_contributions_sync
                sync_age = (timezone.now() - last_sync).total_seconds()
            except SyncStatus.DoesNotExist:
                last_sync = None
                sync_age = float('inf')
            
            # Check if we need to show a sync warning (data older than 15 minutes)
            sync_warning = None
            if last_sync is None:
                sync_warning = "Data has never been synchronized. Please run a sync task."
            elif sync_age > 900:  # 15 minutes in seconds
                sync_warning = f"Data may be outdated. Last sync was {int(sync_age / 60)} minutes ago."
            
            # Get repository from database
            try:
                repository = Repository.objects.get(name=repository_name)
            except Repository.DoesNotExist:
                return Response(
                    {"error": "Repository not found"},
                    status=404,
                )
            
            # Get collaborators
            collaborators_data = []
            for collab in RepositoryCollaborator.objects.filter(repository=repository):
                member = collab.member
                collaborators_data.append({
                    'login': member.username,
                    'name': member.name,
                    'email': member.email,
                    'avatarUrl': member.avatar_url,
                    'role': collab.role or 'Collaborator'
                })
            
            # Get contributors
            contributors_data = []
            for contrib in ProjectContribution.objects.filter(repository=repository):
                member = contrib.member
                contributors_data.append({
                    'login': member.username,
                    'name': member.name,
                    'contributions': contrib.contributions,
                    'avatar_url': member.avatar_url,
                })
            
            return Response(
                {
                    "status": "success",
                    "repository": repository_name,
                    "collaborators": collaborators_data,
                    "contributors": contributors_data,
                    "sync_info": {
                        "last_sync": last_sync,
                        "sync_age_seconds": sync_age if last_sync else None,
                        "warning": sync_warning,
                    },
                }
            )
        except Exception as e:
            logger.exception("Error fetching repository contributors and collaborators")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )


class TriggerSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Endpoint to manually trigger a GitHub data sync."""
        from .tasks import sync_all_github_data
        
        try:
            # Start the sync task
            task = sync_all_github_data.delay()
            
            return Response(
                {
                    "status": "success",
                    "message": "GitHub data sync started",
                    "task_id": task.id,
                }
            )
        except Exception as e:
            logger.exception("Error triggering sync task")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )
    
    def get(self, request):
        """Get sync status information."""
        try:
            try:
                sync_status = SyncStatus.objects.get(pk=1)
            except SyncStatus.DoesNotExist:
                return Response(
                    {
                        "status": "warning",
                        "message": "No sync has been performed yet",
                        "sync_status": None
                    }
                )
            
            now = timezone.now()
            
            return Response(
                {
                    "status": "success",
                    "sync_status": {
                        "last_members_sync": sync_status.last_members_sync,
                        "last_members_sync_age": (now - sync_status.last_members_sync).total_seconds(),
                        "last_repositories_sync": sync_status.last_repositories_sync,
                        "last_repositories_sync_age": (now - sync_status.last_repositories_sync).total_seconds(),
                        "last_contributions_sync": sync_status.last_contributions_sync,
                        "last_contributions_sync_age": (now - sync_status.last_contributions_sync).total_seconds(),
                    }
                }
            )
        except Exception as e:
            logger.exception("Error fetching sync status")
            return Response(
                {"error": str(e), "solution": "Check server logs for more details"},
                status=500,
            )
