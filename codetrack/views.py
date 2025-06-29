from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import GitHubProfile, Repository, UserRepositoryStats, CommitHistory
from .serializers import (
    GitHubProfileSerializer, 
    RepositorySerializer, 
    UserRepositoryStatsSerializer, 
    CommitHistorySerializer,
    UserGitHubStatsSerializer
)
from .services import GitHubService

import logging
import traceback

# Set up logger for the codetrack app
logger = logging.getLogger('codetrack')

class UserStatsView(APIView):
    """
    Get GitHub statistics for the current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logger.info(f"[UserStatsView] Received request from user: {request.user.username}")
        
        try:
            # Get GitHub service
            github_service = GitHubService()
            logger.debug(f"[UserStatsView] Successfully initialized GitHubService")
            
            # Get user stats
            logger.debug(f"[UserStatsView] Fetching stats for user: {request.user.username}")
            if hasattr(request.user, 'email'):
                logger.debug(f"[UserStatsView] User email: {request.user.email}")
            stats = github_service.get_user_stats(request.user)
            
            if not stats:
                logger.warning(f"[UserStatsView] GitHub profile not found for user: {request.user.username}")
                
                # Check if sync endpoint has been called before
                has_sync_attempt = False
                try:
                    # Check if there are any sync records in our database for this user
                    from .models import GitHubProfile
                    profile_count = GitHubProfile.objects.filter(user=request.user).count()
                    has_sync_attempt = profile_count > 0
                except Exception as e:
                    logger.error(f"[UserStatsView] Error checking sync history: {str(e)}")
                
                # Create a helpful error response with instructions
                return Response(
                    {
                        "error": "GitHub profile not found. Please connect your GitHub account.",
                        "user": request.user.username,
                        "email": request.user.email if hasattr(request.user, 'email') else None,
                        "has_previous_sync": has_sync_attempt,
                        "next_steps": [
                            "Use POST to /api/codetrack/sync/ with {'github_username': 'your-github-username'} to connect your account.",
                            "Your GitHub account will be linked and repositories will be synchronized automatically."
                        ],
                        "example": {
                            "url": "/api/codetrack/sync/",
                            "method": "POST",
                            "body": {"github_username": "your-github-username"}
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serialize and return
            logger.debug(f"[UserStatsView] Serializing stats data for user: {request.user.username}")
            serializer = UserGitHubStatsSerializer(stats)
            logger.info(f"[UserStatsView] Successfully retrieved stats for user: {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            error_message = f"[UserStatsView] Error retrieving GitHub stats: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return Response(
                {
                    "error": error_message,
                    "help": "Use POST to /api/codetrack/sync/ with {'github_username': 'your-github-username'} to connect your GitHub account."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserRepositoriesView(APIView):
    """
    Get repositories and their stats for the current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logger.info(f"[UserRepositoriesView] Received request from user: {request.user.username}")
        
        try:
            from .models import GitHubProfile, UserRepositoryStats, Repository
            from Poly_Agent.config import ORGANIZATION
            
            logger.debug(f"[UserRepositoriesView] Fetching GitHub profile for user: {request.user.username}")
            # Get user's GitHub profile
            profile = GitHubProfile.objects.get(user=request.user)
            logger.debug(f"[UserRepositoriesView] Found GitHub profile: {profile.github_username}")
            
            # Log organization info
            logger.debug(f"[UserRepositoriesView] Using organization: {ORGANIZATION}")
            
            # Get repository stats for this user
            logger.debug(f"[UserRepositoriesView] Fetching repository stats for profile: {profile.github_username}")
            
            # First get all repositories for the user
            repo_stats = UserRepositoryStats.objects.filter(profile=profile)
            logger.debug(f"[UserRepositoriesView] Found {repo_stats.count()} total repositories for user")
            
            # Get the count of repos that belong to the organization
            if ORGANIZATION:
                org_repos = Repository.objects.filter(owner=ORGANIZATION)
                logger.debug(f"[UserRepositoriesView] Found {org_repos.count()} total organization repositories")
                
                # Get the count of org repos this user has contributed to
                user_org_repos = repo_stats.filter(repository__owner=ORGANIZATION)
                logger.debug(f"[UserRepositoriesView] User has contributed to {user_org_repos.count()} organization repositories")
                
                # Filter repo_stats to only include organization repositories
                repo_stats = user_org_repos
                logger.debug(f"[UserRepositoriesView] Filtered to {repo_stats.count()} organization repositories")
            
            # Serialize and return
            serializer = UserRepositoryStatsSerializer(repo_stats, many=True)
            
            response_data = {
                "status": "success",
                "organization": ORGANIZATION,
                "projects": serializer.data,
                "sync_info": {
                    "last_sync": profile.last_synced,
                    "sync_age_seconds": (timezone.now() - profile.last_synced).total_seconds(),
                    "warning": "Data may be outdated" if (timezone.now() - profile.last_synced).total_seconds() > 3600 else None,
                },
            }
            
            logger.info(f"[UserRepositoriesView] Successfully retrieved repositories for user: {request.user.username}")
            return Response(response_data)
            
        except GitHubProfile.DoesNotExist:
            error_message = f"[UserRepositoriesView] GitHub profile not found for user: {request.user.username}"
            logger.warning(error_message)
            return Response(
                {"error": "GitHub profile not found. Please connect your GitHub account."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            error_message = f"[UserRepositoriesView] Error fetching user repositories: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CommitHistoryView(APIView):
    """
    Get commit history for a specific repository
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, repository_id):
        logger.info(f"[CommitHistoryView] Received request from user: {request.user.username} for repository ID: {repository_id}")
        
        try:
            from .models import GitHubProfile, Repository, CommitHistory
            
            # Get user's GitHub profile
            logger.debug(f"[CommitHistoryView] Fetching GitHub profile for user: {request.user.username}")
            profile = GitHubProfile.objects.get(user=request.user)
            
            # Get repository
            logger.debug(f"[CommitHistoryView] Fetching repository with ID: {repository_id}")
            repository = get_object_or_404(Repository, id=repository_id)
            logger.debug(f"[CommitHistoryView] Found repository: {repository.full_name}")
            
            # Get commits for this repository
            logger.debug(f"[CommitHistoryView] Fetching commits for repository: {repository.full_name}")
            commits = CommitHistory.objects.filter(
                profile=profile,
                repository=repository
            ).order_by('-commit_date')
            logger.debug(f"[CommitHistoryView] Found {commits.count()} commits")
            
            # Apply pagination if needed
            
            # Serialize and return
            serializer = CommitHistorySerializer(commits, many=True)
            
            response_data = {
                "status": "success",
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "full_name": repository.full_name,
                    "url": repository.url
                },
                "commits": serializer.data
            }
            
            logger.info(f"[CommitHistoryView] Successfully retrieved commits for repository ID: {repository_id}")
            return Response(response_data)
            
        except GitHubProfile.DoesNotExist:
            error_message = f"[CommitHistoryView] GitHub profile not found for user: {request.user.username}"
            logger.warning(error_message)
            return Response(
                {"error": "GitHub profile not found. Please connect your GitHub account."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            error_message = f"[CommitHistoryView] Error fetching commit history: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SyncGitHubDataView(APIView):
    """
    Sync GitHub data for the current user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logger.info(f"[SyncGitHubDataView] Received sync request from user: {request.user.username}")
        
        # Get GitHub username from request data
        github_username = request.data.get('github_username')
        
        # Initialize GitHub service
        logger.debug(f"[SyncGitHubDataView] Initializing GitHubService for sync")
        github_service = GitHubService()
        
        # Log user details
        if hasattr(request.user, 'email'):
            logger.debug(f"[SyncGitHubDataView] User email: {request.user.email}")
        
        # If github_username is not provided, try to find it automatically
        if not github_username:
            logger.info(f"[SyncGitHubDataView] No GitHub username provided. Attempting to find automatically.")
            
            # First check if user already has a GitHub profile
            try:
                # Import the model here to avoid scope issues
                from .models import GitHubProfile
                
                existing_profile = GitHubProfile.objects.get(user=request.user)
                github_username = existing_profile.github_username
                logger.info(f"[SyncGitHubDataView] Found existing GitHub profile for user: {github_username}")
                
                # If we found an existing profile, do a sync and return
                profile = github_service.sync_user_data(request.user, github_username)
                
                # Get additional repository stats after sync
                from .models import UserRepositoryStats
                repo_stats = UserRepositoryStats.objects.filter(profile=profile)
                repo_count = repo_stats.count()
                
                return Response({
                    "status": "success",
                    "message": "GitHub data synced successfully using existing profile",
                    "github_username": github_username,
                    "repositories_found": repo_count,
                    "last_synced": profile.last_synced,
                    "next": "/api/codetrack/stats/"
                })
                
            except GitHubProfile.DoesNotExist:
                # Profile doesn't exist, try to find by email in organization
                if hasattr(request.user, 'email') and request.user.email:
                    email = request.user.email
                    logger.info(f"[SyncGitHubDataView] Trying to find GitHub user by organization email lookup: {email}")
                    github_user = github_service.find_org_member_by_email(email)
                    
                    if github_user:
                        github_username = github_user.get('login')
                        logger.info(f"[SyncGitHubDataView] Found GitHub username by organization lookup: {github_username}")
                    else:
                        # Try matching by username as a fallback
                        logger.info(f"[SyncGitHubDataView] Trying username as GitHub username: {request.user.username}")
                        
                        # Check if username exists on GitHub
                        user_data = github_service.get_user_profile(request.user.username)
                        if user_data:
                            github_username = request.user.username
                            logger.info(f"[SyncGitHubDataView] Found matching GitHub user with username: {github_username}")
                        else:
                            # No automatic matches found
                            logger.warning(f"[SyncGitHubDataView] Could not automatically find GitHub username for user: {request.user.username}")
                            return Response({
                                "error": "Could not automatically find your GitHub username",
                                "user": request.user.username,
                                "email": request.user.email if hasattr(request.user, 'email') else None,
                                "suggestion": "Please provide your GitHub username explicitly",
                                "example": {"github_username": "your-github-username"}
                            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not github_username:
            logger.warning(f"[SyncGitHubDataView] Missing GitHub username in request from user: {request.user.username}")
            return Response(
                {
                    "error": "GitHub username is required",
                    "example": {"github_username": "your-github-username"}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if the GitHub account is already linked to another user
            try:
                from .models import GitHubProfile
                existing_profile = GitHubProfile.objects.filter(github_username=github_username).exclude(user=request.user).first()
                if existing_profile:
                    logger.warning(f"[SyncGitHubDataView] GitHub username {github_username} is already linked to user {existing_profile.user.username}")
                    return Response({
                        "error": f"GitHub username {github_username} is already linked to another user.",
                        "info": "If this is your GitHub account, please contact an administrator for assistance."
                    }, status=status.HTTP_409_CONFLICT)
            except Exception as e:
                logger.error(f"[SyncGitHubDataView] Error checking existing profiles: {str(e)}")
            
            # Verify the GitHub username exists before attempting to sync
            user_data = github_service.get_user_profile(github_username)
            if not user_data:
                logger.warning(f"[SyncGitHubDataView] GitHub username {github_username} not found or not accessible")
                return Response({
                    "error": f"GitHub username {github_username} not found or not accessible.",
                    "suggestions": [
                        "Check that the username is spelled correctly",
                        "Make sure the GitHub account is public or accessible with the current API key",
                        "If you're certain this is correct, contact an administrator"
                    ]
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Sync user data
            logger.debug(f"[SyncGitHubDataView] Starting sync for GitHub username: {github_username}")
            profile = github_service.sync_user_data(request.user, github_username)
            logger.info(f"[SyncGitHubDataView] Successfully synced data for GitHub username: {github_username}")
            
            # Also update the github_username field in the User model
            try:
                request.user.github_username = github_username
                request.user.save(update_fields=['github_username'])
                logger.info(f"[SyncGitHubDataView] Updated github_username in User model: {github_username}")
            except Exception as e:
                logger.error(f"[SyncGitHubDataView] Error updating github_username in User model: {str(e)}")
            
            # Get additional repository stats after sync
            from .models import UserRepositoryStats
            repo_stats = UserRepositoryStats.objects.filter(profile=profile)
            repo_count = repo_stats.count()
            
            # Create a more detailed response
            repos = []
            for repo_stat in repo_stats[:5]:  # Just include the first 5 repos to avoid very large responses
                repos.append({
                    "name": repo_stat.repository.name,
                    "commits": repo_stat.commits,
                    "lines_added": repo_stat.lines_added,
                    "lines_deleted": repo_stat.lines_deleted
                })
            
            return Response({
                "status": "success",
                "message": "GitHub data synced successfully",
                "github_username": github_username,
                "github_email": profile.github_email,
                "repositories_found": repo_count,
                "repositories_preview": repos,
                "has_more_repos": repo_count > len(repos),
                "last_synced": profile.last_synced,
                "next": "/api/codetrack/stats/"
            })
            
        except Exception as e:
            error_message = f"[SyncGitHubDataView] Error syncing GitHub data: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return Response(
                {
                    "error": f"An error occurred: {str(e)}",
                    "contact": "Please contact an administrator if this error persists."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Get sync status for the current user"""
        logger.info(f"[SyncGitHubDataView] Received sync status request from user: {request.user.username}")
        
        try:
            # Get user's GitHub profile
            from .models import GitHubProfile, UserRepositoryStats
            
            logger.debug(f"[SyncGitHubDataView] Fetching GitHub profile for user: {request.user.username}")
            profile = GitHubProfile.objects.get(user=request.user)
            
            sync_age_seconds = (timezone.now() - profile.last_synced).total_seconds()
            logger.debug(f"[SyncGitHubDataView] Sync age: {sync_age_seconds} seconds")
            
            # Get repository count
            repo_count = UserRepositoryStats.objects.filter(profile=profile).count()
            
            return Response({
                "status": "success",
                "github_username": profile.github_username,
                "github_email": profile.github_email,
                "repositories_count": repo_count,
                "last_synced": profile.last_synced,
                "sync_age_seconds": sync_age_seconds,
                "sync_age_hours": round(sync_age_seconds / 3600, 2),
                "needs_refresh": sync_age_seconds > 3600  # Suggest refresh if older than 1 hour
            })
            
        except GitHubProfile.DoesNotExist:
            error_message = f"[SyncGitHubDataView] GitHub account not connected for user: {request.user.username}"
            logger.warning(error_message)
            
            if hasattr(request.user, 'email'):
                logger.debug(f"[SyncGitHubDataView] User has email: {request.user.email}")
                
            return Response({
                "status": "not_connected", 
                "message": "GitHub account not connected",
                "user": request.user.username,
                "email": request.user.email if hasattr(request.user, 'email') else None,
                "solution": "Use POST to /api/codetrack/sync/ with {'github_username': 'your-github-username'} to connect your account"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            error_message = f"[SyncGitHubDataView] Error getting sync status: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_github_user(request):
    """
    Manually link a GitHub username to the current user.
    For admins only.
    """
    logger.info(f"[LinkGitHubUser] Received request from user: {request.user.username}")
    
    # Check if user is admin or staff
    if not request.user.is_staff and not request.user.is_superuser:
        logger.warning(f"[LinkGitHubUser] Non-admin user {request.user.username} tried to use link_github_user")
        return Response(
            {"error": "Only admin users can use this endpoint"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get parameters
    github_username = request.data.get('github_username')
    username = request.data.get('username')
    force = request.data.get('force', False)
    
    if not github_username or not username:
        logger.warning(f"[LinkGitHubUser] Missing required parameters")
        return Response(
            {"error": "Both github_username and username are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Import necessary models
        from .models import GitHubProfile, UserRepositoryStats
        
        # Get the target user
        target_user = User.objects.get(username=username)
        logger.info(f"[LinkGitHubUser] Found target user: {target_user.username}")
        
        # Check if user already has a GitHub profile
        existing_profile = None
        try:
            existing_profile = GitHubProfile.objects.get(user=target_user)
            logger.warning(f"[LinkGitHubUser] User already has GitHub profile: {existing_profile.github_username}")
            
            if not force:
                return Response({
                    "error": f"User already has GitHub profile: {existing_profile.github_username}",
                    "info": "Use force=true to overwrite"
                }, status=status.HTTP_409_CONFLICT)
        except GitHubProfile.DoesNotExist:
            logger.info(f"[LinkGitHubUser] No existing profile found for user")
        
        # Get GitHub service
        github_service = GitHubService()
        
        # Sync user data with the provided GitHub username
        profile = github_service.sync_user_data(target_user, github_username)
        logger.info(f"[LinkGitHubUser] Successfully linked {username} to GitHub username {github_username}")
        
        # Get repository count
        repo_count = UserRepositoryStats.objects.filter(profile=profile).count()
        
        return Response({
            "status": "success",
            "message": f"Successfully linked {username} to GitHub username {github_username}",
            "repository_count": repo_count,
            "github_email": profile.github_email,
            "last_synced": profile.last_synced
        })
        
    except User.DoesNotExist:
        logger.error(f"[LinkGitHubUser] Target user not found: {username}")
        return Response(
            {"error": f"User not found: {username}"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        error_message = f"[LinkGitHubUser] Error linking GitHub user: {str(e)}"
        logger.error(f"{error_message}\n{traceback.format_exc()}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
