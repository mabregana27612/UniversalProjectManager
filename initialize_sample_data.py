"""
Script to initialize sample data in the database for demonstration purposes.
"""

import datetime
from utils.database import (
    get_db_session, create_tables, User, Project, Task,
    TeamMember, Document, Subtask, Meeting
)

def create_sample_data():
    """Create sample data in the database"""
    db = get_db_session()
    try:
        # Check if we already have data
        if db.query(Project).count() > 0:
            print("Database already contains projects. Skipping sample data creation.")
            return
        
        # Ensure we have at least admin user
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            admin_user = User(
                id=1,
                username='admin',
                password_hash='admin',  # In a real app, this would be hashed
                name='System Administrator',
                email='admin@example.com',
                role='admin',
                created_at=datetime.datetime.now().strftime('%Y-%m-%d')
            )
            db.add(admin_user)
            db.commit()
        
        # Create sample projects
        projects = [
            {
                'name': 'Website Redesign',
                'description': 'Redesign company website to improve user experience and conversion rates.',
                'type': 'Development',
                'start_date': '2023-05-01',
                'end_date': '2023-09-30',
                'budget': 45000.00,
                'status': 'In Progress',
                'created_by': admin_user.id
            },
            {
                'name': 'Mobile App Development',
                'description': 'Develop a mobile app for both iOS and Android platforms.',
                'type': 'Development',
                'start_date': '2023-06-15',
                'end_date': '2023-12-15',
                'budget': 80000.00,
                'status': 'Not Started',
                'created_by': admin_user.id
            },
            {
                'name': 'Annual Marketing Campaign',
                'description': 'Plan and execute the annual marketing campaign for Q4.',
                'type': 'Marketing',
                'start_date': '2023-08-01',
                'end_date': '2023-12-31',
                'budget': 65000.00,
                'status': 'Planning',
                'created_by': admin_user.id
            },
            {
                'name': 'Office Renovation',
                'description': 'Renovate the office space to accommodate growing team.',
                'type': 'Infrastructure',
                'start_date': '2023-03-15',
                'end_date': '2023-06-30',
                'budget': 120000.00,
                'status': 'Completed',
                'created_by': admin_user.id
            }
        ]
        
        db_projects = []
        for i, project_data in enumerate(projects, 1):
            project = Project(
                id=i,
                name=project_data['name'],
                description=project_data['description'],
                type=project_data['type'],
                start_date=project_data['start_date'],
                end_date=project_data['end_date'],
                budget=project_data['budget'],
                status=project_data['status'],
                created_at=datetime.datetime.now().strftime('%Y-%m-%d'),
                created_by=project_data['created_by'],
                is_archived=False
            )
            db.add(project)
            db_projects.append(project)
        
        db.commit()
        print(f"Added {len(projects)} sample projects")
        
        # Create team members
        team_members = [
            # Project 1: Website Redesign
            {
                'project_id': 1,
                'name': 'John Smith',
                'role': 'Project Manager',
                'contact_email': 'john.smith@example.com',
                'is_team_leader': True
            },
            {
                'project_id': 1,
                'name': 'Emily Johnson',
                'role': 'UI/UX Designer',
                'contact_email': 'emily.johnson@example.com',
                'is_team_leader': False,
                'reports_to': 1
            },
            {
                'project_id': 1,
                'name': 'Michael Brown',
                'role': 'Frontend Developer',
                'contact_email': 'michael.brown@example.com',
                'is_team_leader': False,
                'reports_to': 1
            },
            {
                'project_id': 1,
                'name': 'Sarah Davis',
                'role': 'Backend Developer',
                'contact_email': 'sarah.davis@example.com',
                'is_team_leader': False,
                'reports_to': 1
            },
            
            # Project 2: Mobile App Development
            {
                'project_id': 2,
                'name': 'David Wilson',
                'role': 'Project Manager',
                'contact_email': 'david.wilson@example.com',
                'is_team_leader': True
            },
            {
                'project_id': 2,
                'name': 'Jennifer Lee',
                'role': 'iOS Developer',
                'contact_email': 'jennifer.lee@example.com',
                'is_team_leader': False,
                'reports_to': 5
            },
            {
                'project_id': 2,
                'name': 'Robert Taylor',
                'role': 'Android Developer',
                'contact_email': 'robert.taylor@example.com',
                'is_team_leader': False,
                'reports_to': 5
            },
            
            # Project 3: Annual Marketing Campaign
            {
                'project_id': 3,
                'name': 'Jessica Martinez',
                'role': 'Marketing Director',
                'contact_email': 'jessica.martinez@example.com',
                'is_team_leader': True
            },
            {
                'project_id': 3,
                'name': 'Thomas Anderson',
                'role': 'Content Creator',
                'contact_email': 'thomas.anderson@example.com',
                'is_team_leader': False,
                'reports_to': 8
            },
            {
                'project_id': 3,
                'name': 'Lisa Wong',
                'role': 'Social Media Specialist',
                'contact_email': 'lisa.wong@example.com',
                'is_team_leader': False,
                'reports_to': 8
            },
            
            # Project 4: Office Renovation
            {
                'project_id': 4,
                'name': 'Kevin Clark',
                'role': 'Facilities Manager',
                'contact_email': 'kevin.clark@example.com',
                'is_team_leader': True
            },
            {
                'project_id': 4,
                'name': 'Amanda Lewis',
                'role': 'Interior Designer',
                'contact_email': 'amanda.lewis@example.com',
                'is_team_leader': False,
                'reports_to': 11
            }
        ]
        
        for i, member_data in enumerate(team_members, 1):
            member = TeamMember(
                id=i,
                project_id=member_data['project_id'],
                name=member_data['name'],
                role=member_data['role'],
                contact_email=member_data.get('contact_email'),
                contact_phone=member_data.get('contact_phone'),
                is_team_leader=member_data.get('is_team_leader', False),
                reports_to=member_data.get('reports_to')
            )
            db.add(member)
        
        db.commit()
        print(f"Added {len(team_members)} sample team members")
        
        # Create tasks
        tasks = [
            # Project 1: Website Redesign
            {
                'project_id': 1,
                'name': 'User Research and Analysis',
                'description': 'Conduct user research and analyze current website performance.',
                'start_date': '2023-05-01',
                'end_date': '2023-05-15',
                'status': 'Completed',
                'priority': 'High',
                'progress': 100,
                'assigned_members': [1, 2]
            },
            {
                'project_id': 1,
                'name': 'UI/UX Design',
                'description': 'Create wireframes and design mockups for the new website.',
                'start_date': '2023-05-16',
                'end_date': '2023-06-15',
                'status': 'Completed',
                'priority': 'High',
                'progress': 100,
                'assigned_members': [2],
                'dependencies': [1]
            },
            {
                'project_id': 1,
                'name': 'Frontend Development',
                'description': 'Implement the new design using HTML, CSS, and JavaScript.',
                'start_date': '2023-06-16',
                'end_date': '2023-08-15',
                'status': 'In Progress',
                'priority': 'Medium',
                'progress': 65,
                'assigned_members': [3],
                'dependencies': [2],
                'requires_approval': True,
                'approval_status': 'Pending'
            },
            {
                'project_id': 1,
                'name': 'Backend Integration',
                'description': 'Integrate the frontend with backend systems and databases.',
                'start_date': '2023-07-15',
                'end_date': '2023-09-15',
                'status': 'In Progress',
                'priority': 'Medium',
                'progress': 30,
                'assigned_members': [4],
                'dependencies': [3]
            },
            {
                'project_id': 1,
                'name': 'Testing and Quality Assurance',
                'description': 'Test the website for bugs and ensure it meets quality standards.',
                'start_date': '2023-09-01',
                'end_date': '2023-09-20',
                'status': 'Not Started',
                'priority': 'High',
                'progress': 0,
                'assigned_members': [1, 2, 3, 4],
                'dependencies': [3, 4]
            },
            
            # Project 2: Mobile App Development
            {
                'project_id': 2,
                'name': 'Requirements Gathering',
                'description': 'Gather and document app requirements from stakeholders.',
                'start_date': '2023-06-15',
                'end_date': '2023-06-30',
                'status': 'Not Started',
                'priority': 'High',
                'progress': 0,
                'assigned_members': [5]
            },
            {
                'project_id': 2,
                'name': 'App Design',
                'description': 'Create app UI/UX design and user flows.',
                'start_date': '2023-07-01',
                'end_date': '2023-07-31',
                'status': 'Not Started',
                'priority': 'High',
                'progress': 0,
                'assigned_members': [5, 6, 7],
                'dependencies': [6]
            },
            
            # Project 3: Annual Marketing Campaign
            {
                'project_id': 3,
                'name': 'Campaign Strategy',
                'description': 'Develop the overall marketing campaign strategy.',
                'start_date': '2023-08-01',
                'end_date': '2023-08-15',
                'status': 'Planning',
                'priority': 'High',
                'progress': 25,
                'assigned_members': [8]
            },
            {
                'project_id': 3,
                'name': 'Content Creation',
                'description': 'Create content for various marketing channels.',
                'start_date': '2023-08-16',
                'end_date': '2023-09-30',
                'status': 'Not Started',
                'priority': 'Medium',
                'progress': 0,
                'assigned_members': [9],
                'dependencies': [8]
            },
            
            # Project 4: Office Renovation
            {
                'project_id': 4,
                'name': 'Space Planning',
                'description': 'Plan the layout and space allocation for the new office.',
                'start_date': '2023-03-15',
                'end_date': '2023-03-31',
                'status': 'Completed',
                'priority': 'High',
                'progress': 100,
                'assigned_members': [11, 12]
            },
            {
                'project_id': 4,
                'name': 'Construction Work',
                'description': 'Perform construction and renovation tasks.',
                'start_date': '2023-04-01',
                'end_date': '2023-06-15',
                'status': 'Completed',
                'priority': 'High',
                'progress': 100,
                'assigned_members': [11],
                'dependencies': [10]
            }
        ]
        
        for i, task_data in enumerate(tasks, 1):
            task = Task(
                id=i,
                project_id=task_data['project_id'],
                name=task_data['name'],
                description=task_data['description'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                status=task_data['status'],
                priority=task_data['priority'],
                progress=task_data['progress'],
                assigned_members=task_data.get('assigned_members', []),
                dependencies=task_data.get('dependencies', []),
                requires_approval=task_data.get('requires_approval', False),
                approval_status=task_data.get('approval_status'),
                approved_by=task_data.get('approved_by'),
                approval_date=task_data.get('approval_date'),
                rejection_reason=task_data.get('rejection_reason')
            )
            db.add(task)
        
        db.commit()
        print(f"Added {len(tasks)} sample tasks")
        
        # Create subtasks
        subtasks = [
            {
                'parent_task_id': 3,  # Frontend Development
                'name': 'Implement Homepage',
                'description': 'Develop the homepage according to the design.',
                'start_date': '2023-06-16',
                'end_date': '2023-06-30',
                'status': 'Completed',
                'progress': 100,
                'assigned_members': [3]
            },
            {
                'parent_task_id': 3,  # Frontend Development
                'name': 'Implement Product Pages',
                'description': 'Develop the product pages according to the design.',
                'start_date': '2023-07-01',
                'end_date': '2023-07-15',
                'status': 'Completed',
                'progress': 100,
                'assigned_members': [3]
            },
            {
                'parent_task_id': 3,  # Frontend Development
                'name': 'Implement Checkout Process',
                'description': 'Develop the checkout process according to the design.',
                'start_date': '2023-07-16',
                'end_date': '2023-08-15',
                'status': 'In Progress',
                'progress': 60,
                'assigned_members': [3]
            }
        ]
        
        for i, subtask_data in enumerate(subtasks, 1):
            subtask = Subtask(
                id=i,
                parent_task_id=subtask_data['parent_task_id'],
                name=subtask_data['name'],
                description=subtask_data['description'],
                start_date=subtask_data['start_date'],
                end_date=subtask_data['end_date'],
                status=subtask_data['status'],
                progress=subtask_data['progress'],
                requires_approval=True,
                assigned_members=subtask_data.get('assigned_members', []),
                created_by=admin_user.id
            )
            db.add(subtask)
        
        db.commit()
        print(f"Added {len(subtasks)} sample subtasks")
        
        # Create meetings
        meetings = [
            {
                'project_id': 1,  # Website Redesign
                'title': 'Kickoff Meeting',
                'datetime': '2023-05-01 09:00:00',
                'duration': 60,  # minutes
                'location': 'Conference Room A',
                'agenda': 'Discuss project goals, timeline, and assignments.',
                'participants': [1, 2, 3, 4],
                'organized_by': 1,
                'status': 'Completed',
                'minutes': 'Discussed project goals and assigned initial tasks. Everyone is clear on their responsibilities.',
                'action_items': [
                    {'assignee_id': 1, 'description': 'Create detailed project plan', 'due_date': '2023-05-03', 'status': 'Completed'},
                    {'assignee_id': 2, 'description': 'Begin user research', 'due_date': '2023-05-05', 'status': 'Completed'}
                ],
                'start_time': '2023-05-01 09:00:00',
                'end_time': '2023-05-01 10:00:00'
            },
            {
                'project_id': 1,  # Website Redesign
                'title': 'Design Review',
                'datetime': '2023-06-05 14:00:00',
                'duration': 90,  # minutes
                'location': 'Conference Room B',
                'agenda': 'Review design mockups and provide feedback.',
                'participants': [1, 2, 3],
                'organized_by': 1,
                'status': 'Completed',
                'minutes': 'Reviewed design mockups. Made several suggestions for improvements. Overall, the designs look good.',
                'action_items': [
                    {'assignee_id': 2, 'description': 'Incorporate feedback into designs', 'due_date': '2023-06-10', 'status': 'Completed'}
                ],
                'start_time': '2023-06-05 14:00:00',
                'end_time': '2023-06-05 15:30:00'
            }
        ]
        
        for i, meeting_data in enumerate(meetings, 1):
            meeting = Meeting(
                id=i,
                project_id=meeting_data['project_id'],
                title=meeting_data['title'],
                datetime=meeting_data['datetime'],
                duration=meeting_data['duration'],
                location=meeting_data['location'],
                agenda=meeting_data['agenda'],
                participants=meeting_data['participants'],
                organized_by=meeting_data['organized_by'],
                status=meeting_data['status'],
                minutes=meeting_data['minutes'],
                action_items=meeting_data['action_items'],
                start_time=meeting_data['start_time'],
                end_time=meeting_data['end_time']
            )
            db.add(meeting)
        
        db.commit()
        print(f"Added {len(meetings)} sample meetings")
        
        print("Sample data created successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error creating sample data: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing sample data...")
    
    # Ensure tables exist
    create_tables()
    
    # Create sample data
    create_sample_data()
    
    print("Sample data initialization completed!")