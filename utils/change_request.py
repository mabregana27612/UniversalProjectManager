"""
Module for handling change requests for tasks and subtasks
"""

import datetime
import json
from sqlalchemy import or_
from utils.database import (
    get_db_session, ChangeRequest, 
    get_task, get_subtask, get_team_member, get_user_by_id,
    update_task, update_subtask, model_to_dict
)

def create_change_request(item_type, item_id, user_id, proposed_changes, requires_meeting=False, change_reason=None, impact_analysis=None):
    """
    Create a new change request.
    
    Args:
        item_type: Either 'task' or 'subtask'
        item_id: The ID of the task or subtask
        user_id: The ID of the user creating the request
        proposed_changes: A dictionary containing the proposed changes
        requires_meeting: Whether this change requires a team meeting
        change_reason: Reason for requesting the change
        impact_analysis: Analysis of impact and risks
        
    Returns:
        The ID of the created change request or None if failed
    """
    db = get_db_session()
    
    try:
        # Get current task or subtask data
        current_data = {}
        affected_members = []
        
        if item_type == 'task':
            task = get_task(item_id)
            if not task:
                return None
            
            current_data = dict(task)
            
            # Get affected team members
            if 'assigned_members' in task and task['assigned_members']:
                affected_members = task['assigned_members']
            
            # Update task to show it has pending changes
            task_obj = db.query(Task).filter_by(id=item_id).first()
            if task_obj:
                task_obj.has_pending_changes = True
                db.commit()
        
        elif item_type == 'subtask':
            subtask = get_subtask(item_id)
            if not subtask:
                return None
            
            current_data = dict(subtask)
            
            # Get affected team members
            if 'assigned_members' in subtask and subtask['assigned_members']:
                affected_members = subtask['assigned_members']
            
            # Update subtask to show it has pending changes
            subtask_obj = db.query(Subtask).filter_by(id=item_id).first()
            if subtask_obj:
                subtask_obj.has_pending_changes = True
                db.commit()
        
        else:
            return None
        
        # Create change request record
        change_request = ChangeRequest(
            task_id=item_id if item_type == 'task' else None,
            subtask_id=item_id if item_type == 'subtask' else None,
            requested_by=user_id,
            requested_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="Pending",
            current_data=current_data,
            proposed_changes=proposed_changes,
            change_reason=change_reason,
            impact_analysis=impact_analysis,
            requires_meeting=requires_meeting,
            affected_members=affected_members
        )
        
        db.add(change_request)
        db.commit()
        
        # Notify affected team members
        if affected_members:
            notify_affected_members(affected_members, change_request.id)
        
        return change_request.id
    
    except Exception as e:
        print(f"Error creating change request: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def get_change_requests(item_type=None, item_id=None, status=None):
    """
    Get change requests with optional filters.
    
    Args:
        item_type: Optional filter by 'task' or 'subtask'
        item_id: Optional filter by specific item ID
        status: Optional filter by status (Pending, Approved, Rejected)
        
    Returns:
        List of change requests matching the filters
    """
    db = get_db_session()
    
    try:
        query = db.query(ChangeRequest)
        
        if item_type == 'task':
            query = query.filter(ChangeRequest.task_id != None)
            if item_id:
                query = query.filter(ChangeRequest.task_id == item_id)
        
        elif item_type == 'subtask':
            query = query.filter(ChangeRequest.subtask_id != None)
            if item_id:
                query = query.filter(ChangeRequest.subtask_id == item_id)
        
        elif item_id:
            query = query.filter(or_(
                ChangeRequest.task_id == item_id,
                ChangeRequest.subtask_id == item_id
            ))
        
        if status:
            query = query.filter(ChangeRequest.status == status)
        
        requests = query.all()
        return [model_to_dict(request) for request in requests]
    
    except Exception as e:
        print(f"Error getting change requests: {e}")
        return []
    finally:
        db.close()

def get_change_request(request_id):
    """Get a specific change request by ID"""
    db = get_db_session()
    
    try:
        request = db.query(ChangeRequest).filter_by(id=request_id).first()
        if request:
            return model_to_dict(request)
        return None
    
    except Exception as e:
        print(f"Error getting change request: {e}")
        return None
    finally:
        db.close()

def approve_change_request(request_id, user_id, comments=None):
    """
    Approve a change request and apply the changes.
    
    Args:
        request_id: The ID of the change request
        user_id: The ID of the approving user
        comments: Optional approval comments
    
    Returns:
        Boolean indicating success or failure
    """
    db = get_db_session()
    
    try:
        request = db.query(ChangeRequest).filter_by(id=request_id).first()
        if not request or request.status != "Pending":
            return False
        
        # Update change request status
        request.status = "Approved"
        request.reviewed_by = user_id
        request.review_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request.review_comments = comments
        
        # Apply changes
        if request.task_id:
            task = get_task(request.task_id)
            if not task:
                return False
            
            # Apply changes to task
            update_task(request.task_id, request.proposed_changes)
            
            # Clear the has_pending_changes flag
            task_obj = db.query(Task).filter_by(id=request.task_id).first()
            if task_obj:
                task_obj.has_pending_changes = False
        
        elif request.subtask_id:
            subtask = get_subtask(request.subtask_id)
            if not subtask:
                return False
            
            # Apply changes to subtask
            update_subtask(request.subtask_id, request.proposed_changes)
            
            # Clear the has_pending_changes flag
            subtask_obj = db.query(Subtask).filter_by(id=request.subtask_id).first()
            if subtask_obj:
                subtask_obj.has_pending_changes = False
        
        db.commit()
        
        # Notify about the approval
        notify_request_status_change(request_id, "approved")
        
        return True
    
    except Exception as e:
        print(f"Error approving change request: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def reject_change_request(request_id, user_id, comments=None):
    """
    Reject a change request.
    
    Args:
        request_id: The ID of the change request
        user_id: The ID of the rejecting user
        comments: Optional rejection comments
    
    Returns:
        Boolean indicating success or failure
    """
    db = get_db_session()
    
    try:
        request = db.query(ChangeRequest).filter_by(id=request_id).first()
        if not request or request.status != "Pending":
            return False
        
        # Update change request status
        request.status = "Rejected"
        request.reviewed_by = user_id
        request.review_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request.review_comments = comments
        
        # Clear the has_pending_changes flag
        if request.task_id:
            task_obj = db.query(Task).filter_by(id=request.task_id).first()
            if task_obj:
                task_obj.has_pending_changes = False
        
        elif request.subtask_id:
            subtask_obj = db.query(Subtask).filter_by(id=request.subtask_id).first()
            if subtask_obj:
                subtask_obj.has_pending_changes = False
        
        db.commit()
        
        # Notify about the rejection
        notify_request_status_change(request_id, "rejected")
        
        return True
    
    except Exception as e:
        print(f"Error rejecting change request: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_user_change_requests(user_id):
    """Get all change requests created by or affecting a user"""
    db = get_db_session()
    
    try:
        # Get team member ID for this user
        user = get_user_by_id(user_id)
        team_member_id = user.get('team_member_id') if user else None
        
        # Get change requests created by this user
        created_by_user = db.query(ChangeRequest).filter(ChangeRequest.requested_by == user_id).all()
        
        # Get change requests affecting this user
        affecting_user = []
        if team_member_id:
            affecting_user = db.query(ChangeRequest).filter(
                ChangeRequest.affected_members.contains([team_member_id])
            ).all()
        
        # Combine and remove duplicates
        all_requests = set(created_by_user + affecting_user)
        return [model_to_dict(request) for request in all_requests]
    
    except Exception as e:
        print(f"Error getting user change requests: {e}")
        return []
    finally:
        db.close()

def notify_affected_members(member_ids, request_id):
    """
    Notify team members affected by a change request.
    This is a placeholder for future implementation with actual notifications.
    
    Args:
        member_ids: List of team member IDs to notify
        request_id: The ID of the change request
    """
    # Placeholder for future notification system
    # For now, just print to console
    print(f"Notifying team members {member_ids} about change request {request_id}")
    
    # In a future implementation, this could send emails, SMS, or in-app notifications
    # Depending on the notification preferences of each team member
    pass

def notify_request_status_change(request_id, status):
    """
    Notify relevant parties about a change request status update.
    
    Args:
        request_id: The ID of the change request
        status: The new status (approved, rejected)
    """
    # Placeholder for future notification system
    request = get_change_request(request_id)
    if not request:
        return
    
    # Get the user who requested the change
    requester_id = request.get('requested_by')
    if not requester_id:
        return
    
    # Get affected team members
    affected_members = request.get('affected_members', [])
    
    # Print to console for now
    print(f"Change request {request_id} has been {status}")
    print(f"Notifying requester {requester_id} and affected members {affected_members}")
    
    # In a future implementation, this could send emails, SMS, or in-app notifications
    pass

# Import these at the end to avoid circular imports
from utils.database import Task, Subtask