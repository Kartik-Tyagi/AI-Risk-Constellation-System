"""
Collaboration Service
Manage workspaces, comments, activities, and user presence for team collaboration
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from backend.models.collaboration import (
    Workspace, Comment, Activity, User, UserPresence,
    UserRole, ActivityType
)

logger = logging.getLogger(__name__)


class CollaborationService:
    """Main collaboration service"""
    
    def __init__(self):
        """Initialize collaboration service"""
        self.workspaces: Dict[str, Workspace] = {}
        self.comments: Dict[str, Comment] = {}
        self.activities: Dict[str, Activity] = {}
        self.users: Dict[str, User] = {}
        self.presence: Dict[str, UserPresence] = {}
        
        self.workspace_counter = 0
        self.comment_counter = 0
        self.activity_counter = 0
    
    # Workspace Management
    def create_workspace(
        self,
        name: str,
        description: str,
        owner_id: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Workspace:
        """
        Create a new workspace
        
        Args:
            name: Workspace name
            description: Workspace description
            owner_id: Owner user ID
            settings: Workspace settings
            
        Returns:
            Created workspace
        """
        self.workspace_counter += 1
        workspace_id = f"WS-{datetime.utcnow().strftime('%Y%m%d')}-{self.workspace_counter:04d}"
        
        workspace = Workspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
            settings=settings
        )
        
        self.workspaces[workspace_id] = workspace
        
        # Log activity
        self._log_activity(
            workspace_id=workspace_id,
            activity_type=ActivityType.WORKSPACE_CREATED,
            user_id=owner_id,
            description=f"Created workspace '{name}'"
        )
        
        logger.info(f"Created workspace: {workspace_id}")
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    def list_workspaces(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List workspaces
        
        Args:
            user_id: Filter by user membership
            
        Returns:
            List of workspaces
        """
        workspaces = self.workspaces.values()
        
        if user_id:
            workspaces = [w for w in workspaces if user_id in w.members]
        
        return [w.to_dict() for w in workspaces]
    
    def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Workspace]:
        """Update workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        if name:
            workspace.name = name
        if description:
            workspace.description = description
        if settings:
            workspace.settings.update(settings)
        
        workspace.updated_at = datetime.utcnow().isoformat()
        
        if user_id:
            self._log_activity(
                workspace_id=workspace_id,
                activity_type=ActivityType.WORKSPACE_UPDATED,
                user_id=user_id,
                description=f"Updated workspace settings"
            )
        
        return workspace
    
    def add_workspace_member(
        self,
        workspace_id: str,
        user_id: str,
        role: UserRole = UserRole.MEMBER,
        added_by: Optional[str] = None
    ) -> bool:
        """Add member to workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        workspace.add_member(user_id, role)
        
        if added_by:
            self._log_activity(
                workspace_id=workspace_id,
                activity_type=ActivityType.USER_JOINED,
                user_id=added_by,
                description=f"Added user {user_id} to workspace",
                metadata={'new_user_id': user_id, 'role': role.value}
            )
        
        return True
    
    def remove_workspace_member(
        self,
        workspace_id: str,
        user_id: str,
        removed_by: Optional[str] = None
    ) -> bool:
        """Remove member from workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        workspace.remove_member(user_id)
        
        if removed_by:
            self._log_activity(
                workspace_id=workspace_id,
                activity_type=ActivityType.USER_LEFT,
                user_id=removed_by,
                description=f"Removed user {user_id} from workspace",
                metadata={'removed_user_id': user_id}
            )
        
        return True
    
    # Comment Management
    def add_comment(
        self,
        workspace_id: str,
        resource_id: str,
        resource_type: str,
        author_id: str,
        content: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Comment:
        """
        Add a comment
        
        Args:
            workspace_id: Workspace ID
            resource_id: Resource being commented on
            resource_type: Type of resource
            author_id: Author user ID
            content: Comment content
            parent_id: Parent comment ID (for replies)
            metadata: Additional metadata
            
        Returns:
            Created comment
        """
        self.comment_counter += 1
        comment_id = f"CMT-{datetime.utcnow().strftime('%Y%m%d')}-{self.comment_counter:06d}"
        
        comment = Comment(
            comment_id=comment_id,
            workspace_id=workspace_id,
            resource_id=resource_id,
            resource_type=resource_type,
            author_id=author_id,
            content=content,
            parent_id=parent_id,
            metadata=metadata
        )
        
        self.comments[comment_id] = comment
        
        # If reply, add to parent
        if parent_id and parent_id in self.comments:
            self.comments[parent_id].add_reply(comment_id)
        
        # Log activity
        self._log_activity(
            workspace_id=workspace_id,
            activity_type=ActivityType.COMMENT_ADDED,
            user_id=author_id,
            description=f"Added comment on {resource_type}",
            resource_id=resource_id,
            resource_type=resource_type,
            metadata={'comment_id': comment_id}
        )
        
        logger.info(f"Added comment: {comment_id}")
        return comment
    
    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Get comment by ID"""
        return self.comments.get(comment_id)
    
    def list_comments(
        self,
        workspace_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        author_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List comments with filters
        
        Args:
            workspace_id: Filter by workspace
            resource_id: Filter by resource
            author_id: Filter by author
            parent_id: Filter by parent (None for top-level)
            limit: Maximum number of comments
            
        Returns:
            List of comments
        """
        comments = self.comments.values()
        
        if workspace_id:
            comments = [c for c in comments if c.workspace_id == workspace_id]
        
        if resource_id:
            comments = [c for c in comments if c.resource_id == resource_id]
        
        if author_id:
            comments = [c for c in comments if c.author_id == author_id]
        
        if parent_id is not None:
            comments = [c for c in comments if c.parent_id == parent_id]
        
        # Filter out deleted comments
        comments = [c for c in comments if not c.is_deleted]
        
        # Sort by creation time (newest first)
        comments = sorted(comments, key=lambda x: x.created_at, reverse=True)
        
        return [c.to_dict() for c in comments[:limit]]
    
    def edit_comment(
        self,
        comment_id: str,
        new_content: str,
        user_id: str
    ) -> Optional[Comment]:
        """Edit a comment"""
        comment = self.get_comment(comment_id)
        if not comment or comment.author_id != user_id:
            return None
        
        comment.edit(new_content)
        
        self._log_activity(
            workspace_id=comment.workspace_id,
            activity_type=ActivityType.COMMENT_EDITED,
            user_id=user_id,
            description=f"Edited comment",
            metadata={'comment_id': comment_id}
        )
        
        return comment
    
    def delete_comment(
        self,
        comment_id: str,
        user_id: str
    ) -> bool:
        """Delete a comment"""
        comment = self.get_comment(comment_id)
        if not comment or comment.author_id != user_id:
            return False
        
        comment.delete()
        
        self._log_activity(
            workspace_id=comment.workspace_id,
            activity_type=ActivityType.COMMENT_DELETED,
            user_id=user_id,
            description=f"Deleted comment",
            metadata={'comment_id': comment_id}
        )
        
        return True
    
    def add_reaction(
        self,
        comment_id: str,
        emoji: str,
        user_id: str
    ) -> bool:
        """Add reaction to comment"""
        comment = self.get_comment(comment_id)
        if not comment:
            return False
        
        comment.add_reaction(emoji, user_id)
        return True
    
    def remove_reaction(
        self,
        comment_id: str,
        emoji: str,
        user_id: str
    ) -> bool:
        """Remove reaction from comment"""
        comment = self.get_comment(comment_id)
        if not comment:
            return False
        
        comment.remove_reaction(emoji, user_id)
        return True
    
    # Activity Feed
    def _log_activity(
        self,
        workspace_id: str,
        activity_type: ActivityType,
        user_id: str,
        description: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Activity:
        """Log an activity"""
        self.activity_counter += 1
        activity_id = f"ACT-{datetime.utcnow().strftime('%Y%m%d')}-{self.activity_counter:06d}"
        
        activity = Activity(
            activity_id=activity_id,
            workspace_id=workspace_id,
            activity_type=activity_type,
            user_id=user_id,
            description=description,
            resource_id=resource_id,
            resource_type=resource_type,
            metadata=metadata
        )
        
        self.activities[activity_id] = activity
        return activity
    
    def get_activity_feed(
        self,
        workspace_id: str,
        user_id: Optional[str] = None,
        activity_type: Optional[ActivityType] = None,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get activity feed
        
        Args:
            workspace_id: Workspace ID
            user_id: Filter by user
            activity_type: Filter by activity type
            hours: Time window in hours
            limit: Maximum number of activities
            
        Returns:
            List of activities
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activities = self.activities.values()
        
        # Filter by workspace
        activities = [a for a in activities if a.workspace_id == workspace_id]
        
        # Filter by time
        activities = [
            a for a in activities
            if datetime.fromisoformat(a.timestamp) > cutoff
        ]
        
        # Filter by user
        if user_id:
            activities = [a for a in activities if a.user_id == user_id]
        
        # Filter by type
        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]
        
        # Sort by timestamp (newest first)
        activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)
        
        return [a.to_dict() for a in activities[:limit]]
    
    def mark_activity_read(
        self,
        activity_id: str,
        user_id: str
    ) -> bool:
        """Mark activity as read"""
        activity = self.activities.get(activity_id)
        if not activity:
            return False
        
        activity.mark_read(user_id)
        return True
    
    # User Presence
    def update_presence(
        self,
        user_id: str,
        workspace_id: str,
        status: Optional[str] = None,
        current_page: Optional[str] = None,
        current_resource: Optional[str] = None
    ) -> UserPresence:
        """
        Update user presence
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            status: User status
            current_page: Current page
            current_resource: Current resource
            
        Returns:
            Updated presence
        """
        presence_key = f"{workspace_id}:{user_id}"
        
        if presence_key not in self.presence:
            self.presence[presence_key] = UserPresence(
                user_id=user_id,
                workspace_id=workspace_id,
                status=status or "online"
            )
        
        self.presence[presence_key].update(
            status=status,
            current_page=current_page,
            current_resource=current_resource
        )
        
        return self.presence[presence_key]
    
    def get_workspace_presence(
        self,
        workspace_id: str,
        active_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get active users in workspace
        
        Args:
            workspace_id: Workspace ID
            active_minutes: Consider users active within this many minutes
            
        Returns:
            List of active user presences
        """
        cutoff = datetime.utcnow() - timedelta(minutes=active_minutes)
        presences = []
        
        for key, presence in self.presence.items():
            if presence.workspace_id == workspace_id:
                last_seen = datetime.fromisoformat(presence.last_seen)
                if last_seen > cutoff and presence.status != "offline":
                    presences.append(presence.to_dict())
        
        return presences
    
    def get_user_presence(
        self,
        user_id: str,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific user presence"""
        presence_key = f"{workspace_id}:{user_id}"
        presence = self.presence.get(presence_key)
        return presence.to_dict() if presence else None
    
    # User Management
    def register_user(
        self,
        user_id: str,
        username: str,
        email: str,
        full_name: str,
        avatar_url: Optional[str] = None
    ) -> User:
        """Register a user"""
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url
        )
        
        self.users[user_id] = user
        logger.info(f"Registered user: {user_id}")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_users(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple users"""
        return [
            self.users[uid].to_dict()
            for uid in user_ids
            if uid in self.users
        ]
    
    # Sharing
    def share_resource(
        self,
        workspace_id: str,
        resource_id: str,
        resource_type: str,
        shared_by: str
    ) -> bool:
        """Share a resource in workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        workspace.share_resource(resource_id)
        
        self._log_activity(
            workspace_id=workspace_id,
            activity_type=ActivityType.ANALYSIS_SHARED,
            user_id=shared_by,
            description=f"Shared {resource_type}",
            resource_id=resource_id,
            resource_type=resource_type
        )
        
        return True
    
    def get_shared_resources(
        self,
        workspace_id: str
    ) -> List[str]:
        """Get shared resources in workspace"""
        workspace = self.get_workspace(workspace_id)
        return workspace.shared_resources if workspace else []


# Global collaboration service instance
_collaboration_service = None


def get_collaboration_service() -> CollaborationService:
    """Get or create global collaboration service instance"""
    global _collaboration_service
    if _collaboration_service is None:
        _collaboration_service = CollaborationService()
    return _collaboration_service


# Made with Bob