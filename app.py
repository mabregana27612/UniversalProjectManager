import streamlit as st
import os
import datetime
import pandas as pd
from utils.data_management import load_data, save_data, initialize_data, authenticate_user
from utils.visualization import create_project_status_chart, create_project_type_chart
from utils.database import create_tables  # Import database functions

# Configure Streamlit page
st.set_page_config(
    page_title="Universal Project Management Information System (UPMIS)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Dashboard'
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None
if 'data_initialized' not in st.session_state:
    # Create database tables if they don't exist
    create_tables()
    initialize_data()
    st.session_state.data_initialized = True
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'team_member_id' not in st.session_state:
    st.session_state.team_member_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Load data into session state if not already loaded
if 'projects' not in st.session_state:
    st.session_state.projects = load_data('projects')
if 'tasks' not in st.session_state:
    st.session_state.tasks = load_data('tasks')
if 'team_members' not in st.session_state:
    st.session_state.team_members = load_data('team_members')
if 'documents' not in st.session_state:
    st.session_state.documents = load_data('documents')
if 'subtasks' not in st.session_state:
    st.session_state.subtasks = load_data('subtasks')
if 'users' not in st.session_state:
    st.session_state.users = load_data('users')

# Authentication check - allow Public Projects page without login
public_pages = ["User Account", "Public Projects"]
if not st.session_state.logged_in and st.session_state.current_page not in public_pages:
    # Force redirect to user account page for login
    st.session_state.current_page = "User Account"
    # Import user management page for login
    from pages.user_management import show_login_page
    show_login_page()
else:
    # Sidebar navigation (always shown)
    st.sidebar.title("📊 UPMIS Navigation")
    
    # User info in sidebar
    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as: {st.session_state.get('username', 'User')}")
        if st.sidebar.button("Logout"):
            # Reset session state for logout
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_role = None
            st.session_state.team_member_id = None
            st.session_state.username = None
            st.session_state.user_name = None
            st.session_state.current_page = "User Account"
            st.rerun()
    else:
        st.sidebar.info("👋 Welcome! Please login to access all features.")
        if st.sidebar.button("Login / Register"):
            st.session_state.current_page = "User Account"
            st.rerun()
    
    # Project selector in sidebar (only when logged in)
    if st.session_state.logged_in and st.session_state.projects:
        project_list = [f"{p['id']} - {p['name']}" for p in st.session_state.projects]
        selected_project = st.sidebar.selectbox(
            "Select Project",
            ["None"] + project_list
        )
        
        if selected_project != "None":
            project_id = int(selected_project.split(' - ')[0])
            st.session_state.current_project_id = project_id
        else:
            st.session_state.current_project_id = None
    
    # Always show navigation menu
    st.sidebar.markdown("### Navigation")
    
    # Full navigation list - all options always visible
    navigation_options = [
        "Dashboard",
        "Project Creation",
        "Timeline",
        "Team Management", 
        "Team Meetings",
        "Subtasks",
        "Change Requests",
        "Documents",
        "Reports",
        "Archives",
        "Public Projects",
        "User Account"
    ]
    
    page = st.sidebar.radio("Go to", navigation_options)
    st.session_state.current_page = page

# Use session_state.current_page to ensure page value is always available
page = st.session_state.current_page

# Protected pages that require login
protected_pages = [
    "Dashboard", "Project Creation", "Timeline", "Team Management", 
    "Team Meetings", "Subtasks", "Change Requests", "Documents", "Reports", "Archives"
]

# Check if user is trying to access a protected page without being logged in
if page in protected_pages and not st.session_state.logged_in:
    st.warning("⚠️ Please log in to access this page")
    # Show login form directly on this page
    from pages.user_management import show_login_page
    show_login_page()
# Display appropriate page based on selection
elif page == "Dashboard":
    st.title("📊 Project Management Dashboard")
    
    # Display dashboard image
    st.image("https://pixabay.com/get/g8b3d37ff307996abc978a8e11e24f35015d2c356a5cfe79d601ddd3b8476138a3ca842ef0cefe05dcb9a96506a95e69b69ea8d715575566b2a71ae0b1b343e33_1280.jpg", 
             caption="Project Management Dashboard", use_container_width=True)
    
    # Dashboard metrics
    if st.session_state.projects:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Projects", len(st.session_state.projects))
        
        with col2:
            active_projects = sum(1 for p in st.session_state.projects if p['status'] != 'Completed')
            st.metric("Active Projects", active_projects)
        
        with col3:
            completed_projects = sum(1 for p in st.session_state.projects if p['status'] == 'Completed')
            st.metric("Completed Projects", completed_projects)
        
        # Project status and type charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Projects by Status")
            fig = create_project_status_chart(st.session_state.projects)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Projects by Type")
            fig = create_project_type_chart(st.session_state.projects)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent projects
        st.subheader("Recent Projects")
        recent_projects = sorted(
            st.session_state.projects,
            key=lambda x: datetime.datetime.strptime(x['start_date'], '%Y-%m-%d'),
            reverse=True
        )[:5]
        
        for project in recent_projects:
            with st.expander(f"{project['name']} ({project['type']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description:** {project['description']}")
                    st.write(f"**Status:** {project['status']}")
                with col2:
                    st.write(f"**Budget:** ${project['budget']:,.2f}")
                    st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
    else:
        st.info("No projects found. Create a new project to get started.")
        if st.button("Create Your First Project"):
            st.session_state.current_page = "Project Creation"
            st.rerun()

elif page == "Project Creation":
    # Import project creation page
    from pages.project_creation import show_project_creation
    show_project_creation()

elif page == "Timeline":
    # Import timeline page
    from pages.timeline import show_timeline
    show_timeline()

elif page == "Team Management":
    # Import team management page
    from pages.team_management import show_team_management
    show_team_management()

elif page == "Documents":
    # Import documents page
    from pages.documents import show_documents
    show_documents()

elif page == "Reports":
    # Import reports page
    from pages.reports import show_reports
    show_reports()

elif page == "Archives":
    # Import archives page
    from pages.archive import show_archives
    show_archives()

elif page == "Subtasks":
    # Import subtasks page
    from pages.subtasks import show_subtasks
    show_subtasks()

elif page == "Team Meetings":
    # Import team meetings page
    from pages.team_meetings import show_team_meetings
    show_team_meetings()

elif page == "Change Requests":
    # Import change requests page
    from pages.change_requests import show_change_requests
    show_change_requests()

elif page == "Public Projects":
    # Import public projects page
    from pages.public_projects import show_public_projects
    show_public_projects()

elif page == "User Account":
    # Import user management page
    from pages.user_management import show_user_management
    show_user_management()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2023 Universal Project Management Information System (UPMIS)")
