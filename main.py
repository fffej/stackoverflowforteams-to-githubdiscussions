import argparse
import sys
from github_discussions_client import GitHubDiscussionsClient

def parse_args():
    parser = argparse.ArgumentParser(
        description='GitHub Discussions Migration Tool',
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

def main():
    args = parse_args()
    
    try:
        # Initialize the client with the provided token
        client = GitHubDiscussionsClient(args.token)
        
        # If a repository is specified, get its information
        if args.repo:
            try:
                owner, repo_name = args.repo.split('/')
                
                # Test the connection by getting repository information
                repo_info = client.get_repository_id(owner, repo_name)
                print(f"Successfully connected to repository: {args.repo}")
                
                # Get and display available discussion categories
                categories = client.get_discussion_categories(owner, repo_name)
                print("\nAvailable discussion categories:")
                for category in categories["repository"]["discussionCategories"]["nodes"]:
                    print(f"- {category['name']}: {category['id']}")
                    
            except ValueError:
                print("Error: Repository should be in format 'owner/name'")
                sys.exit(1)
            except Exception as e:
                print(f"Error accessing repository: {e}")
                sys.exit(1)
        else:
            print("Successfully initialized client. Use --repo to specify a repository.")
            
    except Exception as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()