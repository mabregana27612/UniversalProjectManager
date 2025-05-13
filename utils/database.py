import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Load environment variables
load_dotenv()

# Get the database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine and session - ensure a value is provided
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
    
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(100))
    name = Column(String(100))
    email = Column(String(100))
    role = Column(String(20))
    created_at = Column(String(20))
    last_login = Column(String(20), nullable=True)
    team_member_id = Column(Integer, nullable=True)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    type = Column(String(50))
    start_date = Column(String(20))
    end_date = Column(String(20))
    budget = Column(Float)
    status = Column(String(20))
    created_at = Column(String(20))
    created_by = Column(Integer, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    team_members = relationship("TeamMember", back_populates="project")
    documents = relationship("Document", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    description = Column(Text)
    start_date = Column(String(20))
    end_date = Column(String(20))
    status = Column(String(20))
    priority = Column(String(20))
    progress = Column(Integer, default=0)
    assigned_members = Column(JSON, default=[])
    dependencies = Column(JSON, default=[])
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(20), nullable=True)
    approved_by = Column(Integer, nullable=True)
    approval_date = Column(String(20), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    has_pending_changes = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="parent_task")
    change_requests = relationship("ChangeRequest", back_populates="task", foreign_keys="ChangeRequest.task_id")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    role = Column(String(50))
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    is_team_leader = Column(Boolean, default=False)
    reports_to = Column(Integer, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="team_members")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    file_type = Column(String(20))
    description = Column(Text, nullable=True)
    file_path = Column(String(255))
    uploaded_by = Column(Integer, nullable=True)
    upload_date = Column(String(20))
    
    # Relationships
    project = relationship("Project", back_populates="documents")

class Subtask(Base):
    __tablename__ = "subtasks"
    
    id = Column(Integer, primary_key=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    name = Column(String(100))
    description = Column(Text)
    start_date = Column(String(20))
    end_date = Column(String(20))
    status = Column(String(20))
    progress = Column(Integer, default=0)
    requires_approval = Column(Boolean, default=True)
    assigned_members = Column(JSON, default=[])
    created_by = Column(Integer, nullable=True)
    approval_status = Column(String(20), nullable=True)
    approved_by = Column(Integer, nullable=True)
    approval_date = Column(String(20), nullable=True)
    approval_comments = Column(Text, nullable=True)
    completion_report = Column(Text, nullable=True)
    completion_report_submitted_at = Column(String(20), nullable=True)
    completion_report_submitted_by = Column(Integer, nullable=True)
    has_pending_changes = Column(Boolean, default=False)
    
    # Relationships
    parent_task = relationship("Task", back_populates="subtasks")
    change_requests = relationship("ChangeRequest", foreign_keys="ChangeRequest.subtask_id")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(100))
    datetime = Column(String(20)) 
    duration = Column(Integer)  # in minutes
    location = Column(String(100))
    agenda = Column(Text)
    participants = Column(JSON, default=[])
    organized_by = Column(Integer, nullable=True)
    status = Column(String(20))  # Scheduled, In Progress, Completed, Cancelled
    minutes = Column(Text, nullable=True)
    action_items = Column(JSON, default=[])
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)

class ChangeRequest(Base):
    """Model for change requests"""
    __tablename__ = "change_requests"
    
    id = Column(Integer, primary_key=True)
    # Request can be for a task or subtask
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    subtask_id = Column(Integer, ForeignKey("subtasks.id"), nullable=True)
    
    # Request metadata
    requested_by = Column(Integer)  # User ID
    requested_at = Column(String(50))
    status = Column(String(20), default="Pending")  # Pending, Approved, Rejected
    
    # Current state and proposed changes
    current_data = Column(JSON)  # Current task/subtask data as JSON
    proposed_changes = Column(JSON)  # Only the changes
    change_reason = Column(Text, nullable=True)  # Reason for the changes
    impact_analysis = Column(Text, nullable=True)  # Analysis of impact and risks
    
    # Approval details
    reviewed_by = Column(Integer, nullable=True)  # User ID
    review_date = Column(String(50), nullable=True)
    review_comments = Column(Text, nullable=True)
    
    # Meeting requirement flag
    requires_meeting = Column(Boolean, default=False)
    meeting_id = Column(Integer, nullable=True)  # If a meeting was scheduled
    
    # Affected members (to be notified)
    affected_members = Column(JSON, default=[])
    
    # Relationships
    task = relationship("Task", back_populates="change_requests", foreign_keys=[task_id])
    subtask = relationship("Subtask", back_populates="change_requests", foreign_keys=[subtask_id])

# Create tables in the database
def create_tables():
    # Use a more defensive approach to create tables only if they don't exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    # Get existing tables
    existing_tables = inspector.get_table_names()
    
    # Create each table individually if it doesn't exist
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(engine)
    
    print(f"Database tables verified. Existing tables: {existing_tables}")

# Create a new session for database operations
def get_db_session():
    return SessionLocal()

# Migrate data from JSON files to database
def migrate_json_to_db():
    # Check if data dir exists
    data_dir = Path("data")
    if not data_dir.exists():
        print("No data directory found. Creating empty tables.")
        create_tables()
        return
    
    # Create tables first
    create_tables()
    
    # Open a session
    db = get_db_session()
    
    try:
        # Migrate users
        users_file = data_dir / "users.json"
        if users_file.exists():
            with open(users_file, "r") as f:
                users_data = json.load(f)
                for user_data in users_data:
                    user = User(**user_data)
                    db.add(user)
        
        # Migrate projects
        projects_file = data_dir / "projects.json"
        if projects_file.exists():
            with open(projects_file, "r") as f:
                projects_data = json.load(f)
                for project_data in projects_data:
                    # Remove relationships that aren't columns
                    for key in ["tasks", "team_members", "documents"]:
                        if key in project_data:
                            del project_data[key]
                    project = Project(**project_data)
                    db.add(project)
        
        # Migrate team members
        team_members_file = data_dir / "team_members.json"
        if team_members_file.exists():
            with open(team_members_file, "r") as f:
                team_members_data = json.load(f)
                for member_data in team_members_data:
                    team_member = TeamMember(**member_data)
                    db.add(team_member)
        
        # Migrate tasks
        tasks_file = data_dir / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file, "r") as f:
                tasks_data = json.load(f)
                for task_data in tasks_data:
                    # Remove relationships that aren't columns
                    if "subtasks" in task_data:
                        del task_data["subtasks"]
                    task = Task(**task_data)
                    db.add(task)
        
        # Migrate subtasks
        subtasks_file = data_dir / "subtasks.json"
        if subtasks_file.exists():
            with open(subtasks_file, "r") as f:
                subtasks_data = json.load(f)
                for subtask_data in subtasks_data:
                    subtask = Subtask(**subtask_data)
                    db.add(subtask)
        
        # Migrate documents
        documents_file = data_dir / "documents.json"
        if documents_file.exists():
            with open(documents_file, "r") as f:
                documents_data = json.load(f)
                for doc_data in documents_data:
                    document = Document(**doc_data)
                    db.add(document)
        
        # Migrate meetings
        meetings_file = data_dir / "meetings.json"
        if meetings_file.exists():
            with open(meetings_file, "r") as f:
                meetings_data = json.load(f)
                for meeting_data in meetings_data:
                    meeting = Meeting(**meeting_data)
                    db.add(meeting)
        
        # Commit all changes
        db.commit()
        print("Data migration completed successfully!")
    
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    
    finally:
        db.close()

# Helper function to convert SQLAlchemy model instances to dictionaries
def model_to_dict(model):
    result = {}
    for column in model.__table__.columns:
        result[column.name] = getattr(model, column.name)
    return result

# Data access functions to replace file-based functions
def get_all_users():
    db = get_db_session()
    try:
        users = db.query(User).all()
        return [model_to_dict(user) for user in users]
    finally:
        db.close()

def get_user_by_id(user_id):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return model_to_dict(user) if user else None
    finally:
        db.close()

def get_user_by_username(username):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        return model_to_dict(user) if user else None
    finally:
        db.close()

def create_user(user_data):
    db = get_db_session()
    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        return model_to_dict(user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def update_user(user_id, user_data):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        return model_to_dict(user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_all_projects():
    db = get_db_session()
    try:
        projects = db.query(Project).all()
        return [model_to_dict(project) for project in projects]
    finally:
        db.close()

def get_project(project_id):
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        return model_to_dict(project) if project else None
    finally:
        db.close()

def create_project(project_data):
    db = get_db_session()
    try:
        project = Project(**project_data)
        db.add(project)
        db.commit()
        return model_to_dict(project)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def update_project(project_id, project_data):
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        for key, value in project_data.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.commit()
        return model_to_dict(project)
    finally:
        db.close()

def delete_project(project_id):
    db = get_db_session()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_all_tasks():
    db = get_db_session()
    try:
        tasks = db.query(Task).all()
        return [model_to_dict(task) for task in tasks]
    finally:
        db.close()

def get_task(task_id):
    db = get_db_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        return model_to_dict(task) if task else None
    finally:
        db.close()

def get_project_tasks(project_id):
    db = get_db_session()
    try:
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        return [model_to_dict(task) for task in tasks]
    finally:
        db.close()

def create_task(task_data):
    db = get_db_session()
    try:
        task = Task(**task_data)
    except TypeError as e:
        print(f"Error creating Task: {e}")
        raise
        db.add(task)
        db.commit()
        return model_to_dict(task)
    finally:
        db.close()

def update_task(task_id, task_data):
    db = get_db_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        db.commit()
        return model_to_dict(task)
    finally:
        db.close()

def delete_task(task_id):
    db = get_db_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        # Delete all subtasks associated with this task
        db.query(Subtask).filter(Subtask.parent_task_id == task_id).delete()
        
        db.delete(task)
        db.commit()
        return True
    finally:
        db.close()

def get_all_team_members():
    db = get_db_session()
    try:
        members = db.query(TeamMember).all()
        return [model_to_dict(member) for member in members]
    finally:
        db.close()

def get_team_member(member_id):
    db = get_db_session()
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        return model_to_dict(member) if member else None
    finally:
        db.close()

def get_project_team(project_id):
    db = get_db_session()
    try:
        members = db.query(TeamMember).filter(TeamMember.project_id == project_id).all()
        return [model_to_dict(member) for member in members]
    finally:
        db.close()

def create_team_member(member_data):
    db = get_db_session()
    try:
        member = TeamMember(**member_data)
        db.add(member)
        db.commit()
        return model_to_dict(member)
    finally:
        db.close()

def update_team_member(member_id, member_data):
    db = get_db_session()
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            return None
        
        for key, value in member_data.items():
            if hasattr(member, key):
                setattr(member, key, value)
        
        db.commit()
        return model_to_dict(member)
    finally:
        db.close()

def delete_team_member(member_id):
    db = get_db_session()
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            return False
        
        db.delete(member)
        db.commit()
        return True
    finally:
        db.close()

def get_team_members_by_leader(leader_id):
    db = get_db_session()
    try:
        members = db.query(TeamMember).filter(TeamMember.reports_to == leader_id).all()
        return [model_to_dict(member) for member in members]
    finally:
        db.close()

def get_all_documents():
    db = get_db_session()
    try:
        documents = db.query(Document).all()
        return [model_to_dict(doc) for doc in documents]
    finally:
        db.close()

def get_project_documents(project_id):
    db = get_db_session()
    try:
        documents = db.query(Document).filter(Document.project_id == project_id).all()
        return [model_to_dict(doc) for doc in documents]
    finally:
        db.close()

def create_document(document_data):
    db = get_db_session()
    try:
        document = Document(**document_data)
        db.add(document)
        db.commit()
        return model_to_dict(document)
    finally:
        db.close()

def update_document(document_id, document_data):
    db = get_db_session()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        for key, value in document_data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        db.commit()
        return model_to_dict(document)
    finally:
        db.close()

def delete_document(document_id):
    db = get_db_session()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        db.delete(document)
        db.commit()
        return True
    finally:
        db.close()

def get_all_subtasks():
    db = get_db_session()
    try:
        subtasks = db.query(Subtask).all()
        return [model_to_dict(subtask) for subtask in subtasks]
    finally:
        db.close()

def get_subtask(subtask_id):
    db = get_db_session()
    try:
        subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
        return model_to_dict(subtask) if subtask else None
    finally:
        db.close()

def get_subtasks_by_parent(parent_task_id):
    db = get_db_session()
    try:
        subtasks = db.query(Subtask).filter(Subtask.parent_task_id == parent_task_id).all()
        return [model_to_dict(subtask) for subtask in subtasks]
    finally:
        db.close()

def create_subtask(subtask_data):
    db = get_db_session()
    try:
        subtask = Subtask(**subtask_data)
        db.add(subtask)
        db.commit()
        return model_to_dict(subtask)
    finally:
        db.close()

def update_subtask(subtask_id, subtask_data):
    db = get_db_session()
    try:
        subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
        if not subtask:
            return None
        
        for key, value in subtask_data.items():
            if hasattr(subtask, key):
                setattr(subtask, key, value)
        
        db.commit()
        return model_to_dict(subtask)
    finally:
        db.close()

def delete_subtask(subtask_id):
    db = get_db_session()
    try:
        subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
        if not subtask:
            return False
        
        db.delete(subtask)
        db.commit()
        return True
    finally:
        db.close()

def get_subtasks_by_member(member_id):
    db = get_db_session()
    try:
        # This query is more complex because assigned_members is a JSON field
        # For simplicity, we'll fetch all subtasks and filter in Python
        all_subtasks = db.query(Subtask).all()
        assigned_subtasks = []
        
        for subtask in all_subtasks:
            assigned_members = getattr(subtask, 'assigned_members', [])
            if member_id in assigned_members:
                assigned_subtasks.append(model_to_dict(subtask))
        
        return assigned_subtasks
    finally:
        db.close()

def get_all_meetings():
    db = get_db_session()
    try:
        meetings = db.query(Meeting).all()
        return [model_to_dict(meeting) for meeting in meetings]
    finally:
        db.close()

def get_meeting(meeting_id):
    db = get_db_session()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        return model_to_dict(meeting) if meeting else None
    finally:
        db.close()

def get_project_meetings(project_id):
    db = get_db_session()
    try:
        meetings = db.query(Meeting).filter(Meeting.project_id == project_id).all()
        return [model_to_dict(meeting) for meeting in meetings]
    finally:
        db.close()

def create_meeting(meeting_data):
    db = get_db_session()
    try:
        meeting = Meeting(**meeting_data)
        db.add(meeting)
        db.commit()
        return model_to_dict(meeting)
    finally:
        db.close()

def update_meeting(meeting_id, meeting_data):
    db = get_db_session()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return None
        
        for key, value in meeting_data.items():
            if hasattr(meeting, key):
                setattr(meeting, key, value)
        
        db.commit()
        return model_to_dict(meeting)
    finally:
        db.close()

def delete_meeting(meeting_id):
    db = get_db_session()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return False
        
        db.delete(meeting)
        db.commit()
        return True
    finally:
        db.close()

def get_completed_meetings_for_task(task_id):
    """Get all completed meetings that discuss a specific task"""
    db = get_db_session()
    try:
        # We need to find meetings related to this task
        # Since we don't have a direct task_id field in meetings table,
        # we'll need to retrieve all meetings for the task's project
        # and then check if the task is discussed in the meeting (via action items or minutes)
        
        # First, get the task to find its project
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return []
        
        # Get all completed meetings for this project
        project_meetings = db.query(Meeting).filter(
            Meeting.project_id == task.project_id,
            Meeting.status == 'Completed'
        ).all()
        
        # Convert to dict for manipulation and analysis
        meetings_list = [model_to_dict(meeting) for meeting in project_meetings]
        
        # Filter meetings related to this task
        # This is a simplistic approach - in a real app, you might have a more structured way 
        # to track which tasks were discussed in which meetings
        relevant_meetings = []
        task_name = task.name.lower()
        
        for meeting in meetings_list:
            # Check if task is mentioned in minutes
            if meeting.get('minutes') and task_name in meeting.get('minutes', '').lower():
                relevant_meetings.append(meeting)
                continue
                
            # Check if task is mentioned in action items
            action_items = meeting.get('action_items', [])
            for item in action_items:
                if isinstance(item, dict) and 'description' in item:
                    if task_name in item['description'].lower():
                        relevant_meetings.append(meeting)
                        break
        
        return relevant_meetings
    finally:
        db.close()

if __name__ == "__main__":
    # Create database tables and migrate data when this module is run directly
    migrate_json_to_db()
