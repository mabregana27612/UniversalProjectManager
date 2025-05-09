"""
Script to create user accounts for team members with different roles.
"""
import datetime
from utils.database import get_db_session, User, get_all_team_members
from sqlalchemy.exc import IntegrityError

def create_team_member_users():
    """Create user accounts for team members"""
    print("Creating user accounts for team members...")
    
    # Get all team members from the database
    team_members = get_all_team_members()
    
    # Create users for each team member with different roles
    for member in team_members:
        # Check if username already exists (using email as username)
        email = member.get('contact_email')
        if not email:
            print(f"Skipping user creation for {member['name']} - no email address")
            continue
            
        # Create simple username from email (part before @)
        username = email.split('@')[0]
        
        # Check if user with this username already exists
        db = get_db_session()
        existing_user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if existing_user:
            print(f"User {username} already exists, skipping")
            continue
        
        # Determine role based on team_leader status
        role = 'team_leader' if member.get('is_team_leader', False) else 'team_member'
        
        # Create user data
        user_data = {
            'username': username,
            'password_hash': 'password123',  # Simple password for testing
            'name': member['name'],
            'email': email,
            'role': role,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d'),
            'team_member_id': member['id']
        }
        
        # Create the user directly using SQLAlchemy
        try:
            db = get_db_session()
            new_user = User(**user_data)
            db.add(new_user)
            db.commit()
            print(f"Created user {username} with role {role} for {member['name']}")
        except IntegrityError as e:
            db.rollback()
            print(f"Failed to create user for {member['name']}: {str(e)}")
        except Exception as e:
            db.rollback()
            print(f"Error creating user for {member['name']}: {str(e)}")
        finally:
            db.close()
    
    # Create admin user if not exists
    db = get_db_session()
    admin_exists = db.query(User).filter(User.username == 'admin').first()
    db.close()
    
    if not admin_exists:
        admin_data = {
            'username': 'admin',
            'password_hash': 'admin',  # Simple password for testing
            'name': 'System Administrator',
            'email': 'admin@example.com',
            'role': 'admin',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            db = get_db_session()
            new_admin = User(**admin_data)
            db.add(new_admin)
            db.commit()
            print("Created admin user")
        except Exception as e:
            db.rollback()
            print(f"Failed to create admin user: {str(e)}")
        finally:
            db.close()
    else:
        print("Admin user already exists")
    
    print("User account creation completed!")

if __name__ == "__main__":
    create_team_member_users()