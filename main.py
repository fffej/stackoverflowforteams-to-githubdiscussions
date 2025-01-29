import argparse
import sys
from github_discussions_client import GitHubDiscussionsClient
from stackoverflow_data_dump import *

def parse_args():
    parser = argparse.ArgumentParser(
        description='GitHub Discussions Migration Tool. Assumes there is a data/ directory with Stack Overflow data dump.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python main.py --token YOUR_GITHUB_TOKEN
  python main.py --token YOUR_GITHUB_TOKEN --repo owner/repo-name
        """
    )
    
    parser.add_argument(
        '--token',
        required=True,
        help='GitHub Personal Access Token'
    )
    
    parser.add_argument(
        '--repo',
        help='Repository in format owner/name (e.g., octocat/Hello-World)',
        default=None
    )
    
    return parser.parse_args()

def get_qa_category_id(categories):
    """Helper function to find the Q&A category ID."""
    for category in categories["repository"]["discussionCategories"]["nodes"]:
        if category['name'] == 'Q&A':
            return category['id']
    return None

def main():
    args = parse_args()
    
    try:
        # Initialize the client with the provided token
        client = GitHubDiscussionsClient(args.token)
        owner, repo_name = args.repo.split('/')
        repo_info = client.get_repository_id(owner, repo_name)
        repo_id = repo_info["repository"]["id"]
        print(f"Successfully connected to repository: {args.repo}")
        
        # Find the Q&A discussion category ID
        categories = client.get_discussion_categories(owner, repo_name)
        qa_category_id = get_qa_category_id(categories)
        if not qa_category_id:
            print("Error: Could not find Q&A category in the repository")
            sys.exit(1)       

        # Initialize the export data
        posts = load_stackoverflow_posts("data/posts.json")
        accounts = load_stackoverflow_accounts("data/accounts.json")
        badges = load_stackoverflow_badges("data/badges.json")
        comments = load_stackoverflow_comments("data/comments.json")
        images = load_stackoverflow_images("data/images.json")
        users = load_stackoverflow_users("data/users.json")
        tags = load_stackoverflow_tags("data/tags.json")

        # Stage 1
        # For every question, create a discussion adding relevant answers as comments with GitHub Discussions API
        discussion_tokens = {}
        answer_ids = {}

        for post in posts:
            if post.postType == "question":
                print(f"\nProcessing question: {post.title}")   

                attribution = ""
                if post.ownerUserId != -1:
                    attribution = f"Written by {users[post.ownerUserId].displayName})\n"
                
                result = client.create_discussion(
                    repository_id=repo_id,
                    category_id=qa_category_id,
                    title=post.title,
                    body=attribution + post.bodyMarkdown)   
                discussion_tokens[post.id] = result     

                if post.acceptedAnswerId > 0:
                    answer_ids[post.id] = post.acceptedAnswerId

            elif post.postType == "answer":
                parent_discussion = discussion_tokens.get(post.parentId)
                if parent_discussion is None:
                    print(f"Error: Answer {post.id} has no parent discussion") 
                result = client.create_comment(parent_discussion['createDiscussion']['discussion']['id'], post.bodyMarkdown, answer_ids.get(post.parentId,-1) == post.id)  
            elif post.postType == "article":
                print(f"Skipping article: {post.title}")             

        # Assumption (tagWki and takWikiExcerpt contain little value)
        # What about collection?

        return
            
    except Exception as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()