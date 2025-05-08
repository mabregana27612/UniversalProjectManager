import streamlit as st
import datetime
from utils.data_management import (
    register_user, authenticate_user, update_user, get_user_by_id,
    get_team_member, get_user_by_team_member_id, get_project_team_leaders
)

def show_user_management():
    st.title("👤 User Account Management")
    
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        show_login_page()
    else:
        show_user_dashboard()

def show_login_page():
    # Create tabs for login and registration
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        st.subheader("Login to your Account")
        
        # Login form using st.form to prevent auto-submission on focus changes
        with st.form(key="login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", key="login_password", type="password")
            
            # Submit button inside the form
            login_submitted = st.form_submit_button("Login")
            
            # Only process after user explicitly clicks the login button
            if login_submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    result = authenticate_user(username, password)
                    if result['success']:
                        # Debug output
                        st.write(f"Debug - User data: {result['user']}")
                        
                        # Set user in session
                        st.session_state.user_id = result['user']['id']
                        st.session_state.username = result['user']['username']
                        st.session_state.user_role = result['user']['role']
                        st.session_state.team_member_id = result['user'].get('team_member_id')
                        st.session_state.user_name = result['user']['name']  # Use 'name' instead of 'full_name'
                        st.session_state.logged_in = True  # Explicitly set logged_in state
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result['message'])
    
    with register_tab:
        st.subheader("Create a New Account")
        
        # Use st.form to prevent automatic form submission on input changes
        with st.form(key="registration_form"):
            # Registration form fields
            full_name = st.text_input("Full Name", key="reg_full_name")
            email = st.text_input("Email", key="reg_email")
            username = st.text_input("Username", key="reg_username")
            password = st.text_input("Password", key="reg_password", type="password")
            confirm_password = st.text_input("Confirm Password", key="reg_confirm_password", type="password")
            
            # Team member selection if they're existing members
            st.subheader("Link to Team Member Profile (Optional)")
            st.caption("If you're already added as a team member, select your profile below to link it.")
            
            # Only if project is selected, show team members
            selected_team_member_id = None
            if 'current_project_id' in st.session_state and st.session_state.current_project_id:
                project_id = st.session_state.current_project_id
                
                # Get team members without user accounts
                from utils.data_management import get_project_team
                team_members = get_project_team(project_id)
                
                # Filter out team members who already have accounts
                available_members = []
                for member in team_members:
                    user = get_user_by_team_member_id(member['id'])
                    if not user:
                        available_members.append(member)
                
                if available_members:
                    team_member_options = ["None"] + [f"{m['name']} ({m['role']})" for m in available_members]
                    team_member_index = st.selectbox(
                        "Link to existing team member profile",
                        options=range(len(team_member_options)),
                        format_func=lambda x: team_member_options[x],
                        key="team_member_selection"
                    )
                    
                    # Get selected team member ID, if any
                    if team_member_index > 0:  # Not "None"
                        selected_team_member_id = available_members[team_member_index - 1]['id']
                else:
                    st.info("No available team members to link to. Team members must be created first in the Team Management section.")
            else:
                st.info("Please select a project from the sidebar to link to a team member profile.")
            
            # Form submission button
            register_submitted = st.form_submit_button("Register")
            
            # Process form submission
            if register_submitted:
                # Validate form
                if not full_name or not email or not username or not password:
                    st.error("Please fill out all required fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Register the user
                    user_data = {
                        'username': username,
                        'password_hash': password,  # In a real app, you'd hash this
                        'email': email,
                        'name': full_name,
                        'role': 'team_member',  # Default role for new registrations
                        'team_member_id': selected_team_member_id,
                        'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    result = register_user(user_data)
                    if result['success']:
                        st.success("Registration successful! You can now log in.")
                        # Clear the form
                        for key in ['reg_full_name', 'reg_email', 'reg_username', 'reg_password', 'reg_confirm_password']:
                            if key in st.session_state:
                                st.session_state[key] = ""
                    else:
                        st.error(result['message'])

def show_user_dashboard():
    # Check if user_name exists in session state, use username as fallback
    user_name = st.session_state.get('user_name', st.session_state.get('username', 'User'))
    st.subheader(f"Welcome, {user_name}!")
    
    # Get user details
    user = get_user_by_id(st.session_state.user_id)
    if not user:
        st.error("User information not found.")
        logout_user()
        return
    
    # Display user role badge
    role_badge_style = {
        'admin': "background-color: #1E88E5; color: white; padding: 5px 10px; border-radius: 5px;",
        'team_leader': "background-color: #43A047; color: white; padding: 5px 10px; border-radius: 5px;",
        'team_member': "background-color: #FB8C00; color: white; padding: 5px 10px; border-radius: 5px;"
    }
    
    user_role = user.get('role') or 'team_member'
    role_display = user_role.replace('_', ' ').title()
    style = role_badge_style.get(user_role) or role_badge_style['team_member']
    st.markdown(f"<span style='{style}'>{role_display}</span>", unsafe_allow_html=True)
    
    # Tabs for dashboard
    profile_tab, tasks_tab = st.tabs(["My Profile", "My Tasks"])
    
    with profile_tab:
        st.subheader("Profile Information")
        
        # Display/edit profile information
        with st.form("profile_form"):
            full_name = st.text_input("Full Name", value=user.get('name', ''))
            email = st.text_input("Email", value=user.get('email', ''))
            
            # If linked to team member, show their info
            if user.get('team_member_id'):
                team_member = get_team_member(user['team_member_id'])
                if team_member:
                    st.info(f"Linked to team member profile: {team_member['name']} ({team_member['role']})")
                    
                    # Show if they're a team leader
                    if team_member.get('is_team_leader', False):
                        st.success("You are a Team Leader")
                        
                        # Show team members who report to this leader
                        from utils.data_management import get_team_members_by_leader
                        team = get_team_members_by_leader(team_member['id'])
                        if team:
                            st.write("Team Members reporting to you:")
                            for member in team:
                                st.write(f"- {member['name']} ({member['role']})")
                    
                    # Show who they report to
                    if team_member.get('reports_to'):
                        leader = get_team_member(team_member['reports_to'])
                        if leader:
                            st.write(f"You report to: {leader['name']} ({leader['role']})")
            
            # Change password option
            st.subheader("Change Password")
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submitted = st.form_submit_button("Update Profile")
            if submitted:
                if new_password:
                    # Verify current password
                    if current_password != user.get('password_hash'):
                        st.error("Current password is incorrect.")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match.")
                    else:
                        # Update user with new information including password
                        updated_user = user.copy()
                        updated_user['name'] = full_name
                        updated_user['email'] = email
                        updated_user['password_hash'] = new_password
                        
                        if update_user(user['id'], updated_user):
                            st.success("Profile updated successfully!")
                        else:
                            st.error("Failed to update profile.")
                else:
                    # Update user without changing password
                    updated_user = user.copy()
                    updated_user['name'] = full_name
                    updated_user['email'] = email
                    
                    if update_user(user['id'], updated_user):
                        st.success("Profile updated successfully!")
                    else:
                        st.error("Failed to update profile.")
        
        # Logout button
        if st.button("Logout"):
            logout_user()
            st.rerun()
    
    with tasks_tab:
        st.subheader("My Tasks")
        
        # Different views for team leaders and members
        if not st.session_state.team_member_id:
            st.info("You don't have a linked team member profile. Please contact an administrator.")
        else:
            team_member = get_team_member(st.session_state.team_member_id)
            
            if team_member and team_member.get('is_team_leader', False):
                # Team leader view: show both personal tasks and team's tasks
                show_leader_task_view(team_member)
            elif team_member:
                # Regular team member view: show assigned tasks
                show_member_task_view(team_member)
            else:
                st.error("Could not retrieve your team member information.")

def show_leader_task_view(team_member):
    """Display task dashboard for team leaders"""
    if 'current_project_id' not in st.session_state or not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first.")
        return
    
    project_id = st.session_state.current_project_id
    
    # Tab options for different views
    view_tab, team_tab, approval_tab = st.tabs(["My Tasks", "Team Tasks", "Pending Approvals"])
    
    with view_tab:
        st.subheader("Tasks Assigned to Me")
        show_assigned_tasks(team_member['id'])
    
    with team_tab:
        st.subheader("My Team's Tasks")
        
        # Get team members who report to this leader
        from utils.data_management import get_team_members_by_leader, get_project_tasks
        team = get_team_members_by_leader(team_member['id'])
        
        if team:
            # Get all tasks for the project
            tasks = get_project_tasks(project_id)
            
            # Filter tasks assigned to team members
            team_member_ids = [m['id'] for m in team]
            team_tasks = []
            
            for task in tasks:
                if 'assigned_members' in task:
                    for member_id in task['assigned_members']:
                        if member_id in team_member_ids and task not in team_tasks:
                            team_tasks.append(task)
            
            if team_tasks:
                # Sort tasks by status and due date
                team_tasks.sort(key=lambda x: (x['status'] != 'In Progress', x['status'] != 'Not Started', x['end_date']))
                
                for task in team_tasks:
                    # Display task with assigned team members
                    assigned_members_str = ""
                    if 'assigned_members' in task:
                        assigned_names = []
                        for member_id in task['assigned_members']:
                            member = get_team_member(member_id)
                            if member and member['id'] in team_member_ids:
                                assigned_names.append(member['name'])
                        
                        if assigned_names:
                            assigned_members_str = ", ".join(assigned_names)
                    
                    with st.expander(f"{task['name']} - {task['status']} (Assigned to: {assigned_members_str})"):
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
                        st.progress(int(task['progress']) / 100)
                        
                        # Show subtasks if any
                        from utils.data_management import get_subtasks_by_parent
                        subtasks = get_subtasks_by_parent(task['id'])
                        
                        if subtasks:
                            st.subheader("Subtasks")
                            for subtask in subtasks:
                                st.write(f"- {subtask['name']} ({subtask['status']}, {subtask['progress']}% complete)")
                        
                        # Add subtask button
                        if st.button(f"Add Subtask for {task['name']}", key=f"add_subtask_{task['id']}"):
                            st.session_state.adding_subtask_for = task['id']
                            st.rerun()
            else:
                st.info("No tasks assigned to your team members yet.")
        else:
            st.info("You don't have any team members reporting to you.")
    
    with approval_tab:
        st.subheader("Tasks Pending Approval")
        
        # Get tasks awaiting approval
        from utils.data_management import get_tasks_awaiting_approval, approve_task, reject_task
        pending_tasks = get_tasks_awaiting_approval(project_id)
        
        # Filter to tasks where this leader is responsible
        leader_pending_tasks = []
        for task in pending_tasks:
            # Check if any team member is assigned to this task
            team_members = get_team_members_by_leader(team_member['id'])
            team_member_ids = [m['id'] for m in team_members]
            
            # Add leader's own ID
            team_member_ids.append(team_member['id'])
            
            if 'assigned_members' in task:
                for member_id in task['assigned_members']:
                    if member_id in team_member_ids:
                        leader_pending_tasks.append(task)
                        break
        
        if leader_pending_tasks:
            for task in leader_pending_tasks:
                with st.expander(f"📝 {task['name']} - Pending Approval"):
                    st.write(f"**Description:** {task['description']}")
                    st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
                    
                    # Show assigned members
                    if 'assigned_members' in task and task['assigned_members']:
                        assigned_names = []
                        for member_id in task['assigned_members']:
                            member = get_team_member(member_id)
                            if member:
                                assigned_names.append(f"{member['name']} ({member['role']})")
                        
                        if assigned_names:
                            st.write("**Assigned to:**")
                            for name in assigned_names:
                                st.write(f"- {name}")
                    
                    # Approval actions
                    st.subheader("Approval Decision")
                    approval_comment = st.text_area("Comments (optional)", key=f"comment_{task['id']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve", key=f"approve_{task['id']}"):
                            success = approve_task(task['id'], team_member['id'], approval_comment)
                            if success:
                                st.success("Task approved!")
                                st.rerun()
                            else:
                                st.error("Failed to approve task.")
                    
                    with col2:
                        if st.button("Request Changes", key=f"reject_{task['id']}"):
                            if not approval_comment:
                                st.error("Please provide comments explaining why changes are needed.")
                            else:
                                success = reject_task(task['id'], team_member['id'], approval_comment)
                                if success:
                                    st.success("Task change requested!")
                                    st.rerun()
                                else:
                                    st.error("Failed to request changes.")
        else:
            st.info("No tasks awaiting your approval.")

def show_member_task_view(team_member):
    """Display task dashboard for regular team members"""
    if 'current_project_id' not in st.session_state or not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first.")
        return
    
    project_id = st.session_state.current_project_id
    
    # Tab options for different views
    tasks_tab, subtasks_tab, reports_tab = st.tabs(["My Tasks", "My Subtasks", "My Reports"])
    
    with tasks_tab:
        st.subheader("Tasks Assigned to Me")
        show_assigned_tasks(team_member['id'])
    
    with subtasks_tab:
        st.subheader("My Subtasks")
        
        # Get subtasks assigned to this member
        from utils.data_management import get_subtasks_by_member
        subtasks = get_subtasks_by_member(team_member['id'])
        
        if subtasks:
            for subtask in subtasks:
                # Get parent task info
                from utils.data_management import get_task
                parent_task = get_task(subtask['parent_task_id'])
                parent_name = parent_task['name'] if parent_task else "Unknown Parent Task"
                
                with st.expander(f"{subtask['name']} (Part of: {parent_name})"):
                    st.write(f"**Description:** {subtask['description']}")
                    st.write(f"**Timeline:** {subtask['start_date']} to {subtask['end_date']}")
                    st.write(f"**Status:** {subtask['status']}")
                    st.progress(int(subtask['progress']) / 100)
                    
                    # Report submission
                    st.subheader("Submit Progress Report")
                    
                    with st.form(f"report_form_{subtask['id']}"):
                        progress = st.slider("Completion Percentage", 
                                            0, 100, 
                                            value=int(subtask['progress']),
                                            key=f"progress_{subtask['id']}")
                        
                        status_options = ["Not Started", "In Progress", "Completed", "Delayed"]
                        status = st.selectbox("Status", 
                                            options=status_options,
                                            index=status_options.index(subtask['status']) if subtask['status'] in status_options else 0,
                                            key=f"status_{subtask['id']}")
                        
                        report_content = st.text_area("Progress Report", 
                                                    value=subtask.get('completion_report', ''),
                                                    key=f"report_{subtask['id']}")
                        
                        submitted = st.form_submit_button("Submit Report")
                        if submitted:
                            from utils.data_management import submit_subtask_report
                            report_data = {
                                'content': report_content,
                                'status': status,
                                'progress': progress,
                                'submitted_by': team_member['id']
                            }
                            
                            success = submit_subtask_report(subtask['id'], report_data)
                            if success:
                                st.success("Report submitted successfully!")
                            else:
                                st.error("Failed to submit report.")
        else:
            st.info("You don't have any subtasks assigned to you.")
    
    with reports_tab:
        st.subheader("My Submitted Reports")
        
        # Get subtasks with submitted reports
        from utils.data_management import get_subtasks_by_member
        all_subtasks = get_subtasks_by_member(team_member['id'])
        reported_subtasks = [s for s in all_subtasks if s.get('completion_report')]
        
        if reported_subtasks:
            for subtask in reported_subtasks:
                report_date = subtask.get('completion_report_submitted_at', 'Unknown date')
                with st.expander(f"{subtask['name']} - Report submitted on {report_date}"):
                    st.write("**Report Content:**")
                    st.write(subtask.get('completion_report', 'No content'))
                    
                    st.write(f"**Status:** {subtask['status']}")
                    st.write(f"**Progress:** {subtask['progress']}%")
                    
                    # Show if approved
                    if subtask.get('approval_status') == 'Approved':
                        st.success("This subtask has been approved.")
                    elif subtask.get('approval_status') == 'Rejected':
                        st.error(f"This subtask requires changes: {subtask.get('rejection_reason', 'No reason provided')}")
                    else:
                        st.info("This subtask is pending approval.")
        else:
            st.info("You haven't submitted any reports yet.")

def show_assigned_tasks(member_id):
    """Display tasks assigned to a specific team member"""
    if 'current_project_id' not in st.session_state or not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first.")
        return
    
    project_id = st.session_state.current_project_id
    
    # Get tasks for the project
    from utils.data_management import get_project_tasks
    tasks = get_project_tasks(project_id)
    
    # Filter tasks assigned to this member
    assigned_tasks = []
    for task in tasks:
        if 'assigned_members' in task and member_id in task['assigned_members']:
            assigned_tasks.append(task)
    
    if assigned_tasks:
        # Sort tasks by status and due date
        assigned_tasks.sort(key=lambda x: (x['status'] != 'In Progress', x['status'] != 'Not Started', x['end_date']))
        
        for task in assigned_tasks:
            # Display task details
            with st.expander(f"{task['name']} - {task['status']}"):
                st.write(f"**Description:** {task['description']}")
                st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
                
                # Show approval status
                if 'approval_status' in task:
                    if task['approval_status'] == 'Approved':
                        st.success("This task has been approved")
                    elif task['approval_status'] == 'Pending Approval':
                        st.warning("This task is pending approval")
                    elif task['approval_status'] == 'Rejected':
                        st.error("This task requires changes")
                        if 'rejection_reason' in task:
                            st.write(f"**Reason:** {task['rejection_reason']}")
                
                # Show progress
                st.progress(int(task['progress']) / 100)
                
                # Show subtasks if any
                from utils.data_management import get_subtasks_by_parent
                subtasks = get_subtasks_by_parent(task['id'])
                
                if subtasks:
                    st.subheader("Subtasks")
                    for subtask in subtasks:
                        assigned_to = []
                        if 'assigned_members' in subtask:
                            for sub_member_id in subtask['assigned_members']:
                                member = get_team_member(sub_member_id)
                                if member:
                                    assigned_to.append(member['name'])
                        
                        assigned_str = f" (Assigned to: {', '.join(assigned_to)})" if assigned_to else ""
                        st.write(f"- {subtask['name']} - {subtask['status']}{assigned_str}, {subtask['progress']}% complete")
    else:
        st.info("You don't have any tasks assigned to you in this project.")

def logout_user():
    """Clear user session data"""
    # Reset all user-related session variables
    user_session_keys = [
        'user_id', 
        'username', 
        'user_name',
        'user_role', 
        'team_member_id', 
        'logged_in'
    ]
    
    for key in user_session_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Set logged_in to False explicitly
    st.session_state.logged_in = False
    
    # Force redirect to login page
    st.session_state.current_page = "User Account"