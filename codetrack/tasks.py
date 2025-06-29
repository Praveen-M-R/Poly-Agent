from celery import shared_task
from django.contrib.auth.models import User
from .models import GitHubProfile
from .services import GitHubService
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger('codetrack')

@shared_task
def sync_github_data_for_user(user_id):
    """
    Sync GitHub data for a specific user
    """
    logger.info(f"Starting GitHub data sync for user {user_id}")
    
    try:
        # Get user
        user = User.objects.get(id=user_id)
        
        # Get GitHub profile
        try:
            profile = GitHubProfile.objects.get(user=user)
        except GitHubProfile.DoesNotExist:
            logger.warning(f"GitHub profile not found for user {user.username}")
            return False
        
        # Sync data
        github_service = GitHubService()
        github_service.sync_user_data(user, profile.github_username)
        
        logger.info(f"GitHub data sync completed for user {user.username}")
        return True
    
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False
    except Exception as e:
        logger.exception(f"Error syncing GitHub data for user {user_id}: {str(e)}")
        return False

@shared_task
def sync_github_data_for_all_users():
    """
    Sync GitHub data for all users
    """
    logger.info("Starting GitHub data sync for all users")
    
    # Get all GitHub profiles
    profiles = GitHubProfile.objects.all()
    
    sync_count = 0
    error_count = 0
    
    # Sync data for each profile
    for profile in profiles:
        try:
            github_service = GitHubService()
            github_service.sync_user_data(profile.user, profile.github_username)
            sync_count += 1
        except Exception as e:
            logger.exception(f"Error syncing GitHub data for user {profile.user.username}: {str(e)}")
            error_count += 1
    
    logger.info(f"GitHub data sync completed for {sync_count} users, with {error_count} errors")
    return {"sync_count": sync_count, "error_count": error_count}

@shared_task
def sync_all_github_profiles():
    """
    Background task to sync all GitHub profiles
    """
    logger.info("[Task] Starting scheduled sync of all GitHub profiles")
    
    # Get profiles that haven't been synced in the last day
    one_day_ago = timezone.now() - timedelta(days=1)
    profiles_to_sync = GitHubProfile.objects.filter(last_synced__lt=one_day_ago)
    
    # Log how many profiles we're syncing
    total_profiles = profiles_to_sync.count()
    logger.info(f"[Task] Found {total_profiles} profiles to sync")
    
    # Initialize GitHub service
    github_service = GitHubService()
    
    # Keep track of success/failure
    successful_syncs = 0
    failed_syncs = 0
    
    # Sync each profile
    for profile in profiles_to_sync:
        try:
            logger.info(f"[Task] Syncing profile for user: {profile.user.username}")
            github_service.sync_user_repositories(profile)
            successful_syncs += 1
        except Exception as e:
            logger.error(f"[Task] Error syncing profile for user {profile.user.username}: {str(e)}")
            failed_syncs += 1
    
    logger.info(f"[Task] GitHub profile sync completed. Success: {successful_syncs}, Failed: {failed_syncs}")
    return {
        "total_profiles": total_profiles,
        "successful_syncs": successful_syncs,
        "failed_syncs": failed_syncs
    }

@shared_task
def check_removed_repository_access():
    """
    Background task to check if users still have access to repositories
    """
    logger.info("[Task] Starting check for removed repository access")
    
    # Get all GitHub profiles
    profiles = GitHubProfile.objects.all()
    total_profiles = profiles.count()
    
    # Initialize GitHub service
    github_service = GitHubService()
    
    # Keep track of success/failure
    successful_checks = 0
    failed_checks = 0
    removed_access_count = 0
    
    # Check each profile
    for profile in profiles:
        try:
            logger.info(f"[Task] Checking repository access for user: {profile.user.username}")
            
            # Get current repositories
            current_repositories = github_service.get_user_org_repositories(profile.github_username)
            
            # Extract repository IDs
            if current_repositories:
                # We need to get the DB IDs, not just the GitHub IDs
                repo_full_names = [repo.get('nameWithOwner') for repo in current_repositories]
                from .models import Repository
                repo_ids = list(Repository.objects.filter(full_name__in=repo_full_names).values_list('id', flat=True))
            else:
                repo_ids = []
            
            # Clean up repository access
            from .models import UserRepositoryStats
            before_count = UserRepositoryStats.objects.filter(profile=profile).count()
            github_service.clean_up_removed_repositories(profile, repo_ids)
            after_count = UserRepositoryStats.objects.filter(profile=profile).count()
            
            # Calculate how many were removed
            removed = before_count - after_count
            removed_access_count += removed
            
            if removed > 0:
                logger.info(f"[Task] Removed {removed} repository access records for user: {profile.user.username}")
            
            successful_checks += 1
        except Exception as e:
            logger.error(f"[Task] Error checking repository access for user {profile.user.username}: {str(e)}")
            failed_checks += 1
    
    logger.info(f"[Task] Repository access check completed. Success: {successful_checks}, Failed: {failed_checks}, Total removed: {removed_access_count}")
    return {
        "total_profiles": total_profiles,
        "successful_checks": successful_checks,
        "failed_checks": failed_checks,
        "removed_access_count": removed_access_count
    } 