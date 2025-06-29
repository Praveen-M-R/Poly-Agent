import requests
import logging
import traceback
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from django.contrib.auth import get_user_model
from .models import GitHubProfile, Repository, UserRepositoryStats, CommitHistory
import json
from Poly_Agent.config import GIT_ACCESS_KEY, ORGANIZATION

User = get_user_model()

# Set up logger for the codetrack app
logger = logging.getLogger('codetrack')

class GitHubService:
    """
    Service for interacting with GitHub API using GraphQL
    """
    GITHUB_API_URL = "https://api.github.com/graphql"
    GITHUB_REST_API_URL = "https://api.github.com"
    
    def __init__(self, access_token=None):
        self.access_token = access_token or GIT_ACCESS_KEY or getattr(settings, 'GITHUB_ACCESS_TOKEN', None)
        if not self.access_token:
            logger.error("[GitHubService] GitHub access token not provided. API calls will fail.")
        else:
            logger.debug("[GitHubService] Initialized with access token")
    
    def get_user_profile(self, username):
        """
        Get GitHub user profile information using GraphQL
        """
        logger.info(f"[GitHubService] Fetching GitHub profile for username: {username}")
        
        headers = self._get_headers()
        query = """
        query($username: String!) {
          user(login: $username) {
            login
            name
            email
            avatarUrl
            url
          }
        }
        """
        variables = {"username": username}
        
        try:
            logger.debug(f"[GitHubService] Sending GraphQL request for user profile: {username}")
            response = requests.post(
                self.GITHUB_API_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = f"[GitHubService] GraphQL errors fetching profile for {username}: {data['errors']}"
                logger.error(error_message)
                return None
            
            logger.debug(f"[GitHubService] Successfully fetched GitHub profile for {username}")    
            return data["data"]["user"]
        except requests.exceptions.RequestException as e:
            error_message = f"[GitHubService] Error fetching GitHub profile for {username}: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return None
    
    def get_user_repositories(self, username):
        """
        Get repositories for a user using GraphQL
        """
        logger.info(f"[GitHubService] Fetching repositories for username: {username}")
        
        headers = self._get_headers()
        query = """
        query($username: String!, $first: Int!) {
          user(login: $username) {
            repositories(first: $first, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                name
                owner {
                  login
                }
                nameWithOwner
                url
                description
                isPrivate
                createdAt
              }
            }
          }
        }
        """
        variables = {"username": username, "first": 100}
        
        try:
            logger.debug(f"[GitHubService] Sending GraphQL request for repositories: {username}")
            response = requests.post(
                self.GITHUB_API_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = f"[GitHubService] GraphQL errors fetching repositories for {username}: {data['errors']}"
                logger.error(error_message)
                return []
            
            repos = data["data"]["user"]["repositories"]["nodes"]
            logger.debug(f"[GitHubService] Successfully fetched {len(repos)} repositories for {username}")
            return repos
        except requests.exceptions.RequestException as e:
            error_message = f"[GitHubService] Error fetching repositories for {username}: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return []
    
    def get_organization_repositories(self):
        """
        Get all repositories for the organization specified in config
        """
        logger.info(f"[GitHubService] Fetching repositories for organization: {ORGANIZATION}")
        
        if not ORGANIZATION:
            logger.warning("[GitHubService] No organization specified in config.")
            return []
            
        try:
            # Use GraphQL API to fetch organization repositories
            headers = self._get_headers()
            query = """
            query($org: String!) {
              organization(login: $org) {
                repositories(first: 100, isFork: false) {
                  nodes {
                    name
                    url
                    description
                    isPrivate
                    owner {
                      login
                    }
                  }
                }
              }
            }
            """
            variables = {"org": ORGANIZATION}
            response = requests.post(
                self.GITHUB_API_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = f"[GitHubService] GraphQL errors fetching organization repositories: {data['errors']}"
                logger.error(error_message)
                return []
            
            # Extract repositories from response
            org_repos = data["data"]["organization"]["repositories"]["nodes"]
            logger.info(f"[GitHubService] Successfully fetched {len(org_repos)} repositories for organization: {ORGANIZATION}")
            
            # Format the data to match our expected format
            formatted_repos = []
            for repo in org_repos:
                formatted_repos.append({
                    "name": repo.get("name"),
                    "owner": {
                        "login": repo.get("owner", {}).get("login", ORGANIZATION)
                    },
                    "nameWithOwner": f"{ORGANIZATION}/{repo.get('name')}",
                    "url": repo.get("url"),
                    "description": repo.get("description"),
                    "isPrivate": repo.get("isPrivate", False)
                })
            
            return formatted_repos
        except Exception as e:
            error_message = f"[GitHubService] Error fetching organization repositories: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return []
    
    def get_repository_contributors(self, repo_name):
        """
        Get contributors and collaborators for a repository
        """
        if not ORGANIZATION:
            logger.warning("[GitHubService] No organization specified in config.")
            return {"collaborators": [], "contributors": []}
        
        logger.info(f"[GitHubService] Fetching contributors for repository: {repo_name}")
        
        try:
            # Fetch collaborators via GraphQL
            headers = self._get_headers()
            query = """
            query($org: String!, $repo: String!) {
              repository(owner: $org, name: $repo) {
                collaborators(first: 100) {
                  nodes {
                    login
                    name
                    email
                    avatarUrl
                  }
                }
              }
            }
            """
            variables = {"org": ORGANIZATION, "repo": repo_name}
            response = requests.post(
                self.GITHUB_API_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = f"[GitHubService] GraphQL errors fetching collaborators: {data['errors']}"
                logger.error(error_message)
                return {"collaborators": [], "contributors": []}
            
            collaborators = data["data"]["repository"]["collaborators"]["nodes"]
            logger.debug(f"[GitHubService] Found {len(collaborators)} collaborators for repository {repo_name}")
            
            # Fetch contributors via REST API
            rest_headers = self._get_rest_headers()
            rest_url = f"{self.GITHUB_REST_API_URL}/repos/{ORGANIZATION}/{repo_name}/contributors"
            rest_response = requests.get(rest_url, headers=rest_headers)
            rest_response.raise_for_status()
            
            contributors_raw = rest_response.json()
            logger.debug(f"[GitHubService] Found {len(contributors_raw)} contributors for repository {repo_name}")
            
            # Format contributors
            contributors = []
            for contributor in contributors_raw:
                contributors.append({
                    "login": contributor.get("login"),
                    "contributions": contributor.get("contributions", 0),
                    "avatarUrl": contributor.get("avatar_url"),
                    "url": contributor.get("html_url")
                })
            
            return {
                "collaborators": collaborators,
                "contributors": contributors
            }
        except Exception as e:
            error_message = f"[GitHubService] Error fetching repository contributors: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return {"collaborators": [], "contributors": []}
    
    def fetch_commit_history_for_user(self, repository_name, username):
        """
        Fetch commit history for a given user in a repository and calculate total lines added.
        """
        logger.info(f"[GitHubService] Fetching commit history for {username} in {repository_name}")
        
        if not ORGANIZATION:
            logger.warning("[GitHubService] No organization specified in config.")
            return None
        
        try:
            rest_headers = self._get_rest_headers()
            commits_url = f"{self.GITHUB_REST_API_URL}/repos/{ORGANIZATION}/{repository_name}/commits"
            params = {'author': username, 'per_page': 100}
            total_lines_added = 0
            total_lines_deleted = 0
            page = 1
            
            while True:
                paged_url = f"{commits_url}?author={username}&per_page=100&page={page}"
                response = requests.get(paged_url, headers=rest_headers)
                response.raise_for_status()
                
                commits = response.json()
                if not commits:
                    break
                
                for commit in commits:
                    sha = commit.get("sha")
                    if not sha:
                        continue
                    
                    commit_detail_url = f"{self.GITHUB_REST_API_URL}/repos/{ORGANIZATION}/{repository_name}/commits/{sha}"
                    detail_response = requests.get(commit_detail_url, headers=rest_headers)
                    detail_response.raise_for_status()
                    
                    commit_data = detail_response.json()
                    stats = commit_data.get("stats", {})
                    additions = stats.get("additions", 0)
                    deletions = stats.get("deletions", 0)
                    total_lines_added += additions
                    total_lines_deleted += deletions
                
                # Check if there are more pages
                if 'Link' in response.headers and 'rel="next"' in response.headers['Link']:
                    page += 1
                else:
                    break
            
            return {
                "lines_added": total_lines_added,
                "lines_deleted": total_lines_deleted,
                "net_lines": total_lines_added - total_lines_deleted
            }
        except Exception as e:
            error_message = f"[GitHubService] Error fetching commit history: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return None
    
    def get_user_org_repositories(self, username):
        """
        Get repositories for a user that belong to the specified organization,
        including private repositories
        """
        logger.info(f"[GitHubService] Fetching organization repositories for username: {username}")
        
        if not ORGANIZATION:
            logger.warning("[GitHubService] No organization specified in config. Falling back to all repositories.")
            return self.get_user_repositories(username)
        
        try:
            # First get all organization repositories
            org_repos = self.get_organization_repositories()
            
            if not org_repos:
                logger.warning(f"[GitHubService] No repositories found for organization: {ORGANIZATION}")
                return []
                
            # Now for each repository, check if the user is a contributor
            user_org_repos = []
            
            for repo in org_repos:
                repo_name = repo.get("name")
                if not repo_name:
                    continue
                
                try:
                    # Get contributors data from our own method
                    contributors_data = self.get_repository_contributors(repo_name)
                    
                    # Check if this user is a contributor or collaborator
                    is_contributor = False
                    
                    # Check collaborators
                    collaborators = contributors_data.get("collaborators", [])
                    for collaborator in collaborators:
                        if collaborator.get("login") == username:
                            is_contributor = True
                            break
                    
                    # If not a collaborator, check contributors
                    if not is_contributor:
                        contributors = contributors_data.get("contributors", [])
                        for contributor in contributors:
                            if contributor.get("login") == username:
                                is_contributor = True
                                break
                    
                    if is_contributor:
                        user_org_repos.append(repo)
                        
                except Exception as repo_e:
                    logger.error(f"[GitHubService] Error checking contributors for repo {repo_name}: {str(repo_e)}")
                    continue
            
            logger.info(f"[GitHubService] Found {len(user_org_repos)} organization repositories where {username} is a contributor")
            return user_org_repos
                
        except Exception as e:
            error_message = f"[GitHubService] Error fetching user's organization repositories: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            # Fall back to standard repository fetching
            logger.info(f"[GitHubService] Falling back to standard repository fetching")
            return self.get_user_repositories(username)
    
    def get_repository_commits(self, owner, repo, username=None):
        """
        Get commits for a repository using GraphQL, optionally filtered by username
        """
        logger.info(f"[GitHubService] Fetching commits for repository: {owner}/{repo}" + (f" filtered by {username}" if username else ""))
        
        headers = self._get_headers()
        query = """
        query($owner: String!, $name: String!, $first: Int!) {
          repository(owner: $owner, name: $name) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: $first, author: {emails: [$username]}) {
                    nodes {
                      oid
                      messageHeadline
                      committedDate
                      additions
                      deletions
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "owner": owner, 
            "name": repo, 
            "first": 100,
            "username": username if username else ""
        }
        
        try:
            logger.debug(f"[GitHubService] Sending GraphQL request for commits: {owner}/{repo}")
            response = requests.post(
                self.GITHUB_API_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = f"[GitHubService] GraphQL errors fetching commits for {owner}/{repo}: {data['errors']}"
                logger.error(error_message)
                logger.info(f"[GitHubService] Falling back to REST API for commits")
                return self._get_repository_commits_rest(owner, repo, username)
            
            if not data["data"]["repository"]["defaultBranchRef"]:
                logger.warning(f"[GitHubService] No default branch found for {owner}/{repo}")
                return []
            
            commits = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["nodes"]
            logger.debug(f"[GitHubService] Successfully fetched {len(commits)} commits for {owner}/{repo}")
            return commits
        except (requests.exceptions.RequestException, KeyError) as e:
            error_message = f"[GitHubService] Error fetching commits for {owner}/{repo}: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            logger.info(f"[GitHubService] Falling back to REST API for commits")
            return self._get_repository_commits_rest(owner, repo, username)
    
    def _get_repository_commits_rest(self, owner, repo, username=None):
        """Fallback to REST API for commits"""
        logger.info(f"[GitHubService] Using REST API to fetch commits for: {owner}/{repo}")
        
        headers = self._get_rest_headers()
        url = f"{self.GITHUB_REST_API_URL}/repos/{owner}/{repo}/commits"
        
        # Filter by username if provided
        params = {'author': username} if username else {}
        
        try:
            logger.debug(f"[GitHubService] Sending REST request to: {url}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            commits = response.json()
            logger.debug(f"[GitHubService] Fetched {len(commits)} commits from REST API")
            
            # Process commits to match GraphQL format
            processed_commits = []
            logger.debug(f"[GitHubService] Processing commit details")
            for commit in commits:
                # Get detailed commit info to get additions/deletions
                try:
                    detail_url = f"{self.GITHUB_REST_API_URL}/repos/{owner}/{repo}/commits/{commit['sha']}"
                    logger.debug(f"[GitHubService] Fetching commit detail for: {commit['sha']}")
                    detail_response = requests.get(detail_url, headers=headers)
                    detail_response.raise_for_status()
                    detail = detail_response.json()
                    
                    processed_commits.append({
                        "oid": commit["sha"],
                        "messageHeadline": commit["commit"]["message"].split("\n")[0],
                        "committedDate": commit["commit"]["committer"]["date"],
                        "additions": detail["stats"]["additions"],
                        "deletions": detail["stats"]["deletions"]
                    })
                except Exception as detail_e:
                    error_message = f"[GitHubService] Error fetching commit details for {commit['sha']}: {str(detail_e)}"
                    logger.error(f"{error_message}\n{traceback.format_exc()}")
            
            logger.info(f"[GitHubService] Successfully processed {len(processed_commits)} commits via REST API")
            return processed_commits
        except requests.exceptions.RequestException as e:
            error_message = f"[GitHubService] Error fetching commits via REST for {owner}/{repo}: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            return []
    
    def sync_user_data(self, user_obj, github_username):
        """
        Sync user data from GitHub, including profile, repositories, and commits
        """
        logger.info(f"[GitHubService] Starting sync for user: {user_obj.username}, GitHub username: {github_username}")
        
        try:
            # Get or create GitHub profile
            profile, created = GitHubProfile.objects.get_or_create(user=user_obj)
            
            # Update profile information
            logger.debug(f"[GitHubService] Updating GitHub profile for: {github_username}")
            profile.github_username = github_username
            profile.last_synced = timezone.now()
            
            # Get additional profile information
            user_data = self.get_user_profile(github_username)
            if user_data:
                logger.debug(f"[GitHubService] Updating profile details from GitHub API")
                profile.github_email = user_data.get('email', '')
                profile.avatar_url = user_data.get('avatarUrl', '')
                profile.save()
                
                # Also update the User model's github_username field
                try:
                    user_obj.github_username = github_username
                    user_obj.save(update_fields=['github_username'])
                    logger.debug(f"[GitHubService] Updated User model github_username: {github_username}")
                except Exception as e:
                    logger.error(f"[GitHubService] Error updating User model github_username: {str(e)}")
            else:
                logger.warning(f"[GitHubService] No profile data found for GitHub username: {github_username}")
                profile.save()
                
                # Still update the User model's github_username field
                try:
                    user_obj.github_username = github_username
                    user_obj.save(update_fields=['github_username'])
                    logger.debug(f"[GitHubService] Updated User model github_username: {github_username}")
                except Exception as e:
                    logger.error(f"[GitHubService] Error updating User model github_username: {str(e)}")
            
            # Sync repositories
            logger.debug(f"[GitHubService] Syncing repositories for: {github_username}")
            self.sync_user_repositories(profile)
            
            logger.info(f"[GitHubService] Sync completed for user: {user_obj.username}")
            return profile
        except Exception as e:
            error_message = f"[GitHubService] Error syncing user data: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            raise
    
    def sync_user_repositories(self, profile):
        """
        Sync repositories for a GitHub profile
        """
        # Get repositories from GitHub - prioritize org repositories
        repositories = self.get_user_org_repositories(profile.github_username)
        
        if not repositories:
            logger.warning(f"[GitHubService] No repositories found for user: {profile.github_username}")
            # Clean up repository access records since we found no repositories
            self.clean_up_removed_repositories(profile, [])
            return
        
        # Log stats about repositories
        private_repos = [r for r in repositories if r.get('isPrivate', False)]
        logger.info(f"[GitHubService] Found {len(repositories)} total repositories, {len(private_repos)} private repositories")
        
        # Keep track of how many repositories were actually processed
        processed_count = 0
        skipped_count = 0
        processed_repo_ids = []
        
        # Process each repository
        for repo_data in repositories:
            repo_name = repo_data.get('name')
            repo_owner = repo_data.get('owner', {}).get('login')
            repo_full_name = repo_data.get('nameWithOwner')
            
            if not all([repo_name, repo_owner, repo_full_name]):
                logger.warning(f"[GitHubService] Skipping repository with incomplete data: {repo_data}")
                skipped_count += 1
                continue
            
            # If we have an organization set, only process repositories from that organization
            if ORGANIZATION and repo_owner != ORGANIZATION:
                logger.debug(f"[GitHubService] Skipping non-organization repository: {repo_full_name}")
                skipped_count += 1
                continue
                
            # Get or create repository
            repo, _ = Repository.objects.update_or_create(
                full_name=repo_full_name,
                defaults={
                    'name': repo_name,
                    'owner': repo_owner,
                    'url': repo_data.get('url', ''),
                    'description': repo_data.get('description', ''),
                    'is_private': repo_data.get('isPrivate', False)
                }
            )
            
            processed_count += 1
            processed_repo_ids.append(repo.id)
            
            # Sync repository stats for this user
            self.sync_repository_stats(profile, repo)
            
        logger.info(f"[GitHubService] Processed {processed_count} repositories, skipped {skipped_count} repositories")
        
        # Clean up any repository access records that are no longer valid
        self.clean_up_removed_repositories(profile, processed_repo_ids)
    
    def clean_up_removed_repositories(self, profile, current_repo_ids):
        """
        Remove repository statistics for repositories that the user no longer has access to
        """
        from .models import UserRepositoryStats
        
        try:
            # Get all repository stats for this profile
            all_repo_stats = UserRepositoryStats.objects.filter(profile=profile)
            
            # Find repository stats that are no longer valid
            if current_repo_ids:
                removed_repo_stats = all_repo_stats.exclude(repository__id__in=current_repo_ids)
            else:
                # If no repositories were found, keep repo stats for now to avoid data loss
                # in case this was a temporary API error
                return
            
            removed_count = removed_repo_stats.count()
            
            if removed_count > 0:
                # Log which repositories are being removed
                removed_repos = [f"{rs.repository.owner}/{rs.repository.name}" for rs in removed_repo_stats]
                logger.info(f"[GitHubService] Removing {removed_count} repository access records for {profile.github_username}: {', '.join(removed_repos)}")
                
                # Delete the stats
                removed_repo_stats.delete()
                
                logger.info(f"[GitHubService] Successfully removed {removed_count} outdated repository access records")
        except Exception as e:
            error_message = f"[GitHubService] Error cleaning up removed repositories: {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            # We don't want to break the sync process if cleanup fails
            pass
    
    def sync_repository_stats(self, profile, repository):
        """
        Sync repository statistics for a user
        """
        # Try to get commit stats from our own method first
        try:
            # First check if this is an organization repository
            if repository.owner == ORGANIZATION:
                logger.info(f"[GitHubService] Using organization API for repo stats: {repository.name}")
                
                # Use our own method for getting commit history
                commit_stats = self.fetch_commit_history_for_user(repository.name, profile.github_username)
                
                if commit_stats:
                    logger.info(f"[GitHubService] Found commit stats via org API for {profile.github_username} in {repository.name}")
                    
                    # Get commit count from REST API
                    # We need to make an additional request to get commit count
                    headers = self._get_rest_headers()
                    url = f"{self.GITHUB_REST_API_URL}/repos/{repository.owner}/{repository.name}/commits"
                    params = {'author': profile.github_username}
                    
                    try:
                        response = requests.get(url, headers=headers, params=params)
                        response.raise_for_status()
                        if 'link' in response.headers:
                            # Parse the Link header to get the total count
                            import re
                            link = response.headers['link']
                            match = re.search(r'page=(\d+)>; rel="last"', link)
                            if match:
                                last_page = int(match.group(1))
                                # Estimate commit count based on pages (GitHub returns 30 per page)
                                commit_count = (last_page - 1) * 30 + len(response.json())
                            else:
                                commit_count = len(response.json())
                        else:
                            # If no Link header, we got all the commits in one page
                            commit_count = len(response.json())
                    except Exception as e:
                        logger.error(f"[GitHubService] Error getting commit count: {str(e)}")
                        commit_count = 0  # Default if we can't get the count
                    
                    # Extract statistics 
                    lines_added = commit_stats.get('lines_added', 0)
                    lines_deleted = commit_stats.get('lines_deleted', 0)
                    net_lines = commit_stats.get('net_lines', 0)
                    
                    # Update repository stats
                    UserRepositoryStats.objects.update_or_create(
                        profile=profile,
                        repository=repository,
                        defaults={
                            'commits': commit_count,
                            'lines_added': lines_added,
                            'lines_deleted': lines_deleted,
                            'net_lines': net_lines,
                            'last_updated': timezone.now()
                        }
                    )
                    
                    logger.info(f"[GitHubService] Updated stats for {profile.github_username} in {repository.name}")
                    return
        except Exception as e:
            logger.error(f"[GitHubService] Error using organization API for repo stats: {str(e)}")
            logger.info(f"[GitHubService] Falling back to standard API for repo stats")
        
        # Fall back to standard GitHub API if organization API fails
        # Get commits for this user in this repository
        commits = self.get_repository_commits(
            repository.owner, 
            repository.name, 
            profile.github_email or profile.github_username
        )
        
        if not commits:
            return
        
        # Count total commits
        commit_count = len(commits)
        
        # Initialize counters
        lines_added = 0
        lines_deleted = 0
        
        # Process commit stats
        for commit_data in commits:
            commit_sha = commit_data.get('oid')
            if not commit_sha:
                continue
                
            # Extract stats directly from GraphQL response
            commit_lines_added = commit_data.get('additions', 0)
            commit_lines_deleted = commit_data.get('deletions', 0)
            
            # Update counters
            lines_added += commit_lines_added
            lines_deleted += commit_lines_deleted
            
            # Create or update commit history
            commit_date = commit_data.get('committedDate')
            commit_message = commit_data.get('messageHeadline', '')
            
            if commit_date:
                CommitHistory.objects.update_or_create(
                    profile=profile,
                    repository=repository,
                    commit_hash=commit_sha,
                    defaults={
                        'commit_message': commit_message,
                        'commit_date': commit_date,
                        'lines_added': commit_lines_added,
                        'lines_deleted': commit_lines_deleted
                    }
                )
        
        # Calculate net lines
        net_lines = lines_added - lines_deleted
        
        # Update repository stats
        UserRepositoryStats.objects.update_or_create(
            profile=profile,
            repository=repository,
            defaults={
                'commits': commit_count,
                'lines_added': lines_added,
                'lines_deleted': lines_deleted,
                'net_lines': net_lines,
                'last_updated': timezone.now()
            }
        )
    
    def get_user_stats(self, username_or_obj):
        """
        Get aggregated GitHub stats for a user
        """
        if isinstance(username_or_obj, str):
            try:
                user = User.objects.get(username=username_or_obj)
            except User.DoesNotExist:
                return None
        else:
            user = username_or_obj
        
        # Try to get GitHub profile by direct user relation
        try:
            profile = GitHubProfile.objects.get(user=user)
            logger.debug(f"[GitHubService] Found GitHub profile for user: {user.username}")
        except GitHubProfile.DoesNotExist:
            logger.warning(f"[GitHubService] No direct GitHub profile found for user: {user.username}")
            
            # Try finding user in organization by email
            if hasattr(user, 'email') and user.email:
                email = user.email
                logger.debug(f"[GitHubService] Trying to find GitHub user by organization email lookup: {email}")
                github_user = self.find_org_member_by_email(email)
                
                if github_user:
                    github_username = github_user['login']
                    logger.info(f"[GitHubService] Found GitHub user in organization with email {email}: {github_username}")
                    
                    # Create profile for this user automatically
                    try:
                        logger.info(f"[GitHubService] Creating GitHub profile for user {user.username} with GitHub username {github_username}")
                        profile = GitHubProfile.objects.create(
                            user=user,
                            github_username=github_username,
                            github_email=email,
                            avatar_url=github_user.get('avatarUrl', ''),
                            last_synced=timezone.now()
                        )
                        
                        # Also update User model's github_username field
                        try:
                            user.github_username = github_username
                            user.save(update_fields=['github_username'])
                            logger.info(f"[GitHubService] Updated User model github_username field: {github_username}")
                        except Exception as e:
                            logger.error(f"[GitHubService] Error updating User model github_username field: {str(e)}")
                        
                        # Auto-sync the repositories for this user
                        self.sync_user_repositories(profile)
                        logger.info(f"[GitHubService] Successfully created profile and synced repositories")
                    except Exception as e:
                        logger.error(f"[GitHubService] Error creating profile from organization lookup: {str(e)}")
                        return None
                else:
                    # Try finding by local email match
                    try:
                        profile = GitHubProfile.objects.filter(github_email=email).first()
                        if profile:
                            logger.debug(f"[GitHubService] Found GitHub profile by email match: {email}")
                            
                            # Update User model's github_username field
                            try:
                                user.github_username = profile.github_username
                                user.save(update_fields=['github_username'])
                                logger.info(f"[GitHubService] Updated User model github_username from matched profile: {profile.github_username}")
                            except Exception as e:
                                logger.error(f"[GitHubService] Error updating User model github_username field: {str(e)}")
                        else:
                            logger.warning(f"[GitHubService] No GitHub profile found for email: {email}")
                            return None
                    except Exception as e:
                        logger.error(f"[GitHubService] Error finding profile by email: {str(e)}")
                        return None
            else:
                logger.warning(f"[GitHubService] No GitHub profile found for user: {user.username}")
                return None
        
        # Get all repository stats for this user
        repo_stats = UserRepositoryStats.objects.filter(profile=profile)
        
        # Aggregate stats
        agg_stats = repo_stats.aggregate(
            total_commits=Sum('commits'),
            total_lines_added=Sum('lines_added'),
            total_lines_deleted=Sum('lines_deleted'),
            total_net_lines=Sum('net_lines')
        )
        
        # Build result
        result = {
            'username': user.username,
            'github_username': profile.github_username,
            'avatar_url': profile.avatar_url,
            'total_commits': agg_stats.get('total_commits') or 0,
            'total_lines_added': agg_stats.get('total_lines_added') or 0,
            'total_lines_deleted': agg_stats.get('total_lines_deleted') or 0,
            'net_lines': agg_stats.get('total_net_lines') or 0,
            'repositories_count': repo_stats.count(),
            'last_synced': profile.last_synced
        }
        
        return result
    
    def find_org_member_by_email(self, email):
        """
        Find an organization member by their email using GraphQL API
        Uses the organization settings from Poly_Agent config
        """
        logger.info(f"[GitHubService] Looking up organization member with email: {email}")
        
        if not ORGANIZATION:
            logger.error(f"[GitHubService] No organization specified in config")
            return None
        
        headers = self._get_headers()
        
        # We need to get all members and filter for email match
        # There's no direct query for members by email in the GitHub API
        logger.debug(f"[GitHubService] Searching for organization member with email: {email}")
        return self.search_all_org_members_for_email(email)

    def search_all_org_members_for_email(self, email):
        """
        Search all organization members for a matching email
        This method fetches all members and checks their emails, which can be expensive
        for large organizations
        """
        if not ORGANIZATION:
            logger.error(f"[GitHubService] No organization specified in config")
            return None
        
        headers = self._get_headers()
        query = """
        query($org: String!, $cursor: String) {
          organization(login: $org) {
            membersWithRole(first: 100, after: $cursor) {
              pageInfo {
                endCursor
                hasNextPage
              }
              nodes {
                login
                name
                email
                avatarUrl
              }
            }
          }
        }
        """
        
        has_next_page = True
        cursor = None
        all_members = []
        
        try:
            # Iterate through pages of members
            while has_next_page:
                variables = {
                    "org": ORGANIZATION,
                    "cursor": cursor
                }
                
                logger.debug(f"[GitHubService] Fetching organization members page, cursor: {cursor}")
                response = requests.post(
                    self.GITHUB_API_URL, 
                    json={"query": query, "variables": variables}, 
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"[GitHubService] GraphQL errors fetching org members: {data['errors']}")
                    break
                
                result = data["data"]["organization"]["membersWithRole"]
                members = result["nodes"]
                all_members.extend(members)
                
                page_info = result["pageInfo"]
                has_next_page = page_info["hasNextPage"]
                cursor = page_info["endCursor"]
            
            logger.info(f"[GitHubService] Found {len(all_members)} total organization members")
            
            # Search for the email - do a case insensitive match
            # First try exact match
            for member in all_members:
                member_email = member.get("email")
                if member_email and member_email.lower() == email.lower():
                    logger.info(f"[GitHubService] Found organization member with matching email: {member['login']}")
                    return member

            # If not found by exact match, try domain-only match as a fallback
            # This handles cases where email domains might differ slightly
            if '@' in email:
                username, domain = email.lower().split('@', 1)
                for member in all_members:
                    member_email = member.get("email")
                    if member_email and '@' in member_email:
                        _, member_domain = member_email.lower().split('@', 1)
                        if domain == member_domain:
                            logger.info(f"[GitHubService] Found organization member with matching email domain: {member['login']}")
                            logger.info(f"[GitHubService] User email: {email}, Member email: {member_email}")
                            return member
                
            # Try fallback to user's username
            email_username = email.split('@')[0] if '@' in email else email
            for member in all_members:
                if member.get('login', '').lower() == email_username.lower():
                    logger.info(f"[GitHubService] Found organization member with matching username: {member['login']}")
                    return member
                
            logger.warning(f"[GitHubService] No organization member found with email: {email}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"[GitHubService] Error searching organization members: {str(e)}")
            return None
    
    def _get_headers(self):
        """Get headers for GraphQL API requests"""
        if not self.access_token:
            logger.error("[GitHubService] No access token available for API request")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    def _get_rest_headers(self):
        """Get headers for REST API requests"""
        if not self.access_token:
            logger.error("[GitHubService] No access token available for REST API request")
        return {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
        } 