"""
Script to clear the database and re-populate it from JSON data.
This ensures all JSON data is properly migrated to the PostgreSQL database.
"""

import os
import json
import datetime
from sqlalchemy import delete
from utils.database import (
    get_db_session, create_tables, User, Project, Task,
    TeamMember, Document, Subtask, Meeting
)

DATA_DIR = "data"

def load_json_data(data_type):
    """Load data from a JSON file"""
    try:
        filepath = os.path.join(DATA_DIR, f"{data_type}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        return []
    except Exception as e:
        print(f"Error loading {data_type}.json: {str(e)}")
        return []

def clear_database():
    """Clear all data from the database"""
    db = get_db_session()
    try:
        # Delete in order to respect foreign keys
        db.query(Subtask).delete()
        db.query(Meeting).delete()
        db.query(Document).delete()
        db.query(Task).delete()
        db.query(TeamMember).delete()
        db.query(Project).delete()
        # Keep users table intact to preserve login credentials
        db.commit()
        print("Database cleared successfully (kept users for login)")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {str(e)}")
    finally:
        db.close()

def populate_database():
    """Populate the database with data from JSON files"""
    # Users
    user_data = load_json_data('users')
    db = get_db_session()
    try:
        # Only add users if none exist (to preserve existing logins)
        existing_users = db.query(User).count()
        if existing_users == 0 and user_data:
            for user in user_data:
                new_user = User(
                    id=user['id'],
                    username=user['username'],
                    password_hash=user['password_hash'],
                    name=user.get('name', user.get('full_name', '')),
                    email=user.get('email', ''),
                    role=user.get('role', 'team_member'),
                    created_at=user.get('created_at', datetime.datetime.now().strftime('%Y-%m-%d')),
                    last_login=user.get('last_login', None),
                    team_member_id=user.get('team_member_id', None)
                )
                db.add(new_user)
            db.commit()
            print(f"Added {len(user_data)} users to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding users: {str(e)}")
    finally:
        db.close()
    
    # Projects
    project_data = load_json_data('projects')
    db = get_db_session()
    try:
        for project in project_data:
            new_project = Project(
                id=project['id'],
                name=project['name'],
                description=project['description'],
                type=project['type'],
                start_date=project['start_date'],
                end_date=project['end_date'],
                budget=project['budget'],
                status=project['status'],
                created_at=project.get('created_at', datetime.datetime.now().strftime('%Y-%m-%d')),
                created_by=project.get('created_by', None),
                is_archived=project.get('is_archived', False)
            )
            db.add(new_project)
        db.commit()
        print(f"Added {len(project_data)} projects to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding projects: {str(e)}")
    finally:
        db.close()
    
    # Team Members
    team_member_data = load_json_data('team_members')
    db = get_db_session()
    try:
        for member in team_member_data:
            new_member = TeamMember(
                id=member['id'],
                project_id=member['project_id'],
                name=member['name'],
                role=member['role'],
                contact_email=member.get('contact_email', None),
                contact_phone=member.get('contact_phone', None),
                is_team_leader=member.get('is_team_leader', False),
                reports_to=member.get('reports_to', None)
            )
            db.add(new_member)
        db.commit()
        print(f"Added {len(team_member_data)} team members to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding team members: {str(e)}")
    finally:
        db.close()
    
    # Tasks
    task_data = load_json_data('tasks')
    db = get_db_session()
    try:
        for task in task_data:
            new_task = Task(
                id=task['id'],
                project_id=task['project_id'],
                name=task['name'],
                description=task['description'],
                start_date=task['start_date'],
                end_date=task['end_date'],
                status=task['status'],
                priority=task['priority'],
                progress=task.get('progress', 0),
                assigned_members=task.get('assigned_members', []),
                dependencies=task.get('dependencies', []),
                requires_approval=task.get('requires_approval', False),
                approval_status=task.get('approval_status', None),
                approved_by=task.get('approved_by', None),
                approval_date=task.get('approval_date', None),
                rejection_reason=task.get('rejection_reason', None)
            )
            db.add(new_task)
        db.commit()
        print(f"Added {len(task_data)} tasks to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding tasks: {str(e)}")
    finally:
        db.close()
    
    # Documents
    document_data = load_json_data('documents')
    db = get_db_session()
    try:
        for document in document_data:
            new_document = Document(
                id=document['id'],
                project_id=document['project_id'],
                name=document['name'],
                file_type=document['file_type'],
                description=document.get('description', None),
                file_path=document['file_path'],
                uploaded_by=document.get('uploaded_by', None),
                upload_date=document['upload_date']
            )
            db.add(new_document)
        db.commit()
        print(f"Added {len(document_data)} documents to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding documents: {str(e)}")
    finally:
        db.close()
    
    # Subtasks
    subtask_data = load_json_data('subtasks')
    db = get_db_session()
    try:
        for subtask in subtask_data:
            new_subtask = Subtask(
                id=subtask['id'],
                parent_task_id=subtask['parent_task_id'],
                name=subtask['name'],
                description=subtask['description'],
                start_date=subtask['start_date'],
                end_date=subtask['end_date'],
                status=subtask['status'],
                progress=subtask.get('progress', 0),
                requires_approval=subtask.get('requires_approval', True),
                assigned_members=subtask.get('assigned_members', []),
                created_by=subtask.get('created_by', None),
                approval_status=subtask.get('approval_status', None),
                approved_by=subtask.get('approved_by', None),
                approval_date=subtask.get('approval_date', None),
                approval_comments=subtask.get('approval_comments', None),
                completion_report=subtask.get('completion_report', None),
                completion_report_submitted_at=subtask.get('completion_report_submitted_at', None),
                completion_report_submitted_by=subtask.get('completion_report_submitted_by', None)
            )
            db.add(new_subtask)
        db.commit()
        print(f"Added {len(subtask_data)} subtasks to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding subtasks: {str(e)}")
    finally:
        db.close()
    
    # Meetings
    meeting_data = load_json_data('meetings')
    db = get_db_session()
    try:
        for meeting in meeting_data:
            new_meeting = Meeting(
                id=meeting['id'],
                project_id=meeting['project_id'],
                title=meeting['title'],
                datetime=meeting['datetime'],
                duration=meeting['duration'],
                location=meeting['location'],
                agenda=meeting.get('agenda', ''),
                participants=meeting.get('participants', []),
                organized_by=meeting.get('organized_by', None),
                status=meeting['status'],
                minutes=meeting.get('minutes', None),
                action_items=meeting.get('action_items', []),
                start_time=meeting.get('start_time', None),
                end_time=meeting.get('end_time', None)
            )
            db.add(new_meeting)
        db.commit()
        print(f"Added {len(meeting_data)} meetings to the database")
    except Exception as e:
        db.rollback()
        print(f"Error adding meetings: {str(e)}")
    finally:
        db.close()

def remove_json_files():
    """Remove all JSON data files from the data directory"""
    try:
        json_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        for file in json_files:
            os.remove(os.path.join(DATA_DIR, file))
        print(f"Removed {len(json_files)} JSON files")
    except Exception as e:
        print(f"Error removing JSON files: {str(e)}")

if __name__ == "__main__":
    print("Starting database reset and data migration...")
    
    # Ensure tables exist
    create_tables()
    
    # Clear existing data
    clear_database()
    
    # Populate database with JSON data
    populate_database()
    
    # Remove JSON files to ensure app uses only database
    remove_json_files()
    
    print("Migration completed successfully!")