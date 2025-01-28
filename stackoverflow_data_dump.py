from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import List, Optional, TypedDict, Dict

@dataclass
class StackOverflowPost:
    # Required fields with defaults
    id: int = 0
    postType: str = ""
    postState: str = ""
    creationDate: datetime = field(default_factory=lambda: datetime.now())
    bodyMarkdown: str = ""
    body: str = ""
    
    # Fields that might be missing in some posts, with defaults
    favoriteCount: int = 0
    commentCount: int = 0
    answerCount: int = 0
    answerScore: int = 0
    score: int = 0
    ownerUserId: int = 0
    
    # Optional fields for questions
    viewCount: Optional[int] = None
    acceptedAnswerId: Optional[int] = None
    tags: Optional[str] = None
    title: Optional[str] = None
    
    # Optional fields for answers
    parentId: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'StackOverflowPost':
        # Convert ISO format string to datetime
        if 'creationDate' in data:
            data['creationDate'] = datetime.fromisoformat(data['creationDate'].replace('Z', '+00:00'))
        
        # Filter out unexpected fields
        valid_fields = cls.__annotations__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Create instance with filtered data
        return cls(**filtered_data)

def load_stackoverflow_posts(file_path: str) -> List[StackOverflowPost]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [StackOverflowPost.from_dict(post) for post in data]

class Account(TypedDict):
    accountId: int
    verifiedEmail: str

def load_stackoverflow_accounts(json_file_path: str) -> Dict[int, str]:
    """
    Reads a JSON file containing account information and returns a mapping of account IDs to emails.       
    Returns:
        Dict[int, str]: Dictionary mapping account IDs (int) to email addresses (str)
    """
    with open(json_file_path, 'r') as file:
        accounts: List[Account] = json.load(file)
    
    return {account['accountId']: account['verifiedEmail'] for account in accounts}