from celery import shared_task
import logging
from django.utils import timezone
from .models import Member, Repository, ProjectContribution, RepositoryCollaborator, SyncStatus
from .services import fetch_organization_members, fetch_organization_repositories, fetch_repository_contributors, fetch_commit_history_for_user

logger = logging.getLogger(__name__)

@shared_task
def sync_members():
    """Sync members from GitHub API to database."""
    logger.info("Starting sync of organization members")
    try:
        # Fetch members from GitHub API
        github_members = fetch_organization_members()
        
        # Get current usernames in GitHub
        current_usernames = {m["login"] for m in github_members}
        
        # Delete members that no longer exist in GitHub
        deleted_count = Member.objects.exclude(username__in=current_usernames).delete()[0]
        
        # Update or create members
        created_count = 0
        updated_count = 0
        
        for member_data in github_members:
            obj, created = Member.objects.update_or_create(
                username=member_data["login"],
                defaults={
                    "name": member_data.get("name") or member_data["login"],
                    "email": member_data.get("email", ""),
                    "avatar_url": member_data.get("avatarUrl", ""),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Update sync status
        status, _ = SyncStatus.objects.get_or_create(pk=1)
        status.last_members_sync = timezone.now()
        status.save()
        
        logger.info(f"Members sync completed - Created: {created_count}, Updated: {updated_count}, Deleted: {deleted_count}")
        return {
            "created": created_count,
            "updated": updated_count,
            "deleted": deleted_count,
            "total": created_count + updated_count
        }
    
    except Exception as e:
        logger.exception("Error syncing members")
        raise e

@shared_task
def sync_repositories():
    """Sync repositories from GitHub API to database."""
    logger.info("Starting sync of organization repositories")
    try:
        # Fetch repositories from GitHub API
        github_repositories = fetch_organization_repositories()
        
        # Get current repository names in GitHub
        current_names = {r["name"] for r in github_repositories}
        
        # Delete repositories that no longer exist in GitHub
        deleted_count = Repository.objects.exclude(name__in=current_names).delete()[0]
        
        # Update or create repositories
        created_count = 0
        updated_count = 0
        
        for repo_data in github_repositories:
            obj, created = Repository.objects.update_or_create(
                name=repo_data["name"],
                defaults={
                    "url": repo_data.get("url", ""),
                    "description": repo_data.get("description", ""),
                    "is_private": repo_data.get("isPrivate", False),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Update sync status
        status, _ = SyncStatus.objects.get_or_create(pk=1)
        status.last_repositories_sync = timezone.now()
        status.save()
        
        logger.info(f"Repositories sync completed - Created: {created_count}, Updated: {updated_count}, Deleted: {deleted_count}")
        return {
            "created": created_count,
            "updated": updated_count,
            "deleted": deleted_count,
            "total": created_count + updated_count
        }
    
    except Exception as e:
        logger.exception("Error syncing repositories")
        raise e

@shared_task
def sync_repository_data(repository_name=None):
    """Sync contributors and collaborators for a specific repository or all repositories."""
    if repository_name:
        repositories = Repository.objects.filter(name=repository_name)
        logger.info(f"Starting sync of repository data for {repository_name}")
    else:
        repositories = Repository.objects.all()
        logger.info(f"Starting sync of repository data for all repositories")
    
    contributors_total = 0
    collaborators_total = 0
    
    for repository in repositories:
        try:
            # Fetch contributors and collaborators from GitHub API
            repo_data = fetch_repository_contributors(repository.name)
            
            # Process contributors
            contributors = repo_data.get("contributors", [])
            current_contributor_usernames = set()
            
            for contributor_data in contributors:
                username = contributor_data.get("login")
                if not username:
                    continue
                
                current_contributor_usernames.add(username)
                
                # Get or create member
                member, _ = Member.objects.get_or_create(
                    username=username,
                    defaults={"name": username}
                )
                
                # Get commit history stats
                commit_stats = fetch_commit_history_for_user(repository.name, username)
                
                # Update or create contribution
                ProjectContribution.objects.update_or_create(
                    member=member,
                    repository=repository,
                    defaults={
                        "contributions": contributor_data.get("contributions", 0),
                        "lines_added": commit_stats.get("lines_added", 0),
                        "lines_deleted": commit_stats.get("lines_deleted", 0),
                        "net_lines": commit_stats.get("net_lines", 0),
                    }
                )
                
                contributors_total += 1
            
            # Process collaborators
            collaborators = repo_data.get("collaborators", [])
            current_collaborator_usernames = set()
            
            for collaborator_data in collaborators:
                username = collaborator_data.get("login")
                if not username:
                    continue
                
                current_collaborator_usernames.add(username)
                
                # Get or create member
                member, _ = Member.objects.get_or_create(
                    username=username,
                    defaults={
                        "name": collaborator_data.get("name", username),
                        "email": collaborator_data.get("email", ""),
                        "avatar_url": collaborator_data.get("avatarUrl", ""),
                    }
                )
                
                # Update or create collaborator
                RepositoryCollaborator.objects.update_or_create(
                    member=member,
                    repository=repository,
                    defaults={"role": None}  # We don't have role information yet
                )
                
                collaborators_total += 1
            
            # Clean up old contributors and collaborators for this repository
            # that are no longer present in GitHub
            ProjectContribution.objects.filter(
                repository=repository
            ).exclude(
                member__username__in=current_contributor_usernames
            ).delete()
            
            RepositoryCollaborator.objects.filter(
                repository=repository
            ).exclude(
                member__username__in=current_collaborator_usernames
            ).delete()
            
            logger.info(f"Repository {repository.name} sync completed - "
                       f"Contributors: {len(current_contributor_usernames)}, "
                       f"Collaborators: {len(current_collaborator_usernames)}")
        
        except Exception as e:
            logger.exception(f"Error syncing repository {repository.name}")
            # Continue with other repositories even if one fails
    
    # Update sync status
    status, _ = SyncStatus.objects.get_or_create(pk=1)
    status.last_contributions_sync = timezone.now()
    status.save()
    
    logger.info(f"All repository data sync completed - "
               f"Contributors total: {contributors_total}, "
               f"Collaborators total: {collaborators_total}")
    
    return {
        "contributors_total": contributors_total,
        "collaborators_total": collaborators_total,
    }

@shared_task
def sync_all_github_data():
    """Sync all GitHub data (members, repositories, and repository data)."""
    logger.info("Starting sync of all GitHub data")
    
    # Run each sync task in sequence
    members_result = sync_members()
    repositories_result = sync_repositories()
    repository_data_result = sync_repository_data()
    
    return {
        "members": members_result,
        "repositories": repositories_result,
        "repository_data": repository_data_result,
    } 