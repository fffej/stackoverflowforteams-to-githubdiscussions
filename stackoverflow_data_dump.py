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

@dataclass
class Badge:
    isCode: bool
    tagBased: bool
    single: bool
    awardedCount: int
    id: int
    badgeClass: str  # Simplified from enum to string
    badgeReasonTypeId: str
    awardFrequency: int
    description: str
    name: str

def parse_badge(badge_dict: dict) -> Badge:
    return Badge(
        isCode=badge_dict["isCode"],
        tagBased=badge_dict["tagBased"],
        single=badge_dict["single"],
        awardedCount=badge_dict["awardedCount"],
        id=badge_dict["id"],
        badgeClass=badge_dict["class"],
        badgeReasonTypeId=badge_dict["badgeReasonTypeId"],
        awardFrequency=badge_dict["awardFrequency"],
        description=badge_dict["description"],
        name=badge_dict["name"]
    )

def load_stackoverflow_badges(file_path: str) -> List[Badge]:
    """"
    Reads a JSON file containing badge information and returns a list of Badge objects.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [parse_badge(badge_dict) for badge_dict in data]

@dataclass
class Comment:
    # Required fields
    id: int
    creationDate: datetime     
    postId: int 
    postCommentTypeId: str     
    userId: int 
    text: str
    replyToUserId: int
    editCount: int
    score: int

def load_stackoverflow_comments(filename: str) -> List[Comment]:
    """
    Parse comments from a JSON file into a list of strongly typed Comment objects
    
    Args:
        filename: Path to the JSON file containing comment data
        
    Returns:
        List of Comment objects
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {filename}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {filename}")
    
    comments = []
    
    for data in comments_data:
        # Convert ISO format string to datetime if present
        creation_date = None
        if 'creationDate' in data and data['creationDate']:
            try:
                creation_date = datetime.fromisoformat(data['creationDate'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        
        # Create Comment object with all fields optional except id
        comment = Comment(
            id=data['id'],
            creationDate=creation_date,
            editCount=data.get('editCount'),
            postId=data.get('postId'),
            postCommentTypeId=data.get('postCommentTypeId'),
            score=data.get('score'),
            userId=data.get('userId'),
            text=data.get('text', ''),
            replyToUserId=data.get('replyToUserId')
        )
        comments.append(comment)
    
    return comments

@dataclass
class ImageRecord:
    creationDate: datetime
    imageGuid: str
    id: int

    def __post_init__(self):
        # Convert string to datetime if it's not already a datetime object
        if isinstance(self.creationDate, str):
            self.creationDate = datetime.fromisoformat(self.creationDate.replace('Z', '+00:00'))



def load_stackoverflow_images(file_path: str) -> List[ImageRecord]:
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            # Convert JSON data into list of ImageRecord objects
            return [ImageRecord(**record) for record in json_data]
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")

@dataclass
class UserProfile:
    id: int
    accountId: int
    userTypeId: str
    displayName: str
    realName: str
    profileImageUrl: str
    reputation: int
    views: int
    answerCount: int
    questionCount: int
    goldBadges: int
    silverBadges: int
    bronzeBadges: int
    lastAccessDate: datetime
    creationDate: datetime    
    lastLoginDate: datetime
    location: Optional[str] = None
    title: Optional[str] = None
    lastModifiedDate: Optional[datetime] = None

def load_stackoverflow_users(file_path: str) -> List[UserProfile]:
    """
    Convert JSON data into a list of UserProfile objects.
    Handles datetime parsing and optional fields.
    """
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        profiles = []
        for data in json_data:
            # Convert ISO datetime strings to datetime objects
            datetime_fields = ['lastAccessDate', 'creationDate', 'lastModifiedDate', 'lastLoginDate']
            for field in datetime_fields:
                if field in data:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
            
            # Create UserProfile object with unpacked dictionary
            profile = UserProfile(**data)
            profiles.append(profile)
        
        return profiles
    
@dataclass
class StackOverflowTag:
    """Represents a StackOverflow tag with its associated metadata."""
    id: int
    name: str
    count: int
    is_special_tag: bool
    creation_date: datetime    
    excerpt_post_id: int | None = None
    wiki_post_id: int | None = None

def load_stackoverflow_tags(file_path: str) -> List[StackOverflowTag]:
    try:
        with open(file_path, 'r') as f:
            tags_data = json.load(f)

        tags = []
        for tag_data in tags_data:
            # Convert camelCase to snake_case for Python conventions
            tag = StackOverflowTag(
                id=tag_data['id'],
                name=tag_data['name'],
                count=tag_data['count'],
                is_special_tag=tag_data['isSpecialTag'],
                creation_date=datetime.fromisoformat(tag_data['creationDate'].replace('Z', '+00:00')),
                wiki_post_id=tag_data.get('wikiPostId'),
                excerpt_post_id=tag_data.get('excerptPostId')
            )
            tags.append(tag)

        return tags

    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {str(e)}", e.doc, e.pos)
    except KeyError as e:
        raise KeyError(f"Missing required field in JSON data: {str(e)}")
    except ValueError as e:
        raise ValueError(f"Invalid data format in JSON: {str(e)}")        