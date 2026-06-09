"""
Collaboration API Routes
Endpoints for workspaces, comments, activities, and user presence
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel, Field
except ImportError:
    # Placeholder for when FastAPI is not installed
    class APIRouter:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def put(self, *args, **kwargs): return lambda f: f
        def delete(self, *args, **kwargs): return lambda f: f
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail): pass
    
    def Query(**kwargs): return None
    
    class BaseModel: pass
    class Field:
        def __init__(self, *args, **kwargs): pass

from backend.services.collaboration_service import get_collaboration_service
from backend.models.collaboration import UserRole, ActivityType

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# Request/Response Models
class WorkspaceCreateRequest(BaseModel):
    """Request to create workspace"""
    name: str
    description: str
    owner_id: str
    settings: Optional[Dict[str, Any]] = None


class WorkspaceUpdateRequest(BaseModel):
    """Request to update workspace"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class MemberAddRequest(BaseModel):
    """Request to add member"""
    user_id: str
    role: str = "member"
    added_by: str


class CommentCreateRequest(BaseModel):
    """Request to create comment"""
    workspace_id: str
    resource_id: str
    resource_type: str
    author_id: str
    content: str
    parent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CommentEditRequest(BaseModel):
    """Request to edit comment"""
    new_content: str
    user_id: str


class ReactionRequest(BaseModel):
    """Request to add/remove reaction"""
    emoji: str
    user_id: str


class PresenceUpdateRequest(BaseModel):
    """Request to update presence"""
    user_id: str
    workspace_id: str
    status: Optional[str] = None
    current_page: Optional[str] = None
    current_resource: Optional[str] = None


class UserRegisterRequest(BaseModel):
    """Request to register user"""
    user_id: str
    username: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None


class ShareResourceRequest(BaseModel):
    """Request to share resource"""
    workspace_id: str
    resource_id: str
    resource_type: str
    shared_by: str


# Workspace Endpoints
@router.post("/workspaces")
async def create_workspace(request: WorkspaceCreateRequest):
    """Create a new workspace"""
    try:
        service = get_collaboration_service()
        
        workspace = service.create_workspace(
            name=request.name,
            description=request.description,
            owner_id=request.owner_id,
            settings=request.settings
        )
        
        return {
            'workspace': workspace.to_dict(),
            'message': 'Workspace created successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")


@router.get("/workspaces")
async def list_workspaces(user_id: Optional[str] = Query(default=None)):
    """List workspaces"""
    try:
        service = get_collaboration_service()
        workspaces = service.list_workspaces(user_id=user_id)
        
        return {
            'workspaces': workspaces,
            'total': len(workspaces)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workspaces: {str(e)}")


@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace details"""
    try:
        service = get_collaboration_service()
        workspace = service.get_workspace(workspace_id)
        
        if not workspace:
            raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
        
        return workspace.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace: {str(e)}")


@router.put("/workspaces/{workspace_id}")
async def update_workspace(workspace_id: str, request: WorkspaceUpdateRequest):
    """Update workspace"""
    try:
        service = get_collaboration_service()
        
        workspace = service.update_workspace(
            workspace_id=workspace_id,
            name=request.name,
            description=request.description,
            settings=request.settings
        )
        
        if not workspace:
            raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
        
        return {
            'workspace': workspace.to_dict(),
            'message': 'Workspace updated successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workspace: {str(e)}")


@router.post("/workspaces/{workspace_id}/members")
async def add_member(workspace_id: str, request: MemberAddRequest):
    """Add member to workspace"""
    try:
        service = get_collaboration_service()
        
        # Parse role
        try:
            role = UserRole[request.role.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        success = service.add_workspace_member(
            workspace_id=workspace_id,
            user_id=request.user_id,
            role=role,
            added_by=request.added_by
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
        
        return {
            'message': f'User {request.user_id} added to workspace',
            'role': role.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")


@router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_member(workspace_id: str, user_id: str, removed_by: str = Query(...)):
    """Remove member from workspace"""
    try:
        service = get_collaboration_service()
        
        success = service.remove_workspace_member(
            workspace_id=workspace_id,
            user_id=user_id,
            removed_by=removed_by
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
        
        return {'message': f'User {user_id} removed from workspace'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")


# Comment Endpoints
@router.post("/comments")
async def add_comment(request: CommentCreateRequest):
    """Add a comment"""
    try:
        service = get_collaboration_service()
        
        comment = service.add_comment(
            workspace_id=request.workspace_id,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            author_id=request.author_id,
            content=request.content,
            parent_id=request.parent_id,
            metadata=request.metadata
        )
        
        return {
            'comment': comment.to_dict(),
            'message': 'Comment added successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")


@router.get("/comments")
async def list_comments(
    workspace_id: Optional[str] = Query(default=None),
    resource_id: Optional[str] = Query(default=None),
    author_id: Optional[str] = Query(default=None),
    parent_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500)
):
    """List comments"""
    try:
        service = get_collaboration_service()
        
        comments = service.list_comments(
            workspace_id=workspace_id,
            resource_id=resource_id,
            author_id=author_id,
            parent_id=parent_id,
            limit=limit
        )
        
        return {
            'comments': comments,
            'total': len(comments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list comments: {str(e)}")


@router.get("/comments/{comment_id}")
async def get_comment(comment_id: str):
    """Get comment details"""
    try:
        service = get_collaboration_service()
        comment = service.get_comment(comment_id)
        
        if not comment:
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
        
        return comment.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comment: {str(e)}")


@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: str, request: CommentEditRequest):
    """Edit a comment"""
    try:
        service = get_collaboration_service()
        
        comment = service.edit_comment(
            comment_id=comment_id,
            new_content=request.new_content,
            user_id=request.user_id
        )
        
        if not comment:
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found or unauthorized")
        
        return {
            'comment': comment.to_dict(),
            'message': 'Comment updated successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to edit comment: {str(e)}")


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Query(...)):
    """Delete a comment"""
    try:
        service = get_collaboration_service()
        
        success = service.delete_comment(comment_id=comment_id, user_id=user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found or unauthorized")
        
        return {'message': 'Comment deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete comment: {str(e)}")


@router.post("/comments/{comment_id}/reactions")
async def add_reaction(comment_id: str, request: ReactionRequest):
    """Add reaction to comment"""
    try:
        service = get_collaboration_service()
        
        success = service.add_reaction(
            comment_id=comment_id,
            emoji=request.emoji,
            user_id=request.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
        
        return {'message': 'Reaction added successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add reaction: {str(e)}")


@router.delete("/comments/{comment_id}/reactions")
async def remove_reaction(comment_id: str, request: ReactionRequest):
    """Remove reaction from comment"""
    try:
        service = get_collaboration_service()
        
        success = service.remove_reaction(
            comment_id=comment_id,
            emoji=request.emoji,
            user_id=request.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
        
        return {'message': 'Reaction removed successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove reaction: {str(e)}")


# Activity Feed Endpoints
@router.get("/activity")
async def get_activity_feed(
    workspace_id: str = Query(...),
    user_id: Optional[str] = Query(default=None),
    activity_type: Optional[str] = Query(default=None),
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=50, le=200)
):
    """Get activity feed"""
    try:
        service = get_collaboration_service()
        
        # Parse activity type
        act_type = None
        if activity_type:
            try:
                act_type = ActivityType[activity_type.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid activity type: {activity_type}")
        
        activities = service.get_activity_feed(
            workspace_id=workspace_id,
            user_id=user_id,
            activity_type=act_type,
            hours=hours,
            limit=limit
        )
        
        return {
            'activities': activities,
            'total': len(activities)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity feed: {str(e)}")


@router.post("/activity/{activity_id}/read")
async def mark_activity_read(activity_id: str, user_id: str = Query(...)):
    """Mark activity as read"""
    try:
        service = get_collaboration_service()
        
        success = service.mark_activity_read(activity_id=activity_id, user_id=user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
        
        return {'message': 'Activity marked as read'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark activity as read: {str(e)}")


# Presence Endpoints
@router.post("/presence")
async def update_presence(request: PresenceUpdateRequest):
    """Update user presence"""
    try:
        service = get_collaboration_service()
        
        presence = service.update_presence(
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            status=request.status,
            current_page=request.current_page,
            current_resource=request.current_resource
        )
        
        return {
            'presence': presence.to_dict(),
            'message': 'Presence updated successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update presence: {str(e)}")


@router.get("/presence")
async def get_workspace_presence(
    workspace_id: str = Query(...),
    active_minutes: int = Query(default=5, le=60)
):
    """Get active users in workspace"""
    try:
        service = get_collaboration_service()
        
        presences = service.get_workspace_presence(
            workspace_id=workspace_id,
            active_minutes=active_minutes
        )
        
        return {
            'presences': presences,
            'total': len(presences)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace presence: {str(e)}")


@router.get("/presence/{user_id}")
async def get_user_presence(user_id: str, workspace_id: str = Query(...)):
    """Get user presence"""
    try:
        service = get_collaboration_service()
        
        presence = service.get_user_presence(user_id=user_id, workspace_id=workspace_id)
        
        if not presence:
            raise HTTPException(status_code=404, detail=f"Presence not found for user {user_id}")
        
        return presence
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user presence: {str(e)}")


# User Endpoints
@router.post("/users")
async def register_user(request: UserRegisterRequest):
    """Register a user"""
    try:
        service = get_collaboration_service()
        
        user = service.register_user(
            user_id=request.user_id,
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            avatar_url=request.avatar_url
        )
        
        return {
            'user': user.to_dict(),
            'message': 'User registered successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user details"""
    try:
        service = get_collaboration_service()
        user = service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return user.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.post("/users/batch")
async def get_users_batch(user_ids: List[str]):
    """Get multiple users"""
    try:
        service = get_collaboration_service()
        users = service.get_users(user_ids)
        
        return {
            'users': users,
            'total': len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")


# Sharing Endpoints
@router.post("/share")
async def share_resource(request: ShareResourceRequest):
    """Share a resource in workspace"""
    try:
        service = get_collaboration_service()
        
        success = service.share_resource(
            workspace_id=request.workspace_id,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            shared_by=request.shared_by
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Workspace {request.workspace_id} not found")
        
        return {'message': 'Resource shared successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share resource: {str(e)}")


@router.get("/workspaces/{workspace_id}/shared")
async def get_shared_resources(workspace_id: str):
    """Get shared resources in workspace"""
    try:
        service = get_collaboration_service()
        
        resources = service.get_shared_resources(workspace_id=workspace_id)
        
        return {
            'resources': resources,
            'total': len(resources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shared resources: {str(e)}")


# Made with Bob