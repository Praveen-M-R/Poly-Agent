import requests
from Poly_Agent.config import GIT_ACCESS_KEY, ORGANIZATION
import logging

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/graphql"

def fetch_organization_members():
    headers = {
        "Authorization": f"Bearer {GIT_ACCESS_KEY}",
        "Content-Type": "application/json"
    }

    query = """
    query($org: String!) {
      organization(login: $org) {
        membersWithRole(first: 100) {
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

    variables = {"org": ORGANIZATION}
    response = requests.post(GITHUB_API_URL, json={"query": query, "variables": variables}, headers=headers)
    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    members = data["data"]["organization"]["membersWithRole"]["nodes"]
    logger.debug(f"Processed members data: {members}")
    return members

def fetch_organization_repositories():
    headers = {
        "Authorization": f"Bearer {GIT_ACCESS_KEY}",
        "Content-Type": "application/json"
    }

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
    response = requests.post(GITHUB_API_URL, json={"query": query, "variables": variables}, headers=headers)
    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    repositories = data["data"]["organization"]["repositories"]["nodes"]
    logger.debug(f"Processed repositories data: {repositories}")
    return repositories

def fetch_repository_contributors(repository_name):
    headers = {
        "Authorization": f"Bearer {GIT_ACCESS_KEY}",
        "Content-Type": "application/json"
    }

    # Fetch collaborators via GraphQL
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

    variables = {"org": ORGANIZATION, "repo": repository_name}
    response = requests.post(GITHUB_API_URL, json={"query": query, "variables": variables}, headers=headers)
    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    collaborators = data["data"]["repository"]["collaborators"]["nodes"]
    logger.debug(f"Processed collaborators data for repo {repository_name}: {collaborators}")

    # Fetch contributors via REST API
    rest_url = f"https://api.github.com/repos/{ORGANIZATION}/{repository_name}/contributors"
    rest_headers = {
        "Authorization": f"token {GIT_ACCESS_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    rest_response = requests.get(rest_url, headers=rest_headers)
    if rest_response.status_code != 200:
        raise Exception(f"Failed to fetch contributors from REST API: {rest_response.text}")
    contributors_raw = rest_response.json()
    logger.debug(f"Processed contributors data from REST API for repo {repository_name}: {contributors_raw}")

    # Map contributors to include contributions count (number of commits)
    contributors = []
    for contributor in contributors_raw:
        contributors.append({
            "login": contributor.get("login"),
            "contributions": contributor.get("contributions", 0),
            "avatarUrl": contributor.get("avatar_url"),
            "url": contributor.get("html_url"),
            # Other fields can be added if needed
        })

    return {
        "collaborators": collaborators,
        "contributors": contributors
    }

def fetch_commit_history_for_user(repository_name, username):
    """
    Fetch commit history for a given user in a repository and calculate total lines added.
    """
    rest_headers = {
        "Authorization": f"token {GIT_ACCESS_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    commits_url = f"https://api.github.com/repos/{ORGANIZATION}/{repository_name}/commits?author={username}&per_page=100"
    total_lines_added = 0
    total_lines_deleted = 0
    page = 1

    while True:
        paged_url = f"{commits_url}&page={page}"
        response = requests.get(paged_url, headers=rest_headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch commits for {username} in repo {repository_name}: {response.text}")
            break
        commits = response.json()
        if not commits:
            break

        for commit in commits:
            sha = commit.get("sha")
            if not sha:
                continue
            commit_detail_url = f"https://api.github.com/repos/{ORGANIZATION}/{repository_name}/commits/{sha}"
            detail_response = requests.get(commit_detail_url, headers=rest_headers)
            if detail_response.status_code != 200:
                logger.error(f"Failed to fetch commit details for {sha} in repo {repository_name}: {detail_response.text}")
                continue
            commit_data = detail_response.json()
            stats = commit_data.get("stats", {})
            additions = stats.get("additions", 0)
            deletions = stats.get("deletions", 0)
            total_lines_added += additions
            total_lines_deleted += deletions

        page += 1

    return {
        "lines_added": total_lines_added,
        "lines_deleted": total_lines_deleted,
        "net_lines": total_lines_added - total_lines_deleted
    }
