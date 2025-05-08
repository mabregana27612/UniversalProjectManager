import streamlit as st
import datetime
import pandas as pd
import numpy as np
from utils.data_management import (
    get_project, get_project_tasks, add_task, update_task, get_project_team, 
    get_team_member, get_project_team_leaders, get_team_members_by_leader,
    assign_task_to_team, get_tasks_awaiting_approval, approve_task, reject_task,
    get_dependent_tasks, analyze_schedule_impact
)
from utils.visualization import create_gantt_chart, create_burndown_chart

def show_timeline():
    st.title("📅 Project Timeline Management")
    
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
    
    # Display timeline image
    st.image("https://pixabay.com/get/g6ee063ae7b2531ddb934477a4f5e288732b61e7e1a093910d10a747ef4768279857c8a99f276444f1e232aed80de23c81081a444e25decc935cfdafb82e7adca_1280.jpg", 
             caption="Project Timeline", use_container_width=True)
    
    # Project timeline header
    st.subheader(f"Timeline for: {project['name']}")
    st.caption(f"Project duration: {project['start_date']} to {project['end_date']}")
    
    # Create tabs for Timeline View, Task Management, and Task Approval
    tab1, tab2, tab3 = st.tabs(["Timeline View", "Task Management", "Task Approval & Impact"])
    
    with tab1:
        # Timeline visualization
        if tasks:
            st.subheader("Gantt Chart")
            fig = create_gantt_chart(project_id, tasks)
            st.plotly_chart(fig, use_container_width=True)
            
            # Burndown chart
            st.subheader("Burndown Chart")
            burndown_fig = create_burndown_chart(project_id, tasks)
            if burndown_fig:
                st.plotly_chart(burndown_fig, use_container_width=True)
            else:
                st.info("Burndown chart will be available when tasks are added with start and end dates.")
        else:
            st.info("No tasks found. Add tasks in the Task Management tab to see the timeline.")
    
    with tab2:
        # Task management
        st.subheader("Task Management")
        
        # Create two columns for the layout
        task_list_col, task_form_col = st.columns([1, 1])
        
        with task_list_col:
            # Display existing tasks
            st.subheader("Current Tasks")
            
            if tasks:
                # Sort tasks by start date
                sorted_tasks = sorted(tasks, key=lambda x: x['start_date'])
                
                for task in sorted_tasks:
                    # Add a special icon or color for milestones
                    if task.get('is_milestone', False):
                        milestone_icon = "🏆 "  # Trophy icon for milestones
                        milestone_style = "background-color: #e6f3ff; padding: 10px; border-radius: 5px; border-left: 4px solid #4285f4;"
                    else:
                        milestone_icon = ""
                        milestone_style = ""
                        
                    # Format task title with optional milestone icon
                    task_title = f"{milestone_icon}{task['name']} ({task['status']})"
                    
                    with st.expander(task_title):
                        if milestone_style:
                            st.markdown(f'<div style="{milestone_style}"><strong>MILESTONE</strong></div>', unsafe_allow_html=True)
                            
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
                        
                        # Create a progress bar
                        progress_color = "green" if task['progress'] >= 75 else "orange" if task['progress'] >= 25 else "red"
                        st.markdown(f"""
                        <div style="margin-bottom: 10px;">
                            <strong>Progress:</strong> {task['progress']}%
                            <div style="background-color: #f0f0f0; border-radius: 3px; height: 20px; width: 100%;">
                                <div style="background-color: {progress_color}; width: {task['progress']}%; height: 100%; border-radius: 3px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display assigned team members grouped by teams if possible
                        if 'assigned_members' in task and task['assigned_members']:
                            st.write("**Assigned Team Members:**")
                            
                            # Get team leaders who are assigned to this task
                            assigned_leaders = []
                            for member_id in task['assigned_members']:
                                member = get_team_member(member_id)
                                if member and member.get('is_team_leader', False):
                                    assigned_leaders.append(member)
                            
                            # Display team leaders and their team members who are assigned
                            if assigned_leaders:
                                for leader in assigned_leaders:
                                    st.markdown(f"**Team: {leader['name']}'s Team**")
                                    st.write(f"- {leader['name']} (Team Leader - {leader['role']})")
                                    
                                    # Get team members of this leader
                                    if 'team_members' in leader and leader['team_members']:
                                        # Get team members, filtering out None values
                                        leader_team_members = []
                                        for m_id in leader['team_members']:
                                            member = get_team_member(m_id)
                                            if member:
                                                leader_team_members.append(member)
                                        
                                        # Only show team members who are assigned to this task
                                        for member in leader_team_members:
                                            if member['id'] in task['assigned_members']:
                                                st.write(f"  - {member['name']} ({member['role']})")
                                    
                                    st.markdown("---")
                            
                            # Display other assigned members who aren't part of a team
                            other_members = []
                            for member_id in task['assigned_members']:
                                member = get_team_member(member_id)
                                if member and not member.get('is_team_leader', False):
                                    # Check if member is already displayed as part of a team
                                    is_in_displayed_team = False
                                    for leader in assigned_leaders:
                                        if 'team_members' in leader and member_id in leader['team_members']:
                                            is_in_displayed_team = True
                                            break
                                    
                                    if not is_in_displayed_team:
                                        other_members.append(member)
                            
                            if other_members:
                                st.write("**Other Assigned Members:**")
                                for member in other_members:
                                    st.write(f"- {member['name']} ({member['role']})")
                        
                        # Edit button for task
                        if st.button(f"Edit Task #{task['id']}", key=f"edit_{task['id']}"):
                            st.session_state.editing_task_id = task['id']
                            st.rerun()
            else:
                st.info("No tasks defined. Create your first task!")
        
        with task_form_col:
            # Task creation/editing form
            editing_task = False
            current_task = {}
            
            if 'editing_task_id' in st.session_state and st.session_state.editing_task_id:
                st.subheader("Edit Task")
                editing_task = True
                # Find the task being edited
                for task in tasks:
                    if task['id'] == st.session_state.editing_task_id:
                        current_task = task
                        break
            else:
                st.subheader("Add New Task")
            
            # Task form
            task_name = st.text_input(
                "Task Name", 
                value=current_task.get('name', ''),
                key="task_name"
            )
            
            task_description = st.text_area(
                "Task Description", 
                value=current_task.get('description', ''),
                key="task_desc"
            )
            
            # Dates
            col1, col2 = st.columns(2)
            with col1:
                default_start = datetime.datetime.strptime(project['start_date'], '%Y-%m-%d')
                if 'start_date' in current_task:
                    default_start = datetime.datetime.strptime(current_task['start_date'], '%Y-%m-%d')
                
                task_start = st.date_input(
                    "Start Date", 
                    value=default_start,
                    min_value=datetime.datetime.strptime(project['start_date'], '%Y-%m-%d'),
                    max_value=datetime.datetime.strptime(project['end_date'], '%Y-%m-%d'),
                    key="task_start"
                )
            
            with col2:
                default_end = datetime.datetime.strptime(project['start_date'], '%Y-%m-%d') + datetime.timedelta(days=7)
                if 'end_date' in current_task:
                    default_end = datetime.datetime.strptime(current_task['end_date'], '%Y-%m-%d')
                
                task_end = st.date_input(
                    "End Date", 
                    value=default_end,
                    min_value=datetime.datetime.strptime(project['start_date'], '%Y-%m-%d'),
                    max_value=datetime.datetime.strptime(project['end_date'], '%Y-%m-%d'),
                    key="task_end"
                )
            
            # Task status
            task_status_options = ["Not Started", "In Progress", "Completed", "Delayed"]
            default_status_index = 0
            if 'status' in current_task and current_task['status'] in task_status_options:
                default_status_index = task_status_options.index(current_task['status'])
            
            task_status = st.selectbox(
                "Status", 
                task_status_options,
                index=default_status_index,
                key="task_status"
            )
            
            # Task progress
            task_progress = st.slider(
                "Progress (%)", 
                min_value=0, 
                max_value=100, 
                value=current_task.get('progress', 0),
                key="task_progress"
            )
            
            # Is milestone
            is_milestone = st.checkbox(
                "Mark as Milestone", 
                value=current_task.get('is_milestone', False),
                key="is_milestone"
            )
            
            # Requires approval
            requires_approval = st.checkbox(
                "Requires Approval Before Execution", 
                value=current_task.get('requires_approval', True),
                key="requires_approval"
            )
            
            # Dependencies (only show if there are other tasks)
            dependencies = []
            if tasks and not (editing_task and len(tasks) == 1):
                st.subheader("Dependencies")
                
                # Filter out the current task if editing
                available_tasks = [t for t in tasks if not (editing_task and t['id'] == st.session_state.editing_task_id)]
                
                if available_tasks:
                    for task in available_tasks:
                        if st.checkbox(
                            f"Depends on: {task['name']}", 
                            value=task['id'] in current_task.get('dependencies', []),
                            key=f"dep_{task['id']}"
                        ):
                            dependencies.append(task['id'])
                else:
                    st.info("No other tasks available for dependencies.")
                    
            # Team member assignment
            st.subheader("Assign Team Members")
            team = get_project_team(project_id)
            assigned_members = []
            
            # Get team leaders
            team_leaders = get_project_team_leaders(project_id)
            
            if team:
                # Get current assigned members
                current_assigned = current_task.get('assigned_members', [])
                
                # Assignment mode (individual or team-based)
                assignment_mode = st.radio(
                    "Assignment Type",
                    options=["Assign Individual Members", "Assign to Teams"],
                    index=0,
                    key="assignment_mode"
                )
                
                if assignment_mode == "Assign Individual Members":
                    # Individual assignment
                    for member in team:
                        if st.checkbox(
                            f"Assign: {member['name']} ({member['role']})",
                            value=member['id'] in current_assigned,
                            key=f"assign_{member['id']}"
                        ):
                            assigned_members.append(member['id'])
                else:
                    # Team-based assignment
                    if team_leaders:
                        for leader in team_leaders:
                            # Check if leader's entire team should be assigned
                            team_assigned = st.checkbox(
                                f"Assign Team: {leader['name']}'s Team",
                                value=False,
                                key=f"team_{leader['id']}"
                            )
                            
                            # Get team members
                            team_members = []
                            if 'team_members' in leader and leader['team_members']:
                                team_members = leader['team_members']
                                
                                # Get team members, filtering out None values
                                leader_team = []
                                for member_id in team_members:
                                    member = get_team_member(member_id)
                                    if member:
                                        leader_team.append(member)
                                
                                # Display team members with indentation
                                for member in leader_team:
                                    st.write(f"   - {member['name']} ({member['role']})")
                            
                            # If team is assigned, add all team members to assigned_members
                            if team_assigned:
                                # Add leader
                                if leader['id'] not in assigned_members:
                                    assigned_members.append(leader['id'])
                                
                                # Add all team members
                                for member_id in team_members:
                                    if member_id not in assigned_members:
                                        assigned_members.append(member_id)
                    else:
                        st.info("No team leaders defined. Designate team leaders in the Team Management section.")
                
                # If no members assigned yet, show warning
                if not assigned_members:
                    st.warning("No team members assigned to this task yet.")
            else:
                st.info("No team members available. Add team members in the Team Management section.")
            
            # Submit button
            if editing_task:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Task"):
                        if not task_name:
                            st.error("Task name is required!")
                        elif task_start > task_end:
                            st.error("End date must be after start date!")
                        else:
                            task_data = {
                                'name': task_name,
                                'description': task_description,
                                'start_date': task_start.strftime('%Y-%m-%d'),
                                'end_date': task_end.strftime('%Y-%m-%d'),
                                'status': task_status,
                                'progress': task_progress,
                                'dependencies': dependencies,
                                'is_milestone': is_milestone,
                                'requires_approval': requires_approval,
                                'assigned_members': assigned_members
                            }
                            
                            success = update_task(st.session_state.editing_task_id, task_data)
                            if success:
                                st.success("Task updated successfully!")
                                st.session_state.editing_task_id = None
                                st.rerun()
                            else:
                                st.error("Failed to update task!")
                
                with col2:
                    if st.button("Cancel Editing"):
                        st.session_state.editing_task_id = None
                        st.rerun()
            else:
                if st.button("Add Task"):
                    if not task_name:
                        st.error("Task name is required!")
                    elif task_start > task_end:
                        st.error("End date must be after start date!")
                    else:
                        task_data = {
                            'project_id': project_id,
                            'name': task_name,
                            'description': task_description,
                            'start_date': task_start.strftime('%Y-%m-%d'),
                            'end_date': task_end.strftime('%Y-%m-%d'),
                            'status': task_status,
                            'progress': task_progress,
                            'dependencies': dependencies,
                            'is_milestone': is_milestone,
                            'requires_approval': requires_approval,
                            'assigned_members': assigned_members
                        }
                        
                        task_id = add_task(task_data)
                        if task_id:
                            st.success(f"Task added with ID: {task_id}")
                            st.rerun()
                        else:
                            st.error("Failed to add task!")
    
    # Task approval and dependency impact analysis tab
    with tab3:
        st.subheader("Task Approval & Change Management")
        
        # Create two columns
        approval_col, impact_col = st.columns([1, 1])
        
        with approval_col:
            st.subheader("Tasks Requiring Approval")
            pending_tasks = get_tasks_awaiting_approval(project_id)
            
            if pending_tasks:
                for task in pending_tasks:
                    with st.expander(f"📝 {task['name']} - Pending Approval"):
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Timeline:** {task['start_date']} to {task['end_date']}")
                        
                        # Display assigned team members
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
                                # In a real app, you'd use the current user's ID
                                approver_id = "current_user"
                                success = approve_task(task['id'], approver_id, approval_comment)
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
                                    # In a real app, you'd use the current user's ID
                                    reviewer_id = "current_user"
                                    success = reject_task(task['id'], reviewer_id, approval_comment)
                                    if success:
                                        st.success("Task change requested!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to request changes.")
            else:
                st.info("No tasks are currently awaiting approval.")
        
        with impact_col:
            st.subheader("Dependency Impact Analysis")
            st.write("Analyze how changes to a task will impact dependent tasks.")
            
            # Task selection for impact analysis
            if tasks:
                selected_task_id = st.selectbox(
                    "Select a task to analyze potential changes:",
                    options=[t['id'] for t in tasks],
                    format_func=lambda x: next((t['name'] for t in tasks if t['id'] == x), "Unknown"),
                    key="impact_task_id"
                )
                
                # Get the selected task
                selected_task = next((t for t in tasks if t['id'] == selected_task_id), None)
                
                if selected_task:
                    st.write(f"Current end date: {selected_task['end_date']}")
                    
                    # New end date picker
                    new_end_date = st.date_input(
                        "Proposed new end date:",
                        value=datetime.datetime.strptime(selected_task['end_date'], '%Y-%m-%d'),
                        min_value=datetime.datetime.strptime(project['start_date'], '%Y-%m-%d'),
                        max_value=datetime.datetime.strptime(project['end_date'], '%Y-%m-%d'),
                        key="impact_end_date"
                    )
                    
                    # Convert to string format for comparison
                    new_end_date_str = new_end_date.strftime('%Y-%m-%d')
                    
                    if new_end_date_str != selected_task['end_date']:
                        # Analyze impact
                        if st.button("Analyze Impact"):
                            impacts = analyze_schedule_impact(selected_task_id, new_end_date_str)
                            
                            if impacts:
                                st.subheader("Tasks Impacted:")
                                st.write(f"Proposed change will affect {len(impacts)} dependent task(s).")
                                
                                for impact in impacts:
                                    with st.expander(f"⚠️ {impact['task_name']} will be affected"):
                                        st.write(f"**Current timeline:** {impact['current_start']} to {impact['current_end']}")
                                        st.write(f"**Suggested new timeline:** {impact['suggested_start']} to {impact['suggested_end']}")
                                        st.write(f"**Days shifted:** {impact['impact_days']}")
                                        
                                        if impact['impact_days'] > 0:
                                            st.warning(f"⚠️ This task will be delayed by {impact['impact_days']} days")
                                        elif impact['impact_days'] < 0:
                                            st.success(f"✅ This task can start {abs(impact['impact_days'])} days earlier")
                                        
                                # Option to apply changes
                                if st.button("Apply All Changes"):
                                    st.warning("This would update all dependent tasks. This feature is coming soon.")
                            else:
                                st.success("No dependent tasks will be affected by this change.")
                    else:
                        st.info("Change the end date to see potential impacts on dependent tasks.")
            else:
                st.info("No tasks available for impact analysis.")
                
            st.markdown("""
            ### About Impact Analysis
            
            The impact analysis tool helps visualize how changes to one task will affect other dependent tasks in the project timeline.
            
            When a task's timeline changes:
            - Tasks that depend on it may need to be rescheduled
            - Project completion dates may be affected
            - Resource allocation might need adjustments
            
            Use this tool before approving timeline changes to understand the full impact on your project.
            """)

    # Timeline best practices
    with st.expander("Timeline Management Tips"):
        st.markdown("""
        ### Timeline Management Best Practices
        
        1. **Break Down Tasks**: Divide large tasks into smaller, manageable pieces.
        2. **Set Realistic Deadlines**: Allow sufficient time for task completion.
        3. **Identify Dependencies**: Clearly mark which tasks depend on others.
        4. **Track Milestones**: Use milestones to mark important checkpoints.
        5. **Update Regularly**: Keep the timeline current with actual progress.
        6. **Buffer Time**: Include contingency time for unexpected delays.
        7. **Review & Approval**: Have critical tasks reviewed by leadership before execution.
        8. **Analyze Changes**: Always check dependency impacts before changing task timelines.
        
        Well-managed timelines help keep projects on track and provide clear visibility into project progress.
        """)
