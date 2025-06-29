#!/usr/bin/env python
"""
Script to find and fix GitHubProfile issues:
1. Find profiles with missing github_email
2. Find users with matching emails but no GitHub profile
3. Link existing profiles to users with matching emails
4. Look up organization members to create profiles for users without them
"""
import os
import sys
import django
import argparse
import logging
from datetime import datetime
import traceback

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

def setup_logging(log_file=None):
    """Set up logging for this script"""
    handlers = [
        logging.StreamHandler()  # Console handler
    ]
    
    if log_file:
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )

def fix_missing_github_emails(github_service, dry_run=True):
    """Find and fix GitHub profiles with missing emails"""
    logger = logging.getLogger(__name__)
    
    logger.info("Checking for profiles with missing GitHub emails")
    profiles = GitHubProfile.objects.filter(github_email__isnull=True) | GitHubProfile.objects.filter(github_email="")
    
    if not profiles.exists():
        logger.info("No profiles with missing GitHub emails found")
        return
        
    logger.info(f"Found {profiles.count()} profiles with missing GitHub emails")
    
    for profile in profiles:
        logger.info(f"Profile {profile.id}: User={profile.user.username}, GitHub={profile.github_username}")
        
        # Try to get GitHub email from API
        try:
            user_data = github_service.get_user_profile(profile.github_username)
            if user_data and 'email' in user_data and user_data['email']:
                github_email = user_data['email']
                logger.info(f"Found GitHub email for {profile.github_username}: {github_email}")
                
                if not dry_run:
                    profile.github_email = github_email
                    profile.save()
                    logger.info(f"Updated profile with GitHub email")
                else:
                    logger.info(f"Would update profile with GitHub email: {github_email} (dry run)")
            else:
                logger.warning(f"Could not find GitHub email for {profile.github_username}")
        except Exception as e:
            logger.error(f"Error getting GitHub email for {profile.github_username}: {str(e)}")

def find_users_without_profiles(github_service, dry_run=True):
    """Find users without GitHub profiles but with emails that might match"""
    logger = logging.getLogger(__name__)
    
    logger.info("Looking for users without GitHub profiles")
    
    # Get all users with email addresses
    users_with_email = User.objects.exclude(email="").exclude(email__isnull=True)
    logger.info(f"Found {users_with_email.count()} users with email addresses")
    
    # Get all users who already have GitHub profiles
    users_with_profiles = User.objects.filter(github_profile__isnull=False)
    logger.info(f"Found {users_with_profiles.count()} users who already have GitHub profiles")
    
    # Find users who have emails but no GitHub profiles
    users_without_profiles = users_with_email.exclude(id__in=users_with_profiles.values_list('id', flat=True))
    logger.info(f"Found {users_without_profiles.count()} users with emails but no GitHub profiles")
    
    # Check if any of these users have emails that match existing profiles
    for user in users_without_profiles:
        logger.info(f"Checking user {user.username} with email {user.email}")
        
        try:
            # First check if there's a matching profile by email
            matching_profile = GitHubProfile.objects.filter(github_email=user.email).first()
            
            if matching_profile:
                logger.info(f"Found matching profile by email: {matching_profile.github_username}")
                if matching_profile.user != user:
                    logger.warning(f"Profile is linked to different user: {matching_profile.user.username}")
                    
                    if not dry_run:
                        # Create a new profile for this user with the same GitHub username
                        logger.info(f"Creating new profile for {user.username} with GitHub username {matching_profile.github_username}")
                        new_profile = GitHubProfile.objects.create(
                            user=user,
                            github_username=matching_profile.github_username,
                            github_email=user.email,
                            avatar_url=matching_profile.avatar_url
                        )
                        logger.info(f"Created new profile {new_profile.id}")
                    else:
                        logger.info(f"Would create new profile for {user.username} (dry run)")
            else:
                # Try to find by organization member lookup
                logger.info(f"Checking organization for email: {user.email}")
                org_member = github_service.find_org_member_by_email(user.email)
                
                if org_member:
                    github_username = org_member.get('login')
                    logger.info(f"Found organization member: {github_username}")
                    
                    if not dry_run:
                        # Create profile for this user
                        new_profile = GitHubProfile.objects.create(
                            user=user,
                            github_username=github_username,
                            github_email=user.email,
                            avatar_url=org_member.get('avatarUrl', '')
                        )
                        logger.info(f"Created new profile for {user.username} with GitHub username {github_username}")
                        
                        # Sync the repositories
                        github_service.sync_user_repositories(new_profile)
                        logger.info(f"Synced repositories for new profile")
                    else:
                        logger.info(f"Would create profile for {user.username} with GitHub username {github_username} (dry run)")
                else:
                    logger.warning(f"No matching GitHub account found for email: {user.email}")
        except Exception as e:
            logger.error(f"Error processing user {user.username}: {str(e)}\n{traceback.format_exc()}")

def sync_all_profiles(github_service, dry_run=True):
    """Sync all GitHub profiles to ensure data is up-to-date"""
    logger = logging.getLogger(__name__)
    
    logger.info("Syncing all GitHub profiles")
    profiles = GitHubProfile.objects.all()
    logger.info(f"Found {profiles.count()} profiles to sync")
    
    for profile in profiles:
        logger.info(f"Syncing profile for {profile.user.username} (GitHub: {profile.github_username})")
        
        if not dry_run:
            try:
                # Sync repositories
                github_service.sync_user_repositories(profile)
                profile.last_synced = datetime.now()
                profile.save()
                
                # Get repo count after sync
                repo_count = UserRepositoryStats.objects.filter(profile=profile).count()
                logger.info(f"Synced profile. Found {repo_count} repositories.")
            except Exception as e:
                logger.error(f"Error syncing profile {profile.id}: {str(e)}")
        else:
            logger.info(f"Would sync profile for {profile.user.username} (dry run)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix GitHub profile issues')
    parser.add_argument('--missing-emails', action='store_true', help='Fix profiles with missing GitHub emails')
    parser.add_argument('--find-users', action='store_true', help='Find users without profiles')
    parser.add_argument('--sync-all', action='store_true', help='Sync all existing profiles')
    parser.add_argument('--run', action='store_true', help='Actually make changes (otherwise dry run)')
    parser.add_argument('--log-file', default=None, help='Log file path')
    
    args = parser.parse_args()
    
    # If no specific action selected, do all
    if not (args.missing_emails or args.find_users or args.sync_all):
        args.missing_emails = True
        args.find_users = True
        args.sync_all = True
    
    # Set up logging
    log_file = args.log_file or os.path.join(os.path.dirname(__file__), '..', 'logs', f'profile_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    setup_logging(log_file)
    logger = logging.getLogger(__name__)
    
    # Print info about the run
    logger.info(f"Starting profile fix script")
    logger.info(f"Organization: {ORGANIZATION}")
    logger.info(f"Dry run: {not args.run}")
    
    # Initialize GitHub service
    github_service = GitHubService()
    
    # Run selected actions
    if args.missing_emails:
        fix_missing_github_emails(github_service, dry_run=not args.run)
    
    if args.find_users:
        find_users_without_profiles(github_service, dry_run=not args.run)
    
    if args.sync_all:
        sync_all_profiles(github_service, dry_run=not args.run)
    
    logger.info("Profile fix script completed") 