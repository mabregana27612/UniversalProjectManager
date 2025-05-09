import os
import json
import datetime
from pathlib import Path
import hashlib

# Import database functions
from utils.database import (
    # User functions
    get_all_users, get_user_by_id, get_user_by_username, create_user, update_user,
    
    # Project functions
    get_all_projects, get_project, create_project, update_project, delete_project,
    
    # Task functions
    get_all_tasks, get_task, get_project_tasks, create_task, update_task, delete_task,
    
    # Team member functions
    get_all_team_members, get_team_member, get_project_team, create_team_member, 
    update_team_member, delete_team_member, get_team_members_by_leader,
    
    # Document functions
    get_all_documents, get_project_documents, create_document, update_document, delete_document,
    
    # Subtask functions
    get_all_subtasks, get_subtask, get_subtasks_by_parent, create_subtask,
    update_subtask, delete_subtask, get_subtasks_by_member,
    
    # Meeting functions
    get_all_meetings, get_meeting, get_project_meetings, create_meeting,
    update_meeting, delete_meeting, get_completed_meetings_for_task
)

# Legacy functions for backward compatibility (now using database)
def ensure_data_dir():
    """Make sure the data directory exists"""
    os.makedirs('data', exist_ok=True)

def save_data(data_type, data):
    """Save data to the database (no longer uses JSON files)"""
    # This function is now a placeholder - all saving is done via specific database functions
    # Called by old code but has no effect as we're using the database
    return True

def load_data(data_type):
    """Load data from the database (no longer uses JSON files)"""
    if data_type == 'users':
        return get_all_users()
    elif data_type == 'projects':
        return get_all_projects()
    elif data_type == 'tasks':
        return get_all_tasks()
    elif data_type == 'team_members':
        return get_all_team_members()
    elif data_type == 'documents':
        return get_all_documents()
    elif data_type == 'subtasks':
        return get_all_subtasks()
    elif data_type == 'meetings':
        return get_all_meetings()
    else:
        # For any unrecognized data type
        print(f"Warning: Unrecognized data type '{data_type}'")
        return []

def initialize_data():
    """Initialize data structures if they don't exist yet"""
    from utils.database import get_db_session, User, create_tables
    
    # Ensure tables are created
    create_tables()
    
    # Check if we have an admin user
    db = get_db_session()
    try:
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                id=1,
                username='admin',
                password_hash='admin',  # In a real app, this would be hashed
                name='System Administrator',
                email='admin@example.com',
                role='admin',
                created_at='2023-01-01'
            )
            db.add(admin_user)
            db.commit()
            print("Created admin user in database")
    except Exception as e:
        print(f"Error initializing admin user: {str(e)}")
    finally:
        db.close()

def get_new_id(data_type):
    """Generate a new ID for a data type (legacy function)"""
    data = load_data(data_type)
    return max([item['id'] for item in data], default=0) + 1

def add_project(project_data):
    """Add a new project"""
    if 'id' not in project_data:
        project_data['id'] = get_new_id('projects')
    
    if 'created_at' not in project_data:
        project_data['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    return create_project(project_data)['id']

def archive_project(project_id):
    """Archive a project by setting is_archived flag"""
    project = get_project(project_id)
    if project:
        project['is_archived'] = True
        update_project(project_id, project)
        return True
    return False

def get_archived_projects():
    """Get all archived projects"""
    projects = get_all_projects()
    return [p for p in projects if p.get('is_archived', False)]

def add_task(task_data):
    """Add a new task"""
    if 'id' not in task_data:
        task_data['id'] = get_new_id('tasks')
    
    return create_task(task_data)['id']

def add_team_member(member_data):
    """Add a new team member"""
    if 'id' not in member_data:
        member_data['id'] = get_new_id('team_members')
    
    return create_team_member(member_data)['id']

def get_project_team_leaders(project_id):
    """Get all team leaders for a project"""
    team = get_project_team(project_id)
    return [member for member in team if member.get('is_team_leader', False)]

def assign_task_to_team(task_id, team_member_ids):
    """Assign a task to team members"""
    task = get_task(task_id)
    if task:
        task['assigned_members'] = team_member_ids
        update_task(task_id, task)
        return True
    return False

def assign_member_to_leader(member_id, leader_id):
    """Assign a team member to report to a leader"""
    member = get_team_member(member_id)
    if member:
        member['reports_to'] = leader_id
        update_team_member(member_id, member)
        return True
    return False

def add_document(document_data):
    """Add a new document"""
    if 'id' not in document_data:
        document_data['id'] = get_new_id('documents')
    
    if 'upload_date' not in document_data:
        document_data['upload_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    return create_document(document_data)['id']

def register_user(user_data):
    """Register a new user"""
    # Check if username already exists
    all_users = get_all_users()
    if any(u['username'] == user_data['username'] for u in all_users):
        return {"success": False, "message": "Username already exists!"}
    
    if 'id' not in user_data:
        user_data['id'] = get_new_id('users')
    
    if 'created_at' not in user_data:
        user_data['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # In a real app, you would hash the password
    # user_data['password_hash'] = hashlib.sha256(user_data['password'].encode()).hexdigest()
    
    create_user(user_data)
    return {"success": True, "message": "User registered successfully!"}

def authenticate_user(username, password):
    """Authenticate a user by username and password"""
    user = get_user_by_username(username)
    
    if user and user['password_hash'] == password:  # In a real app, compare hashed values
        user_data = {
            "user_id": user['id'],
            "user": user,
            "role": user['role'],
            "success": True
        }
        
        # Update last login
        user['last_login'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_user(user['id'], user)
        
        return user_data
    
    return {"success": False, "message": "Invalid username or password!"}

def get_user_by_team_member_id(team_member_id):
    """Get user by associated team member ID"""
    all_users = get_all_users()
    matching_users = [u for u in all_users if u.get('team_member_id') == team_member_id]
    return matching_users[0] if matching_users else None

def can_access_project(user_id, project_id):
    """Check if a user can access a project"""
    user = get_user_by_id(user_id)
    
    # Admin can access all projects
    if user and user['role'] == 'admin':
        return True
    
    # Check if user is associated with a team member in this project
    if user and user.get('team_member_id'):
        team = get_project_team(project_id)
        return any(member['id'] == user['team_member_id'] for member in team)
    
    return False

def can_access_task(user_id, task_id):
    """Check if a user can access a task"""
    user = get_user_by_id(user_id)
    
    # Admin can access all tasks
    if user and user['role'] == 'admin':
        return True
    
    task = get_task(task_id)
    if not task:
        return False
    
    # Check if user is associated with this task
    if user and user.get('team_member_id'):
        if user['team_member_id'] in task.get('assigned_members', []):
            return True
        
        # Check if user is a team leader for someone assigned to this task
        team_member = get_team_member(user['team_member_id'])
        if team_member and team_member.get('is_team_leader', False):
            team = get_team_members_by_leader(team_member['id'])
            team_member_ids = [member['id'] for member in team]
            return any(member_id in task.get('assigned_members', []) for member_id in team_member_ids)
    
    return False

def get_tasks_awaiting_approval(project_id):
    """Get tasks that are awaiting approval"""
    project_tasks = get_project_tasks(project_id)
    return [task for task in project_tasks if 
            task.get('requires_approval', False) and 
            task.get('approval_status') == 'Pending Approval']

def approve_task(task_id, approver_id, comments=None):
    """Approve a task"""
    task = get_task(task_id)
    if task:
        task['approval_status'] = 'Approved'
        task['approved_by'] = approver_id
        task['approval_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if comments:
            task['approval_comments'] = comments
        
        update_task(task_id, task)
        return True
    return False

def reject_task(task_id, reviewer_id, rejection_reason):
    """Reject a task with reason"""
    task = get_task(task_id)
    if task:
        task['approval_status'] = 'Rejected'
        task['reviewed_by'] = reviewer_id
        task['rejection_reason'] = rejection_reason
        task['review_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        update_task(task_id, task)
        return True
    return False

def get_dependent_tasks(task_id):
    """Get tasks that depend on a given task"""
    all_tasks = get_all_tasks()
    return [task for task in all_tasks if 
            task_id in task.get('dependencies', [])]

def analyze_schedule_impact(task_id, new_end_date):
    """Analyze impact on dependent tasks if end date changes"""
    task = get_task(task_id)
    dependent_tasks = get_dependent_tasks(task_id)
    
    if not task or not dependent_tasks:
        return {"impacted_tasks": [], "total_delay_days": 0}
    
    current_end = datetime.datetime.strptime(task['end_date'], '%Y-%m-%d')
    new_end = datetime.datetime.strptime(new_end_date, '%Y-%m-%d')
    
    # If new date is earlier or the same, no impact
    if new_end <= current_end:
        return {"impacted_tasks": [], "total_delay_days": 0}
    
    # Calculate delay in days
    delay_days = (new_end - current_end).days
    
    impacted_tasks = []
    for dep_task in dependent_tasks:
        # Only count tasks that start after this task ends
        dep_start = datetime.datetime.strptime(dep_task['start_date'], '%Y-%m-%d')
        if dep_start >= current_end:
            # Calculate new dates
            new_start = dep_start + datetime.timedelta(days=delay_days)
            dep_end = datetime.datetime.strptime(dep_task['end_date'], '%Y-%m-%d')
            new_end = dep_end + datetime.timedelta(days=delay_days)
            
            impacted_tasks.append({
                "task_id": dep_task['id'],
                "task_name": dep_task['name'],
                "current_start": dep_task['start_date'],
                "current_end": dep_task['end_date'],
                "new_start": new_start.strftime('%Y-%m-%d'),
                "new_end": new_end.strftime('%Y-%m-%d'),
                "delay_days": delay_days
            })
    
    return {
        "impacted_tasks": impacted_tasks,
        "total_delay_days": delay_days
    }

def add_subtask(subtask_data):
    """Add a new subtask"""
    if 'id' not in subtask_data:
        subtask_data['id'] = get_new_id('subtasks')
    
    result = create_subtask(subtask_data)
    
    # Update parent task progress
    update_parent_task_progress(subtask_data['parent_task_id'])
    
    return result['id']

def update_parent_task_progress(parent_task_id):
    """Update parent task progress based on subtask progress"""
    subtasks = get_subtasks_by_parent(parent_task_id)
    if subtasks:
        total_progress = sum(subtask.get('progress', 0) for subtask in subtasks)
        average_progress = total_progress / len(subtasks)
        
        # Update parent task
        parent_task = get_task(parent_task_id)
        if parent_task:
            parent_task['progress'] = int(average_progress)
            update_task(parent_task_id, parent_task)

def submit_subtask_report(subtask_id, report_data):
    """Submit a completion report for a subtask"""
    subtask = get_subtask(subtask_id)
    if not subtask:
        return False
    
    # Update subtask with report
    subtask['completion_report'] = report_data['content']
    subtask['status'] = report_data['status']
    subtask['progress'] = report_data['progress']
    subtask['completion_report_submitted_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subtask['completion_report_submitted_by'] = report_data['submitted_by']
    
    # If report indicates completion and requires approval, set status
    if report_data['progress'] == 100 and subtask.get('requires_approval', False):
        subtask['approval_status'] = 'Pending Approval'
    
    update_subtask(subtask_id, subtask)
    
    # Update parent task progress
    update_parent_task_progress(subtask['parent_task_id'])
    
    return True

def check_task_meeting_requirement(task_id):
    """Check if a task has had a completed team meeting before allowing subtasks"""
    completed_meetings = get_completed_meetings_for_task(task_id)
    return len(completed_meetings) > 0