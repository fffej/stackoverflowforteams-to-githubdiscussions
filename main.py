import argparse
import sys
from github_discussions_client import GitHubDiscussionsClient
from stackoverflow_data_dump import *
import traceback
import re

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

def get_articles_category_id(categories):
    """Helper function to find the Q&A category ID."""
    for category in categories["repository"]["discussionCategories"]["nodes"]:
        if category['name'] == 'Articles':
            return category['id']
    return None

# Slow, but fine for small lists
def find_user_by_id(users: list[UserProfile], user_id: int) -> Optional[UserProfile]:
    return next((user for user in users if user.id == user_id), None)

# We make the assumption that the images are in the same repository
# Replace image URLs, which means I need to find things like this
# [![enter image description here](https://stackoverflowteams.com/c/XYZ/images/s/8505b790-b95e-44e9-b937-884d990f53c4.png)]
# [![enter image description here](../blob/main/images/8505b790-b95e-44e9-b937-884d990f53c4.png?raw=true)]
def rewrite_image_urls(markdown_text):
   pattern = r'\(https://stackoverflowteams\.com/c/[^/]+/images/[^/]+/([a-f0-9-]+)\.png\)'
   
   # really?
   def replace(match):
       uuid = match.group(1).replace('-', '')
       return f'(../blob/main/images/{uuid}.png?raw=true)'
   
   return re.sub(pattern, replace, markdown_text)

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
        articles_category_id = get_articles_category_id(categories)
        if not articles_category_id:
            print("Error: Could not find articles category in the repository")
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

        process_questions_and_answers = False
        process_articles = True

        for post in posts:
            if process_questions_and_answers and post.postType == "question":
                print(f"\nProcessing question: {post.title}")   

                attribution = ""
                maybeUser = find_user_by_id(users, post.ownerUserId)
                if maybeUser is not None:                    
                    attribution = f"Written by {maybeUser.displayName}\n"
                
                result = client.create_discussion(
                    repository_id=repo_id,
                    category_id=qa_category_id,
                    title=post.title,
                    body=attribution + rewrite_image_urls(post.bodyMarkdown))   
                discussion_tokens[post.id] = result     

                if post.acceptedAnswerId is not None and post.acceptedAnswerId > 0:
                    answer_ids[post.id] = post.acceptedAnswerId

            elif process_questions_and_answers and post.postType == "answer":
                parent_discussion = discussion_tokens.get(post.parentId)
                if parent_discussion is None:
                    print(f"Error: Answer {post.id} has no parent discussion") 
                
                result = client.create_comment(parent_discussion['createDiscussion']['discussion']['id'], post.bodyMarkdown, answer_ids.get(post.parentId,-1) == post.id)  
            elif process_articles and post.postType == "article":
                print(f'Processing article: {post.title}')
                attribution = ""
                maybeUser = find_user_by_id(users, post.ownerUserId)
                if maybeUser is not None:                    
                    attribution = f"Written by {maybeUser.displayName}\n"
                                
                result = client.create_discussion(
                    repository_id=repo_id,
                    category_id=articles_category_id,
                    title=post.title,
                    body=attribution + rewrite_image_urls(post.bodyMarkdown))  


        # Assumption (tagWki and takWikiExcerpt contain little value)
        # What about collection?

        return
            
    except Exception as e:
        print(f"Error initializing client: {e}")
        stack_trace = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print(stack_trace)        
        sys.exit(1)

if __name__ == "__main__":
    main()