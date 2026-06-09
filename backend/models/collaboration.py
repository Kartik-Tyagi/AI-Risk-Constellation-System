"""
Collaboration Models
Data models for workspaces, comments, activities, and users
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class UserRole(Enum):
    """User roles in workspace"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ActivityType(Enum):
    """Types of activities"""
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    COMMENT_ADDED = "comment_added"
    COMMENT_EDITED = "comment_edited"
    COMMENT_DELETED = "comment_deleted"
    ANALYSIS_SHARED = "analysis_shared"
    REPORT_GENERATED = "report_generated"
    SCENARIO_CREATED = "scenario_created"
    ALERT_TRIGGERED = "alert_triggered"


class User:
    """User model"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        full_name: str,
        avatar_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize user
        
        Args:
            user_id: Unique user identifier
            username: Username
            email: Email address
            full_name: Full name
            avatar_url: Avatar image URL
            metadata: Additional metadata
        """
        self.user_id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.avatar_url = avatar_url
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()
        self.last_active = datetime.utcnow().isoformat()
        self.is_online = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'is_online': self.is_online
        }


class Workspace:
    """Workspace model for team collaboration"""
    
    def __init__(
        self,
        workspace_id: str,
        name: str,
        description: str,
        owner_id: str,
        settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize workspace
        
        Args:
            workspace_id: Unique workspace identifier
            name: Workspace name
            description: Workspace description
            owner_id: Owner user ID
            settings: Workspace settings
        """
        self.workspace_id = workspace_id
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.settings = settings or {
            'is_public': False,
            'allow_comments': True,
            'allow_sharing': True,
            'notification_enabled': True
        }
        self.members: Dict[str, UserRole] = {owner_id: UserRole.OWNER}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.shared_resources: List[str] = []
    
    def add_member(self, user_id: str, role: UserRole = UserRole.MEMBER):
        """Add member to workspace"""
        self.members[user_id] = role
        self.updated_at = datetime.utcnow().isoformat()
    
    def remove_member(self, user_id: str):
        """Remove member from workspace"""
        if user_id in self.members and user_id != self.owner_id:
            del self.members[user_id]
            self.updated_at = datetime.utcnow().isoformat()
    
    def update_member_role(self, user_id: str, role: UserRole):
        """Update member role"""
        if user_id in self.members and user_id != self.owner_id:
            self.members[user_id] = role
            self.updated_at = datetime.utcnow().isoformat()
    
    def share_resource(self, resource_id: str):
        """Share a resource in workspace"""
        if resource_id not in self.shared_resources:
            self.shared_resources.append(resource_id)
            self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'workspace_id': self.workspace_id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'settings': self.settings,
            'members': {uid: role.value for uid, role in self.members.items()},
            'member_count': len(self.members),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'shared_resources': self.shared_resources
        }


class Comment:
    """Comment model for annotations"""
    
    def __init__(
        self,
        comment_id: str,
        workspace_id: str,
        resource_id: str,
        resource_type: str,
        author_id: str,
        content: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize comment
        
        Args:
            comment_id: Unique comment identifier
            workspace_id: Workspace ID
            resource_id: Resource being commented on
            resource_type: Type of resource (analysis, report, scenario, etc.)
            author_id: Author user ID
            content: Comment content
            parent_id: Parent comment ID (for replies)
            metadata: Additional metadata (mentions, attachments, etc.)
        """
        self.comment_id = comment_id
        self.workspace_id = workspace_id
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.author_id = author_id
        self.content = content
        self.parent_id = parent_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.is_edited = False
        self.is_deleted = False
        self.reactions: Dict[str, List[str]] = {}  # emoji -> [user_ids]
        self.replies: List[str] = []  # comment_ids
    
    def edit(self, new_content: str):
        """Edit comment content"""
        self.content = new_content
        self.updated_at = datetime.utcnow().isoformat()
        self.is_edited = True
    
    def delete(self):
        """Mark comment as deleted"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_reaction(self, emoji: str, user_id: str):
        """Add reaction to comment"""
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        if user_id not in self.reactions[emoji]:
            self.reactions[emoji].append(user_id)
    
    def remove_reaction(self, emoji: str, user_id: str):
        """Remove reaction from comment"""
        if emoji in self.reactions and user_id in self.reactions[emoji]:
            self.reactions[emoji].remove(user_id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]
    
    def add_reply(self, reply_id: str):
        """Add reply to comment"""
        if reply_id not in self.replies:
            self.replies.append(reply_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'comment_id': self.comment_id,
            'workspace_id': self.workspace_id,
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'author_id': self.author_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'reactions': self.reactions,
            'replies': self.replies,
            'reply_count': len(self.replies)
        }


class Activity:
    """Activity model for activity feed"""
    
    def __init__(
        self,
        activity_id: str,
        workspace_id: str,
        activity_type: ActivityType,
        user_id: str,
        description: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize activity
        
        Args:
            activity_id: Unique activity identifier
            workspace_id: Workspace ID
            activity_type: Type of activity
            user_id: User who performed activity
            description: Activity description
            resource_id: Related resource ID
            resource_type: Type of resource
            metadata: Additional metadata
        """
        self.activity_id = activity_id
        self.workspace_id = workspace_id
        self.activity_type = activity_type
        self.user_id = user_id
        self.description = description
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.is_read: Dict[str, bool] = {}  # user_id -> is_read
    
    def mark_read(self, user_id: str):
        """Mark activity as read by user"""
        self.is_read[user_id] = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'activity_id': self.activity_id,
            'workspace_id': self.workspace_id,
            'activity_type': self.activity_type.value,
            'user_id': self.user_id,
            'description': self.description,
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'is_read': self.is_read
        }


class UserPresence:
    """User presence model for real-time collaboration"""
    
    def __init__(
        self,
        user_id: str,
        workspace_id: str,
        status: str = "online",
        current_page: Optional[str] = None,
        current_resource: Optional[str] = None
    ):
        """
        Initialize user presence
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            status: User status (online, away, busy, offline)
            current_page: Current page/view
            current_resource: Current resource being viewed
        """
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.status = status
        self.current_page = current_page
        self.current_resource = current_resource
        self.last_seen = datetime.utcnow().isoformat()
        self.session_id = str(uuid.uuid4())
    
    def update(
        self,
        status: Optional[str] = None,
        current_page: Optional[str] = None,
        current_resource: Optional[str] = None
    ):
        """Update presence information"""
        if status:
            self.status = status
        if current_page is not None:
            self.current_page = current_page
        if current_resource is not None:
            self.current_resource = current_resource
        self.last_seen = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'workspace_id': self.workspace_id,
            'status': self.status,
            'current_page': self.current_page,
            'current_resource': self.current_resource,
            'last_seen': self.last_seen,
            'session_id': self.session_id
        }


# Made with Bob