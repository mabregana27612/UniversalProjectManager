import os
import json

def create_data_directory():
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created data directory")
    
    # Initialize empty data files
    data_files = [
        'projects.json',
        'tasks.json',
        'team_members.json',
        'documents.json',
        'users.json',
        'subtasks.json',
        'meetings.json'
    ]
    
    for file in data_files:
        file_path = os.path.join('data', file)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file == 'users.json':
                    # Create admin user
                    admin_user = [{
                        "id": 1,
                        "username": "admin",
                        "password_hash": "admin",  # In a real app, this would be hashed
                        "name": "System Administrator",
                        "email": "admin@example.com",
                        "role": "admin",
                        "created_at": "2023-01-01",
                        "last_login": None
                    }]
                    json.dump(admin_user, f)
                else:
                    # Initialize as empty array
                    json.dump([], f)
            print(f"Initialized {file}")

if __name__ == "__main__":
    create_data_directory()
    print("Data initialization complete. You can now run the application.")