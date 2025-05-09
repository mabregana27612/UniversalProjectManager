import streamlit as st
import datetime
from utils.data_management import (
    get_project, get_task, get_project_tasks, get_subtasks_by_parent,
    get_subtask, add_subtask, update_subtask, delete_subtask,
    get_team_member, get_project_team, submit_subtask_report,
    update_parent_task_progress, check_task_meeting_requirement
)

def show_subtasks():
    st.title("🔄 Subtask Management")
    
    # Check if a project is selected
    if not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first!")
        return
    
    # Get project and tasks
    project_id = st.session_state.current_project_id
    project = get_project(project_id)
    tasks = get_project_tasks(project_id)
    
    if not project:
        st.error("Project not found!")
        return
    
    st.subheader(f"Subtasks for Project: {project['name']}")
    
    # Create tabs
    list_tab, create_tab, report_tab = st.tabs(["View Subtasks", "Create Subtasks", "Subtask Reports"])
    
    with list_tab:
        show_subtasks_list(tasks)
    
    with create_tab:
        show_subtask_creation(tasks, project_id)
    
    with report_tab:
        show_subtask_reports(tasks)

def show_subtasks_list(tasks):
    """Display all tasks and their subtasks"""
    if not tasks:
        st.info("No tasks found for this project. Create tasks first.")
        return
    
    # Group tasks by status
    in_progress = [t for t in tasks if t.get('status') == 'In Progress']
    not_started = [t for t in tasks if t.get('status') == 'Not Started']
    completed = [t for t in tasks if t.get('status') == 'Completed']
    other = [t for t in tasks if t.get('status') not in ['In Progress', 'Not Started', 'Completed']]
    
    # Display tasks and subtasks by status
    if in_progress:
        st.subheader("In Progress")
        for task in in_progress:
            display_task_with_subtasks(task)
    
    if not_started:
        st.subheader("Not Started")
        for task in not_started:
            display_task_with_subtasks(task)
    
    if completed:
        st.subheader("Completed")
        for task in completed:
            display_task_with_subtasks(task)
    
    if other:
        st.subheader("Other Status")
        for task in other:
            display_task_with_subtasks(task)

def display_task_with_subtasks(task):
    """Display a task and its subtasks"""
    # Task name with progress
    with st.expander(f"{task['name']} ({task.get('progress', 0)}% complete)"):
        st.write(f"**Description:** {task['description']}")
        st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
        st.write(f"**Status:** {task['status']}")
        
        # Get assigned team members
        if 'assigned_members' in task and task['assigned_members']:
            assigned_names = []
            for member_id in task['assigned_members']:
                member = get_team_member(member_id)
                if member:
                    assigned_names.append(f"{member['name']} ({member['role']})")
            
            if assigned_names:
                st.write("**Assigned to:**")
                st.write(", ".join(assigned_names))
        
        # Progress bar
        st.progress(int(task.get('progress', 0)) / 100)
        
        # Display subtasks
        subtasks = get_subtasks_by_parent(task['id'])
        if subtasks:
            st.subheader("Subtasks")
            
            # Create a table of subtasks
            data = []
            for subtask in subtasks:
                # Get assigned members for this subtask
                assigned_names = []
                if 'assigned_members' in subtask and subtask['assigned_members']:
                    for member_id in subtask['assigned_members']:
                        member = get_team_member(member_id)
                        if member:
                            assigned_names.append(member['name'])
                
                # Format for the table
                data.append({
                    "ID": subtask['id'],
                    "Name": subtask['name'],
                    "Status": subtask['status'],
                    "Progress": f"{subtask.get('progress', 0)}%",
                    "Assigned To": ", ".join(assigned_names) if assigned_names else "Unassigned",
                    "Timeline": f"{subtask['start_date']} to {subtask['end_date']}"
                })
            
            # Display as a dataframe
            import pandas as pd
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Option to view details of a subtask
            selected_subtask_id = st.selectbox(
                "Select a subtask to view details",
                options=[s['id'] for s in subtasks],
                format_func=lambda x: next((s['name'] for s in subtasks if s['id'] == x), "Unknown"),
                key=f"view_subtask_{task['id']}"
            )
            
            if st.button(f"View Subtask Details", key=f"view_subtask_btn_{task['id']}"):
                st.session_state.viewing_subtask_id = selected_subtask_id
                st.rerun()
            
            # Display subtask details if selected
            if 'viewing_subtask_id' in st.session_state:
                subtask = get_subtask(st.session_state.viewing_subtask_id)
                if subtask and subtask['parent_task_id'] == task['id']:
                    st.subheader(f"Subtask: {subtask['name']}")
                    st.write(f"**Description:** {subtask['description']}")
                    st.write(f"**Timeline:** {subtask['start_date']} to {subtask['end_date']}")
                    st.write(f"**Status:** {subtask['status']}")
                    st.write(f"**Progress:** {subtask.get('progress', 0)}%")
                    
                    # Show approval status
                    if subtask.get('approval_status') == 'Approved':
                        st.success("This subtask has been approved")
                    elif subtask.get('approval_status') == 'Pending Approval':
                        st.warning("This subtask is pending approval")
                    elif subtask.get('approval_status') == 'Rejected':
                        st.error("This subtask requires changes")
                    
                    # Show assigned members
                    if 'assigned_members' in subtask and subtask['assigned_members']:
                        assigned_names = []
                        for member_id in subtask['assigned_members']:
                            member = get_team_member(member_id)
                            if member:
                                assigned_names.append(f"{member['name']} ({member['role']})")
                        
                        if assigned_names:
                            st.write("**Assigned to:**")
                            for name in assigned_names:
                                st.write(f"- {name}")
                    
                    # Show completion report if available
                    if subtask.get('completion_report'):
                        st.subheader("Completion Report")
                        st.write(subtask['completion_report'])
                        if subtask.get('completion_report_submitted_at'):
                            st.caption(f"Submitted on {subtask['completion_report_submitted_at']}")
                    
                    # Option to delete subtask
                    if st.button("Delete This Subtask", key=f"delete_subtask_{subtask['id']}"):
                        if delete_subtask(subtask['id']):
                            st.success("Subtask deleted successfully!")
                            # Clean up session state
                            if 'viewing_subtask_id' in st.session_state:
                                del st.session_state.viewing_subtask_id
                            st.rerun()
                        else:
                            st.error("Failed to delete subtask.")
        else:
            st.info("No subtasks defined for this task yet.")
            
            # Check if user has permission to add subtasks
            can_add_subtasks = False
            if st.session_state.logged_in:
                # Check if user is a team leader or admin
                is_leader = False
                if 'team_member_id' in st.session_state and st.session_state.team_member_id:
                    team_member = get_team_member(st.session_state.team_member_id)
                    if team_member and team_member.get('is_team_leader', False):
                        is_leader = True
                
                is_admin = st.session_state.user_role == 'admin'
                can_add_subtasks = is_leader or is_admin
            
            # Only show button if user has permission
            if can_add_subtasks:
                # Button to add a subtask
                if st.button(f"Add Subtask to {task['name']}", key=f"add_subtask_{task['id']}"):
                    st.session_state.adding_subtask_to = task['id']
                    st.rerun()
            else:
                st.info("Only team leaders and administrators can create subtasks after team planning meetings.")

def show_subtask_creation(tasks, project_id):
    """Interface for creating new subtasks"""
    if not tasks:
        st.info("No tasks available. Create tasks first before adding subtasks.")
        return
    
    # Check if user is logged in and has appropriate permissions
    if not st.session_state.logged_in:
        st.warning("Please log in to create subtasks.")
        return
    
    # Check if user is a team leader or admin
    is_leader = False
    if 'team_member_id' in st.session_state and st.session_state.team_member_id:
        team_member = get_team_member(st.session_state.team_member_id)
        if team_member and team_member.get('is_team_leader', False):
            is_leader = True
    
    is_admin = st.session_state.user_role == 'admin'
    
    if not (is_leader or is_admin):
        st.warning("Only team leaders and administrators can create subtasks. Consider scheduling a team meeting to discuss task distribution.")
        
        # Add a button to navigate to the Team Meetings page
        if st.button("Schedule a Team Meeting"):
            st.session_state.current_page = "Team Meetings"
            st.rerun()
        return
    
    st.subheader("Create a New Subtask")
    
    # Show guidelines for creating subtasks
    show_subtask_guidelines()
    
    # Choose parent task
    parent_task_id = None
    parent_task = None
    
    # If we're redirected from a task detail page
    if 'adding_subtask_to' in st.session_state:
        parent_task_id = st.session_state.adding_subtask_to
        parent_task = get_task(parent_task_id)
        if parent_task:
            st.info(f"Adding subtask to: {parent_task['name']}")
            # Check if the task is completed
            if parent_task.get('status') == 'Completed':
                st.warning("⚠️ This task is already marked as completed. Subtasks should typically be created for in-progress tasks.")
                if not st.checkbox("I understand, but still want to add a subtask to this completed task"):
                    return
        else:
            st.error("Selected parent task not found.")
            if 'adding_subtask_to' in st.session_state:
                del st.session_state.adding_subtask_to
            return
    else:
        # Filter out completed tasks by default
        incomplete_tasks = [t for t in tasks if t.get('status') != 'Completed']
        show_all_tasks = st.checkbox("Show completed tasks as well", value=False)
        
        filtered_tasks = tasks if show_all_tasks else incomplete_tasks
        
        if not filtered_tasks:
            if show_all_tasks:
                st.warning("No tasks available for creating subtasks.")
            else:
                st.warning("No incomplete tasks available. All tasks are marked as completed.")
                st.info("Check 'Show completed tasks as well' if you need to add subtasks to a completed task.")
            return
            
        # Select parent task
        task_options = [(t['id'], f"{t['name']} ({t['status']})") for t in filtered_tasks]
        selected_task = st.selectbox(
            "Select parent task",
            options=[t[0] for t in task_options],
            format_func=lambda x: next((t[1] for t in task_options if t[0] == x), "Unknown"),
            key="parent_task_selection"
        )
        parent_task_id = selected_task
        parent_task = get_task(parent_task_id)
        
        if not parent_task:
            st.error("Selected parent task not found. Please select a valid task.")
            return
        
        # Display parent task details for reference
        with st.expander("Parent Task Details", expanded=True):
            st.write(f"**Task:** {parent_task['name']}")
            st.write(f"**Description:** {parent_task['description']}")
            st.write(f"**Timeline:** {parent_task['start_date']} to {parent_task['end_date']}")
            st.write(f"**Status:** {parent_task['status']}")
            st.write(f"**Progress:** {parent_task.get('progress', 0)}%")
            
            # Show assigned team members
            if 'assigned_members' in parent_task and parent_task['assigned_members']:
                assigned_names = []
                for member_id in parent_task['assigned_members']:
                    member = get_team_member(member_id)
                    if member:
                        assigned_names.append(f"{member['name']} ({member['role']})")
                
                if assigned_names:
                    st.write("**Assigned to:**")
                    for name in assigned_names:
                        st.write(f"- {name}")
    
    # Subtask form
    with st.form("subtask_form"):
        subtask_name = st.text_input("Subtask Name")
        subtask_description = st.text_area("Subtask Description")
        
        # Use parent task dates as defaults
        col1, col2 = st.columns(2)
        
        # Ensure parent_task is not None before accessing its fields
        if parent_task and 'start_date' in parent_task and 'end_date' in parent_task:
            try:
                default_start = datetime.datetime.strptime(parent_task['start_date'], '%Y-%m-%d')
                default_end = datetime.datetime.strptime(parent_task['end_date'], '%Y-%m-%d')
                
                with col1:
                    subtask_start = st.date_input(
                        "Start Date",
                        value=default_start,
                        min_value=default_start,
                        max_value=default_end
                    )
                
                with col2:
                    subtask_end = st.date_input(
                        "End Date",
                        value=default_end,
                        min_value=default_start,
                        max_value=default_end
                    )
            except (ValueError, TypeError):
                st.error("Invalid date format in parent task. Using today's date as default.")
                today = datetime.datetime.now()
                with col1:
                    subtask_start = st.date_input("Start Date", value=today)
                with col2:
                    subtask_end = st.date_input("End Date", value=today + datetime.timedelta(days=7))
        else:
            # Use today's date as default if parent task dates are not available
            today = datetime.datetime.now()
            with col1:
                subtask_start = st.date_input("Start Date", value=today)
            with col2:
                subtask_end = st.date_input("End Date", value=today + datetime.timedelta(days=7))
        
        # Status and progress
        status_options = ["Not Started", "In Progress", "Completed", "Delayed"]
        subtask_status = st.selectbox("Status", options=status_options, index=0)
        
        subtask_progress = st.slider("Progress (%)", min_value=0, max_value=100, value=0)
        
        # Requires approval
        requires_approval = st.checkbox("Requires Approval", value=True)
        
        # Assign team members
        st.subheader("Assign Team Members")
        
        # Get team members from parent task
        team_members = []
        if parent_task and isinstance(parent_task, dict) and 'assigned_members' in parent_task and parent_task['assigned_members']:
            for member_id in parent_task['assigned_members']:
                member = get_team_member(member_id)
                if member:
                    team_members.append(member)
        
        assigned_members = []
        if team_members:
            st.write("Select from parent task team members:")
            for member in team_members:
                if st.checkbox(
                    f"{member['name']} ({member['role']})",
                    key=f"member_{member['id']}"
                ):
                    assigned_members.append(member['id'])
        
        # Also allow selection from other project team members
        other_members = get_project_team(project_id)
        other_members = [m for m in other_members if not any(tm['id'] == m['id'] for tm in team_members)]
        
        if other_members:
            st.write("Select from other project team members:")
            for member in other_members:
                if st.checkbox(
                    f"{member['name']} ({member['role']})",
                    key=f"other_member_{member['id']}"
                ):
                    assigned_members.append(member['id'])
        
        # Submit button
        submitted = st.form_submit_button("Create Subtask")
        if submitted:
            if not subtask_name:
                st.error("Subtask name is required!")
            elif subtask_start > subtask_end:
                st.error("End date must be after start date!")
            else:
                # Check if team meeting requirement is met
                has_team_meeting = check_task_meeting_requirement(parent_task_id)
                
                if not has_team_meeting:
                    if st.checkbox("This task hasn't had a completed team meeting. A team meeting is recommended before creating subtasks to ensure proper coordination. Continue anyway?"):
                        st.info("Consider scheduling a team meeting for better coordination.")
                    else:
                        st.warning("Please schedule a team meeting first")
                        if st.button("Go to Team Meetings"):
                            st.session_state.current_page = "Team Meetings"
                            st.rerun()
                        return
                
                # Create subtask
                subtask_data = {
                    'parent_task_id': parent_task_id,
                    'name': subtask_name,
                    'description': subtask_description,
                    'start_date': subtask_start.strftime('%Y-%m-%d'),
                    'end_date': subtask_end.strftime('%Y-%m-%d'),
                    'status': subtask_status,
                    'progress': subtask_progress,
                    'requires_approval': requires_approval,
                    'assigned_members': assigned_members,
                    'created_by': st.session_state.get('user_id', None)  # Store who created the subtask
                }
                
                subtask_id = add_subtask(subtask_data)
                if subtask_id:
                    st.success(f"Subtask created successfully!")
                    
                    # Clear form and redirect to view
                    if 'adding_subtask_to' in st.session_state:
                        del st.session_state.adding_subtask_to
                    
                    st.rerun()
                else:
                    st.error("Failed to create subtask.")

def show_subtask_reports(tasks):
    """Display completion reports for subtasks"""
    st.subheader("Subtask Completion Reports")
    
    # Find all tasks with subtasks
    tasks_with_subtasks = []
    for task in tasks:
        subtasks = get_subtasks_by_parent(task['id'])
        if subtasks:
            tasks_with_subtasks.append((task, subtasks))
    
    if not tasks_with_subtasks:
        st.info("No subtasks with reports found.")
        return
    
    # Display reports grouped by parent task
    for task, subtasks in tasks_with_subtasks:
        # Filter subtasks that have completion reports
        reported_subtasks = [s for s in subtasks if s.get('completion_report')]
        
        if reported_subtasks:
            with st.expander(f"Task: {task['name']} ({len(reported_subtasks)} reports)"):
                for subtask in reported_subtasks:
                    report_date = subtask.get('completion_report_submitted_at', 'Unknown date')
                    submitter_id = subtask.get('completion_report_submitted_by')
                    submitter = "Unknown" if not submitter_id else get_team_member(submitter_id)
                    submitter_name = submitter['name'] if isinstance(submitter, dict) else "Unknown"
                    
                    st.markdown(f"### Subtask: {subtask['name']}")
                    st.write(f"**Reported by:** {submitter_name}")
                    st.write(f"**Date:** {report_date}")
                    st.write(f"**Status:** {subtask['status']}")
                    st.write(f"**Progress:** {subtask.get('progress', 0)}%")
                    
                    st.markdown("**Report Content:**")
                    st.markdown(f"```\n{subtask.get('completion_report', 'No content')}\n```")
                    
                    # Show approval status
                    if subtask.get('approval_status') == 'Approved':
                        st.success("This report has been approved")
                    elif subtask.get('approval_status') == 'Pending Approval':
                        st.warning("This report is pending approval")
                        
                        # For leaders - add approval buttons
                        if ('user_role' in st.session_state and st.session_state.user_role in ['admin', 'team_leader']) and \
                           ('team_member_id' in st.session_state):
                            
                            # Check if this leader is responsible for this subtask
                            team_member_id = st.session_state.team_member_id
                            team_member = get_team_member(team_member_id)
                            
                            if team_member and team_member.get('is_team_leader', False):
                                approval_comment = st.text_area("Approval Comments", key=f"approve_comment_{subtask['id']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Approve Report", key=f"approve_report_{subtask['id']}"):
                                        # Update subtask approval status
                                        subtask_copy = dict(subtask)
                                        subtask_copy['approval_status'] = 'Approved'
                                        subtask_copy['approved_by'] = team_member_id
                                        subtask_copy['approval_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        subtask_copy['approval_comments'] = approval_comment
                                        
                                        if update_subtask(subtask['id'], subtask_copy):
                                            st.success("Report approved!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to approve report.")
                                
                                with col2:
                                    if st.button("Request Changes", key=f"reject_report_{subtask['id']}"):
                                        if not approval_comment:
                                            st.error("Please provide comments explaining why changes are needed.")
                                        else:
                                            # Update subtask to rejected status
                                            subtask_copy = dict(subtask)
                                            subtask_copy['approval_status'] = 'Rejected'
                                            subtask_copy['reviewed_by'] = team_member_id
                                            subtask_copy['rejection_reason'] = approval_comment
                                            subtask_copy['review_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            
                                            if update_subtask(subtask['id'], subtask_copy):
                                                st.success("Change request sent!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to request changes.")
                    
                    elif subtask.get('approval_status') == 'Rejected':
                        st.error(f"This report requires changes: {subtask.get('rejection_reason', 'No reason provided')}")
                    
                    st.markdown("---")
        else:
            continue  # Skip tasks without any reported subtasks

# Helper function to display requirements for creating subtasks
def show_subtask_guidelines():
    with st.expander("Guidelines for Creating Subtasks"):
        st.markdown("""
        ### Best Practices for Creating Subtasks
        
        1. **Break down the parent task** into logical, manageable pieces.
        2. **Assign clear ownership** to each subtask.
        3. **Set realistic timelines** that fit within the parent task's duration.
        4. **Be specific** about what needs to be accomplished.
        5. **Update progress regularly** to keep the project timeline accurate.
        
        Good subtasks are specific, measurable, and have a clear definition of completion.
        """)