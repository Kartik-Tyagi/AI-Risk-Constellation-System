/**
 * CollaborationPanel Component
 * Real-time collaboration features including workspaces, comments, activity feed, and user presence
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './CollaborationPanel.css';

const CollaborationPanel = ({ currentUser, currentResource }) => {
  // State management
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [comments, setComments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [activeTab, setActiveTab] = useState('comments'); // comments, activity, members
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Refs for real-time updates
  const presenceInterval = useRef(null);
  const activityInterval = useRef(null);

  // API base URL
  const API_BASE = '/api/collaboration';

  // Fetch workspaces on mount
  useEffect(() => {
    fetchWorkspaces();
  }, [currentUser]);

  // Set up real-time updates when workspace is selected
  useEffect(() => {
    if (selectedWorkspace) {
      fetchComments();
      fetchActivities();
      fetchActiveUsers();
      updatePresence();

      // Set up intervals for real-time updates
      presenceInterval.current = setInterval(updatePresence, 30000); // Every 30s
      activityInterval.current = setInterval(() => {
        fetchActivities();
        fetchActiveUsers();
      }, 10000); // Every 10s

      return () => {
        clearInterval(presenceInterval.current);
        clearInterval(activityInterval.current);
      };
    }
  }, [selectedWorkspace, currentResource]);

  // API Functions
  const fetchWorkspaces = async () => {
    try {
      const response = await fetch(`${API_BASE}/workspaces?user_id=${currentUser.id}`);
      const data = await response.json();
      setWorkspaces(data.workspaces || []);
      
      // Auto-select first workspace if available
      if (data.workspaces && data.workspaces.length > 0 && !selectedWorkspace) {
        setSelectedWorkspace(data.workspaces[0]);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
      setError('Failed to load workspaces');
    }
  };

  const fetchComments = async () => {
    if (!selectedWorkspace || !currentResource) return;
    
    try {
      const response = await fetch(
        `${API_BASE}/comments?workspace_id=${selectedWorkspace.id}&resource_id=${currentResource.id}`
      );
      const data = await response.json();
      setComments(data.comments || []);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    }
  };

  const fetchActivities = async () => {
    if (!selectedWorkspace) return;
    
    try {
      const response = await fetch(
        `${API_BASE}/activity?workspace_id=${selectedWorkspace.id}&hours=24&limit=50`
      );
      const data = await response.json();
      setActivities(data.activities || []);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
    }
  };

  const fetchActiveUsers = async () => {
    if (!selectedWorkspace) return;
    
    try {
      const response = await fetch(
        `${API_BASE}/presence?workspace_id=${selectedWorkspace.id}&active_minutes=5`
      );
      const data = await response.json();
      setActiveUsers(data.presences || []);
    } catch (err) {
      console.error('Failed to fetch active users:', err);
    }
  };

  const updatePresence = async () => {
    if (!selectedWorkspace || !currentUser) return;
    
    try {
      await fetch(`${API_BASE}/presence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.id,
          workspace_id: selectedWorkspace.id,
          status: 'active',
          current_resource: currentResource?.id,
          current_page: window.location.pathname
        })
      });
    } catch (err) {
      console.error('Failed to update presence:', err);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedWorkspace || !currentResource) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: selectedWorkspace.id,
          resource_id: currentResource.id,
          resource_type: currentResource.type || 'analysis',
          author_id: currentUser.id,
          content: newComment,
          parent_id: replyTo?.id
        })
      });
      
      if (response.ok) {
        setNewComment('');
        setReplyTo(null);
        await fetchComments();
      }
    } catch (err) {
      console.error('Failed to add comment:', err);
      setError('Failed to add comment');
    } finally {
      setLoading(false);
    }
  };

  const handleReaction = async (commentId, emoji) => {
    try {
      await fetch(`${API_BASE}/comments/${commentId}/reactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          emoji,
          user_id: currentUser.id
        })
      });
      await fetchComments();
    } catch (err) {
      console.error('Failed to add reaction:', err);
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;
    
    try {
      await fetch(`${API_BASE}/comments/${commentId}?user_id=${currentUser.id}`, {
        method: 'DELETE'
      });
      await fetchComments();
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  const handleShareResource = async () => {
    if (!selectedWorkspace || !currentResource) return;
    
    try {
      await fetch(`${API_BASE}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: selectedWorkspace.id,
          resource_id: currentResource.id,
          resource_type: currentResource.type || 'analysis',
          shared_by: currentUser.id
        })
      });
      alert('Resource shared successfully!');
    } catch (err) {
      console.error('Failed to share resource:', err);
      setError('Failed to share resource');
    }
  };

  // Helper functions
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const getActivityIcon = (type) => {
    const icons = {
      comment: '💬',
      share: '🔗',
      edit: '✏️',
      delete: '🗑️',
      member_added: '👤',
      member_removed: '👋',
      workspace_created: '🆕',
      workspace_updated: '🔄'
    };
    return icons[type] || '📌';
  };

  const organizeComments = (comments) => {
    // Organize comments into threads
    const commentMap = {};
    const rootComments = [];
    
    comments.forEach(comment => {
      commentMap[comment.id] = { ...comment, replies: [] };
    });
    
    comments.forEach(comment => {
      if (comment.parent_id && commentMap[comment.parent_id]) {
        commentMap[comment.parent_id].replies.push(commentMap[comment.id]);
      } else {
        rootComments.push(commentMap[comment.id]);
      }
    });
    
    return rootComments;
  };

  // Render functions
  const renderComment = (comment, depth = 0) => (
    <div key={comment.id} className={`comment depth-${depth}`}>
      <div className="comment-header">
        <img 
          src={comment.author?.avatar_url || '/default-avatar.png'} 
          alt={comment.author?.username}
          className="comment-avatar"
        />
        <div className="comment-meta">
          <span className="comment-author">{comment.author?.username || 'Unknown'}</span>
          <span className="comment-time">{formatTimestamp(comment.created_at)}</span>
        </div>
        {comment.author?.id === currentUser.id && (
          <button 
            className="comment-delete"
            onClick={() => handleDeleteComment(comment.id)}
            title="Delete comment"
          >
            ×
          </button>
        )}
      </div>
      
      <div className="comment-content">{comment.content}</div>
      
      <div className="comment-actions">
        <button onClick={() => setReplyTo(comment)}>Reply</button>
        {['👍', '❤️', '🎉', '🤔'].map(emoji => (
          <button 
            key={emoji}
            className="reaction-btn"
            onClick={() => handleReaction(comment.id, emoji)}
          >
            {emoji} {comment.reactions?.[emoji]?.length || 0}
          </button>
        ))}
      </div>
      
      {comment.replies && comment.replies.length > 0 && (
        <div className="comment-replies">
          {comment.replies.map(reply => renderComment(reply, depth + 1))}
        </div>
      )}
    </div>
  );

  const renderCommentsTab = () => {
    const threadedComments = organizeComments(comments);
    
    return (
      <div className="comments-tab">
        <div className="comment-input-section">
          {replyTo && (
            <div className="reply-indicator">
              Replying to {replyTo.author?.username}
              <button onClick={() => setReplyTo(null)}>×</button>
            </div>
          )}
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={replyTo ? "Write a reply..." : "Add a comment..."}
            className="comment-input"
            rows="3"
          />
          <button 
            onClick={handleAddComment}
            disabled={!newComment.trim() || loading}
            className="btn-primary"
          >
            {loading ? 'Posting...' : replyTo ? 'Reply' : 'Comment'}
          </button>
        </div>
        
        <div className="comments-list">
          {threadedComments.length === 0 ? (
            <div className="empty-state">No comments yet. Be the first to comment!</div>
          ) : (
            threadedComments.map(comment => renderComment(comment))
          )}
        </div>
      </div>
    );
  };

  const renderActivityTab = () => (
    <div className="activity-tab">
      <div className="activity-list">
        {activities.length === 0 ? (
          <div className="empty-state">No recent activity</div>
        ) : (
          activities.map(activity => (
            <div key={activity.id} className="activity-item">
              <span className="activity-icon">{getActivityIcon(activity.type)}</span>
              <div className="activity-content">
                <div className="activity-description">{activity.description}</div>
                <div className="activity-time">{formatTimestamp(activity.timestamp)}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderMembersTab = () => (
    <div className="members-tab">
      <div className="active-users-section">
        <h4>Active Now ({activeUsers.length})</h4>
        <div className="active-users-list">
          {activeUsers.map(presence => (
            <div key={presence.user_id} className="active-user">
              <div className="user-avatar-container">
                <img 
                  src={presence.user?.avatar_url || '/default-avatar.png'} 
                  alt={presence.user?.username}
                  className="user-avatar"
                />
                <span className="online-indicator"></span>
              </div>
              <div className="user-info">
                <div className="user-name">{presence.user?.username || 'Unknown'}</div>
                <div className="user-status">{presence.status || 'active'}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="all-members-section">
        <h4>All Members ({selectedWorkspace?.members?.length || 0})</h4>
        <div className="members-list">
          {selectedWorkspace?.members?.map(member => (
            <div key={member.user_id} className="member-item">
              <img 
                src={member.user?.avatar_url || '/default-avatar.png'} 
                alt={member.user?.username}
                className="member-avatar"
              />
              <div className="member-info">
                <div className="member-name">{member.user?.username || 'Unknown'}</div>
                <div className="member-role">{member.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Main render
  return (
    <div className="collaboration-panel">
      <div className="panel-header">
        <h3>Collaboration</h3>
        <button 
          onClick={handleShareResource}
          className="btn-share"
          disabled={!currentResource}
          title="Share current resource"
        >
          🔗 Share
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="workspace-selector">
        <select 
          value={selectedWorkspace?.id || ''}
          onChange={(e) => {
            const workspace = workspaces.find(w => w.id === e.target.value);
            setSelectedWorkspace(workspace);
          }}
          className="workspace-select"
        >
          <option value="">Select Workspace</option>
          {workspaces.map(workspace => (
            <option key={workspace.id} value={workspace.id}>
              {workspace.name}
            </option>
          ))}
        </select>
      </div>

      {selectedWorkspace && (
        <>
          <div className="tab-navigation">
            <button 
              className={activeTab === 'comments' ? 'active' : ''}
              onClick={() => setActiveTab('comments')}
            >
              💬 Comments ({comments.length})
            </button>
            <button 
              className={activeTab === 'activity' ? 'active' : ''}
              onClick={() => setActiveTab('activity')}
            >
              📊 Activity ({activities.length})
            </button>
            <button 
              className={activeTab === 'members' ? 'active' : ''}
              onClick={() => setActiveTab('members')}
            >
              👥 Members ({selectedWorkspace.members?.length || 0})
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'comments' && renderCommentsTab()}
            {activeTab === 'activity' && renderActivityTab()}
            {activeTab === 'members' && renderMembersTab()}
          </div>
        </>
      )}

      {!selectedWorkspace && (
        <div className="empty-state">
          Select a workspace to start collaborating
        </div>
      )}
    </div>
  );
};

export default CollaborationPanel;

// Made with Bob
