from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os

class GitHubDiscussionsClient:
    def __init__(self, token):
        # Initialize the GraphQL client
        transport = RequestsHTTPTransport(
            url='https://api.github.com/graphql',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def create_discussion(self, repository_id, category_id, title, body):
        """Create a new discussion in the specified repository."""
        mutation = gql("""
            mutation CreateDiscussion($input: CreateDiscussionInput!) {
                createDiscussion(input: $input) {
                    discussion {
                        id
                        url
                    }
                }
            }
        """)
        
        variables = {
            "input": {
                "repositoryId": repository_id,
                "categoryId": category_id,
                "title": title,
                "body": body
            }
        }
        
        return self.client.execute(mutation, variable_values=variables)

    def get_discussion_categories(self, owner, name):
        """Get available discussion categories for a repository."""
        query = gql("""
            query GetDiscussionCategories($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    discussionCategories(first: 100) {
                        nodes {
                            id
                            name
                            description
                        }
                    }
                }
            }
        """)
        
        variables = {
            "owner": owner,
            "name": name
        }
        
        return self.client.execute(query, variable_values=variables)

    def get_repository_id(self, owner, name):
        """Get the GitHub repository ID."""
        query = gql("""
            query GetRepositoryId($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    id
                }
            }
        """)
        
        variables = {
            "owner": owner,
            "name": name
        }
        
        return self.client.execute(query, variable_values=variables)

    def create_comment(self, discussion_id, body):
        """Add a comment to an existing discussion."""
        mutation = gql("""
            mutation AddDiscussionComment($input: AddDiscussionCommentInput!) {
                addDiscussionComment(input: $input) {
                    comment {
                        id
                        url
                    }
                }
            }
        """)
        
        variables = {
            "input": {
                "discussionId": discussion_id,
                "body": body
            }
        }
        
        return self.client.execute(mutation, variable_values=variables)

# Example usage:
if __name__ == "__main__":
    # Initialize client with your GitHub token
    token = os.getenv("GITHUB_TOKEN")
    client = GitHubDiscussionsClient(token)
    
    # Get repository ID
    repo_info = client.get_repository_id("owner", "repo-name")
    repo_id = repo_info["repository"]["id"]
    
    # Get discussion categories
    categories = client.get_discussion_categories("owner", "repo-name")
    category_id = categories["repository"]["discussionCategories"]["nodes"][0]["id"]
    
    # Create a new discussion
    result = client.create_discussion(
        repository_id=repo_id,
        category_id=category_id,
        title="Migration Test Discussion",
        body="This is a test discussion created via GraphQL"
    )
    
    # Add a comment to the discussion
    discussion_id = result["createDiscussion"]["discussion"]["id"]
    client.create_comment(discussion_id, "This is a test comment")