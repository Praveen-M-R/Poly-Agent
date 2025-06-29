#!/usr/bin/env python
"""
Quick tool to manually link a specific user to a GitHub account.
This is helpful when automatic linking fails or you need to correct a user's GitHub profile.

Example usage:
python fix_user.py --username praveen --github-username praveenr --force
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

def fix_user(username, github_username, force=False):
    """Link a user to a GitHub account"""
    logger = logging.getLogger(__name__)
    
    if not username or not github_username:
        logger.error("Both username and GitHub username are required")
        return False
    
    logger.info(f"Trying to link user {username} to GitHub account {github_username}")
    
    # Find the user
    try:
        user = User.objects.get(username=username)
        logger.info(f"Found user: {user.username}")
        if hasattr(user, 'email'):
            logger.info(f"User email: {user.email}")
    except User.DoesNotExist:
        logger.error(f"User not found: {username}")
        return False
    
    # Check if user already has a GitHub profile
    try:
        existing_profile = GitHubProfile.objects.get(user=user)
        logger.warning(f"User already has a GitHub profile: {existing_profile.github_username}")
        
        if not force:
            logger.error("Use --force to overwrite the existing profile")
            return False
        
        logger.info(f"Force flag set, proceeding to overwrite profile")
    except GitHubProfile.DoesNotExist:
        logger.info(f"No existing GitHub profile found for {username}")
    
    # Initialize GitHub service
    github_service = GitHubService()
    
    # Verify the GitHub username exists
    user_data = github_service.get_user_profile(github_username)
    if not user_data:
        logger.error(f"GitHub username {github_username} not found or not accessible")
        return False
    
    logger.info(f"GitHub user found: {github_username}")
    if user_data.get('email'):
        logger.info(f"GitHub email: {user_data['email']}")
    
    # Sync user data
    try:
        logger.info(f"Starting sync for GitHub username: {github_username}")
        profile = github_service.sync_user_data(user, github_username)
        logger.info(f"Successfully linked user {username} to GitHub username {github_username}")
        
        # Get repository stats
        repo_stats = UserRepositoryStats.objects.filter(profile=profile)
        logger.info(f"Found {repo_stats.count()} repositories")
        
        # Show some repository details
        for idx, repo_stat in enumerate(repo_stats[:5], 1):
            logger.info(f"{idx}. {repo_stat.repository.name}: {repo_stat.commits} commits")
        
        return True
    except Exception as e:
        logger.error(f"Error syncing GitHub data: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Link a user to a GitHub account')
    parser.add_argument('--username', required=True, help='Django username')
    parser.add_argument('--github-username', required=True, help='GitHub username')
    parser.add_argument('--force', action='store_true', help='Force overwrite of existing profile')
    
    args = parser.parse_args()
    
    setup_logging()
    success = fix_user(args.username, args.github_username, args.force)
    
    sys.exit(0 if success else 1) 