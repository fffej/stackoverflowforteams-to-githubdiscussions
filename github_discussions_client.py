from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time
from gql.transport.exceptions import TransportQueryError

class RateLimitedTransport(RequestsHTTPTransport):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def execute(self, document, variable_values=None, *args, **kwargs):
        try:
            response = super().execute(document, variable_values, *args, **kwargs)

            # Extract rate limit headers from the raw HTTP response
            http_response = self.session.post(self.url, json={"query": str(document)}, headers=self.headers)
            rate_limit_headers = http_response.headers

            # Extract and convert rate limit values, handling potential missing headers
            self.rate_limit_remaining = int(rate_limit_headers.get("x-ratelimit-remaining", -1))
            self.rate_limit_reset = int(rate_limit_headers.get("x-ratelimit-reset", -1))

            print(f"Rate Limit Remaining: {self.rate_limit_remaining}")
            print(f"Rate Limit Reset Time (Epoch): {self.rate_limit_reset}")

            return response

        except Exception as e:
            print(f"Error while executing query: {e}")
            raise

class GitHubDiscussionsClient:

    def __init__(self, token):
        self.transport = RateLimitedTransport(
            url='https://api.github.com/graphql',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)

    def _wait_if_rate_limited(self):
        if self.transport.rate_limit_remaining is None or self.transport.rate_limit_reset is None:
            print(f"Rate limit headers not received; proceeding cautiously.")
            return

        if self.transport.rate_limit_remaining == -1 or self.transport.rate_limit_reset == -1:
            print(f"Rate limit headers missing or invalid. Assuming API limits are unknown.")
            return

        if self.transport.rate_limit_remaining == 0:
            reset_time = self.transport.rate_limit_reset
            sleep_time = max(reset_time - time.time(), 1)
            print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds (until reset).")
            time.sleep(sleep_time)
        else:
            print(f"Proceeding with API call. {self.transport.rate_limit_remaining} calls remaining.")

    def execute_query(self, query, variables=None):
        self._wait_if_rate_limited()
        return self.client.execute(query, variable_values=variables)   

    def execute_query(self, query, variables=None):
        max_retries = 4
        attempt = 0
        
        while attempt < max_retries:
            try:
                self._wait_if_rate_limited()
                return self.client.execute(query, variable_values=variables)
            except Exception as e:
                if "was submitted too quickly" in str(e):
                    print(f"Rate limit error detected. Retrying...")
                    attempt += 1
                    if attempt < max_retries:
                        # Exponential backoff: 5s, 25s, 125s
                        delay = 5 ** attempt
                        print(f"Sleeping for {delay} seconds before retrying...")
                        time.sleep(delay)
                        continue
                raise  # Re-raise if it's not a rate limit error or we're out of retries
        
        # If we get here, we've exhausted all retries
        raise TransportQueryError("Failed after maximum retries due to rate limiting")             

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
        
        return self.execute_query(mutation, variables=variables)

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
        
        return self.execute_query(query, variables=variables)

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
        
        return self.execute_query(query, variables=variables)

    def create_comment(self, discussion_id, body, is_answer=False):
        """
        Add a comment to an existing discussion.
        
        Args:
            discussion_id (str): The ID of the discussion to comment on
            body (str): The content of the comment
            is_answer (bool, optional): Whether this comment should be marked as the answer. Defaults to False.
        
        Returns:
            dict: Response containing the created comment's information and success status
        """
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
        
        # Create the comment first
        result = self.execute_query(mutation, variables=variables)
        
        # If this comment should be marked as the answer, make a second call
        if is_answer and result.get('addDiscussionComment', {}).get('comment', {}).get('id'):
            mark_answer_mutation = gql("""
                mutation MarkDiscussionCommentAsAnswer($input: MarkDiscussionCommentAsAnswerInput!) {
                    markDiscussionCommentAsAnswer(input: $input) {
                        discussion {
                            id
                        }
                    }
                }
            """)
            
            mark_variables = {
                "input": {
                    "id": result['addDiscussionComment']['comment']['id']
                }
            }
            
            # Mark the comment as the answer
            self.execute_query(mark_answer_mutation, variables=mark_variables)
        
        return result