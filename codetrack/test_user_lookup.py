#!/usr/bin/env python
"""
Test script to check if a user can be found by email in GitHubService.
"""
import os
import sys
import django
import argparse
import logging

# Set up Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Poly_Agent.settings')
django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model
from codetrack.models import GitHubProfile, Repository, UserRepositoryStats
from codetrack.services import GitHubService
from Poly_Agent.config import ORGANIZATION

User = get_user_model()

def setup_logging():
    """Set up logging for this script"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def test_user_lookup(username=None, email=None, github_username=None, check_org=False):
    """Test looking up a user by username or email"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting user lookup test")
    logger.info(f"Organization set in config: {ORGANIZATION}")
    
    # Initialize GitHub service
    github_service = GitHubService()
    
    # First test organization lookup if requested
    if check_org and email:
        logger.info(f"Testing direct organization lookup for email: {email}")
        org_member = github_service.find_org_member_by_email(email)
        if org_member:
            logger.info(f"Found in organization: {org_member['login']}")
            if 'email' in org_member:
                logger.info(f"Member email: {org_member['email']}")
            if 'name' in org_member:
                logger.info(f"Member name: {org_member['name']}")
        else:
            logger.warning(f"Email {email} not found in organization {ORGANIZATION}")
    
    # Find user
    user = None
    if username:
        try:
            user = User.objects.get(username=username)
            logger.info(f"Found user by username: {username}")
            if hasattr(user, 'email'):
                logger.info(f"User email: {user.email}")
        except User.DoesNotExist:
            logger.error(f"No user found with username: {username}")
            return
    elif email:
        try:
            user = User.objects.get(email=email)
            logger.info(f"Found user by email: {email}")
            logger.info(f"Username: {user.username}")
        except User.DoesNotExist:
            logger.error(f"No user found with email: {email}")
            return
    else:
        logger.error("Either username or email must be provided")
        return
    
    # Find GitHub profile for user
    try:
        profile = GitHubProfile.objects.get(user=user)
        logger.info(f"Found GitHub profile by user relation")
        logger.info(f"GitHub username: {profile.github_username}")
        logger.info(f"GitHub email: {profile.github_email}")
    except GitHubProfile.DoesNotExist:
        logger.warning(f"No GitHub profile found directly linked to user: {user.username}")
        
        # Try to find by email
        if hasattr(user, 'email') and user.email:
            try:
                email_profile = GitHubProfile.objects.filter(github_email=user.email).first()
                if email_profile:
                    logger.info(f"Found GitHub profile by email match: {user.email}")
                    logger.info(f"GitHub username: {email_profile.github_username}")
                    logger.info(f"Profile is linked to user: {email_profile.user.username}")
                else:
                    logger.warning(f"No GitHub profile found with email: {user.email}")
            except Exception as e:
                logger.error(f"Error finding profile by email: {str(e)}")
    
    # Test get_user_stats (this will now try to find user in organization)
    logger.info("Testing GitHubService.get_user_stats with organization lookup")
    stats = github_service.get_user_stats(user)
    if stats:
        logger.info(f"Found GitHub stats for user: {user.username}")
        logger.info(f"GitHub username: {stats['github_username']}")
        logger.info(f"Total commits: {stats['total_commits']}")
        logger.info(f"Repositories: {stats['repositories_count']}")
        
        # Show some repository details
        logger.info("Listing repositories:")
        profile = GitHubProfile.objects.get(github_username=stats['github_username'])
        repos = UserRepositoryStats.objects.filter(profile=profile)
        for idx, repo_stat in enumerate(repos, 1):
            logger.info(f"{idx}. {repo_stat.repository.name} - {repo_stat.commits} commits")
    else:
        logger.warning(f"No GitHub stats found for user: {user.username}")
    
    # Create/update GitHub profile if requested
    if github_username:
        logger.info(f"Syncing GitHub data for username: {github_username}")
        try:
            profile = github_service.sync_user_data(user, github_username)
            logger.info(f"Successfully synced GitHub data")
            logger.info(f"GitHub username: {profile.github_username}")
            logger.info(f"GitHub email: {profile.github_email}")
            logger.info(f"Last synced: {profile.last_synced}")
            
            # Show repository count
            repo_count = UserRepositoryStats.objects.filter(profile=profile).count()
            logger.info(f"Found {repo_count} repositories")
        except Exception as e:
            logger.error(f"Error syncing GitHub data: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test GitHub user lookup')
    parser.add_argument('--username', help='Django username to lookup')
    parser.add_argument('--email', help='Email to lookup')
    parser.add_argument('--github', help='GitHub username to sync (optional)')
    parser.add_argument('--check-org', action='store_true', help='Check organization for email')
    
    args = parser.parse_args()
    
    if not (args.username or args.email):
        print("Error: Either --username or --email must be provided")
        sys.exit(1)
    
    setup_logging()
    test_user_lookup(args.username, args.email, args.github, args.check_org) 