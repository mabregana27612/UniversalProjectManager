"""
Page for managing change requests for tasks and subtasks
"""

import streamlit as st
import datetime
from utils.change_request import (
    create_change_request, get_change_requests, get_change_request,
    approve_change_request, reject_change_request, get_user_change_requests
)
from utils.database import (
    get_task, get_subtask, get_project, get_user_by_id,
    get_team_member, model_to_dict
)
from utils.data_management import can_access_project, can_access_task

def show_change_requests():
    """Display change request management interface"""
    st.title("Change Request Management")
    
    # Check if user is logged in
    if "user" not in st.session_state:
        st.warning("Please log in to access this page.")
        return
    
    # Create tabs for different views
    tabs = st.tabs(["My Change Requests", "Pending Approvals", "Create Change Request"])
    
    with tabs[0]:
        show_my_change_requests()
    
    with tabs[1]:
        show_pending_approvals()
    
    with tabs[2]:
        show_create_change_request()

def show_my_change_requests():
    """Display change requests created by or affecting the current user"""
    st.header("My Change Requests")
    
    user_id = st.session_state.user["id"]
    change_requests = get_user_change_requests(user_id)
    
    if not change_requests:
        st.info("You don't have any change requests.")
        return
    
    # Display change requests in an expander per request
    for request in change_requests:
        # Determine if this is a task or subtask request
        if request["task_id"]:
            item_type = "Task"
            item_id = request["task_id"]
            item = get_task(item_id)
            if not item:
                continue
            project = get_project(item["project_id"])
        else:
            item_type = "Subtask"
            item_id = request["subtask_id"]
            item = get_subtask(item_id)
            if not item:
                continue
            parent_task = get_task(item["parent_task_id"])
            if not parent_task:
                continue
            project = get_project(parent_task["project_id"])
        
        # Get requester info
        requester = get_user_by_id(request["requested_by"])
        requester_name = requester["name"] if requester else "Unknown"
        
        # Format status with color
        status = request["status"]
        if status == "Pending":
            status_html = f"<span style='color:orange;'>{status}</span>"
        elif status == "Approved":
            status_html = f"<span style='color:green;'>{status}</span>"
        else:  # Rejected
            status_html = f"<span style='color:red;'>{status}</span>"
        
        # Display expander for each change request
        with st.expander(f"{item_type}: {item['name']} - Status: {request['status']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Project:** {project['name']}")
                st.markdown(f"**{item_type}:** {item['name']}")
                st.markdown(f"**Requested by:** {requester_name}")
                st.markdown(f"**Requested at:** {request['requested_at']}")
                st.markdown(f"**Status:** {status_html}", unsafe_allow_html=True)

            with col2:
                if request["review_date"]:
                    reviewer = get_user_by_id(request["reviewed_by"])
                    reviewer_name = reviewer["name"] if reviewer else "Unknown"
                    st.markdown(f"**Reviewed by:** {reviewer_name}")
                    st.markdown(f"**Review date:** {request['review_date']}")
                
                if request["requires_meeting"]:
                    st.markdown("**Requires meeting:** Yes")
                    
                    if request["meeting_id"]:
                        st.markdown(f"**Meeting ID:** {request['meeting_id']}")
            
            # Show proposed changes
            st.subheader("Proposed Changes")
            
            # Format changes as a table
            changes = []
            for key, value in request["proposed_changes"].items():
                current_value = request["current_data"].get(key)
                changes.append({
                    "Field": key,
                    "Current Value": str(current_value),
                    "New Value": str(value)
                })
            
            if changes:
                st.table(changes)
            else:
                st.info("No changes specified.")
            
            # Show reviewer comments if available
            if request["review_comments"]:
                st.subheader("Review Comments")
                st.write(request["review_comments"])

def show_pending_approvals():
    """Display pending change requests that the current user can approve"""
    st.header("Pending Approvals")
    
    user_id = st.session_state.user["id"]
    user_role = st.session_state.user["role"]
    
    # Only team leaders and admins can approve change requests
    if user_role not in ["team_leader", "admin"]:
        st.info("Only team leaders and administrators can approve change requests.")
        return
    
    # Get all pending requests
    pending_requests = get_change_requests(status="Pending")
    
    if not pending_requests:
        st.info("There are no pending change requests.")
        return
    
    # Filter requests that the user has permission to approve
    team_member_id = st.session_state.user.get("team_member_id")
    approvable_requests = []
    
    for request in pending_requests:
        # Get the associated item
        if request["task_id"]:
            item_type = "Task"
            item_id = request["task_id"]
            item = get_task(item_id)
            if not item:
                continue
                
            project_id = item["project_id"]
        else:
            item_type = "Subtask"
            item_id = request["subtask_id"]
            item = get_subtask(item_id)
            if not item:
                continue
                
            parent_task = get_task(item["parent_task_id"])
            if not parent_task:
                continue
                
            project_id = parent_task["project_id"]
        
        # Check if user has access to the project
        if user_role == "admin" or can_access_project(user_id, project_id):
            # For team leaders, check if they are responsible for the task or team members
            if user_role == "team_leader" and team_member_id:
                # Check if user is a team leader for any of the assigned members
                if "assigned_members" in item and item["assigned_members"]:
                    is_leader_for_members = False
                    for member_id in item["assigned_members"]:
                        member = get_team_member(member_id)
                        if member and member.get("reports_to") == team_member_id:
                            is_leader_for_members = True
                            break
                    
                    if is_leader_for_members:
                        approvable_requests.append(request)
                        continue
            else:
                # Admins can approve all requests
                approvable_requests.append(request)
    
    if not approvable_requests:
        st.info("There are no pending change requests that you can approve.")
        return
    
    # Display approvable requests
    for request in approvable_requests:
        # Get item details
        if request["task_id"]:
            item_type = "Task"
            item_id = request["task_id"]
            item = get_task(item_id)
            project = get_project(item["project_id"])
        else:
            item_type = "Subtask"
            item_id = request["subtask_id"]
            item = get_subtask(item_id)
            parent_task = get_task(item["parent_task_id"])
            project = get_project(parent_task["project_id"])
        
        # Get requester info
        requester = get_user_by_id(request["requested_by"])
        requester_name = requester["name"] if requester else "Unknown"
        
        # Display expander for each change request
        with st.expander(f"{item_type}: {item['name']} - Project: {project['name']}"):
            st.markdown(f"**Requested by:** {requester_name}")
            st.markdown(f"**Requested at:** {request['requested_at']}")
            
            if request["requires_meeting"]:
                st.markdown("**Requires meeting:** Yes")
                
            # Display change reason if available
            if request.get("change_reason"):
                st.subheader("Reason for Change")
                st.markdown(request["change_reason"])
                
            # Display impact analysis if available
            if request.get("impact_analysis"):
                st.subheader("Impact Analysis")
                st.markdown(request["impact_analysis"])
            
            # Show proposed changes
            st.subheader("Proposed Changes")
            
            # Format changes as a table
            changes = []
            for key, value in request["proposed_changes"].items():
                current_value = request["current_data"].get(key)
                changes.append({
                    "Field": key,
                    "Current Value": str(current_value),
                    "New Value": str(value)
                })
            
            if changes:
                st.table(changes)
            else:
                st.info("No changes specified.")
            
            # Add approval/rejection form
            st.subheader("Review")
            
            with st.form(f"review_form_{request['id']}"):
                comments = st.text_area("Comments", key=f"comments_{request['id']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    approve_btn = st.form_submit_button("Approve")
                
                with col2:
                    reject_btn = st.form_submit_button("Reject")
                
                if approve_btn:
                    result = approve_change_request(request["id"], user_id, comments)
                    if result:
                        st.success("Change request approved!")
                        st.rerun()
                    else:
                        st.error("Failed to approve change request. Please try again.")
                
                if reject_btn:
                    result = reject_change_request(request["id"], user_id, comments)
                    if result:
                        st.success("Change request rejected!")
                        st.rerun()
                    else:
                        st.error("Failed to reject change request. Please try again.")

def show_create_change_request():
    """Interface for creating a new change request"""
    st.header("Create Change Request")
    
    # Check if projects exist
    if "projects" not in st.session_state or not st.session_state.projects:
        st.warning("No projects available.")
        return
    
    user_id = st.session_state.user["id"]
    
    # Filter projects the user can access
    accessible_projects = [p for p in st.session_state.projects 
                            if can_access_project(user_id, p["id"])]
    
    if not accessible_projects:
        st.warning("You don't have access to any projects.")
        return
    
    # Project selection
    project_names = [p["name"] for p in accessible_projects]
    selected_project_name = st.selectbox("Select Project", project_names)
    
    selected_project = next((p for p in accessible_projects 
                           if p["name"] == selected_project_name), None)
    
    if not selected_project:
        st.warning("Please select a project.")
        return
    
    # Get tasks for the selected project
    project_tasks = [t for t in st.session_state.tasks 
                    if t["project_id"] == selected_project["id"]]
    
    if not project_tasks:
        st.warning("No tasks available for this project.")
        return
    
    # Item type selection
    item_type = st.radio("Select Item Type", ["Task", "Subtask"])
    
    if item_type == "Task":
        # Task selection
        task_names = [t["name"] for t in project_tasks]
        selected_task_name = st.selectbox("Select Task", task_names)
        
        selected_task = next((t for t in project_tasks 
                            if t["name"] == selected_task_name), None)
        
        if not selected_task:
            st.warning("Please select a task.")
            return
        
        # Check if user can access this task
        if not can_access_task(user_id, selected_task["id"]):
            st.error("You don't have access to this task.")
            return
        
        # Display current task details
        st.subheader("Current Task Details")
        st.markdown(f"**Name:** {selected_task['name']}")
        st.markdown(f"**Description:** {selected_task['description']}")
        st.markdown(f"**Start Date:** {selected_task['start_date']}")
        st.markdown(f"**End Date:** {selected_task['end_date']}")
        st.markdown(f"**Status:** {selected_task['status']}")
        st.markdown(f"**Priority:** {selected_task['priority']}")
        st.markdown(f"**Progress:** {selected_task['progress']}%")
        
        # Editable fields
        st.subheader("Propose Changes")
        
        with st.form("task_change_request_form"):
            description = st.text_area("Description", selected_task["description"])
            
            col1, col2 = st.columns(2)
            with col1:
                # Handle start date more safely
                start_date_value = None
                if selected_task["start_date"]:
                    try:
                        start_date_value = datetime.datetime.strptime(selected_task["start_date"], "%Y-%m-%d").date()
                    except:
                        start_date_value = datetime.date.today()
                else:
                    start_date_value = datetime.date.today()
                
                start_date = st.date_input("Start Date", value=start_date_value)
            
            with col2:
                # Handle end date more safely
                end_date_value = None
                if selected_task["end_date"]:
                    try:
                        end_date_value = datetime.datetime.strptime(selected_task["end_date"], "%Y-%m-%d").date()
                    except:
                        end_date_value = datetime.date.today() + datetime.timedelta(days=7)
                else:
                    end_date_value = datetime.date.today() + datetime.timedelta(days=7)
                
                end_date = st.date_input("End Date", value=end_date_value)
            
            status_options = ["Not Started", "In Progress", "Completed", "On Hold"]
            status = st.selectbox("Status", options=status_options, index=status_options.index(selected_task["status"]) if selected_task["status"] in status_options else 0)
            
            priority_options = ["Low", "Medium", "High", "Critical"]
            priority = st.selectbox("Priority", options=priority_options, index=priority_options.index(selected_task["priority"]) if selected_task["priority"] in priority_options else 0)
            
            progress = st.slider("Progress (%)", 0, 100, selected_task["progress"])
            
            st.subheader("Change Request Details")
            
            change_reason = st.text_area("Reason for Change", 
                                         help="Explain why the current task cannot be completed as planned")
            
            impact_analysis = st.text_area("Impact Analysis", 
                                          help="Describe the potential effects and risks of making these changes")
            
            requires_meeting = st.checkbox("This change requires a team meeting", 
                                          help="Check if this change is significant enough to warrant team discussion")
            
            submit_btn = st.form_submit_button("Submit Change Request")
            
            if submit_btn:
                # Collect changes
                changes = {}
                
                if description != selected_task["description"]:
                    changes["description"] = description
                
                # Compare dates safely
                if selected_task["start_date"]:
                    try:
                        existing_start_date = datetime.datetime.strptime(selected_task["start_date"], "%Y-%m-%d").date()
                        if start_date != existing_start_date:
                            changes["start_date"] = start_date.strftime("%Y-%m-%d")
                    except:
                        changes["start_date"] = start_date.strftime("%Y-%m-%d")
                else:
                    changes["start_date"] = start_date.strftime("%Y-%m-%d")
                
                if selected_task["end_date"]:
                    try:
                        existing_end_date = datetime.datetime.strptime(selected_task["end_date"], "%Y-%m-%d").date()
                        if end_date != existing_end_date:
                            changes["end_date"] = end_date.strftime("%Y-%m-%d")
                    except:
                        changes["end_date"] = end_date.strftime("%Y-%m-%d")
                else:
                    changes["end_date"] = end_date.strftime("%Y-%m-%d")
                
                if status != selected_task["status"]:
                    changes["status"] = status
                
                if priority != selected_task["priority"]:
                    changes["priority"] = priority
                
                if progress != selected_task["progress"]:
                    changes["progress"] = progress
                
                if not changes:
                    st.warning("No changes detected. Please modify at least one field.")
                else:
                    # Create change request
                    result = create_change_request("task", selected_task["id"], user_id, changes, requires_meeting, change_reason, impact_analysis)
                    
                    if result:
                        st.success("Change request submitted successfully!")
                    else:
                        st.error("Failed to submit change request. Please try again.")
    
    else:  # Subtask
        # Task selection first
        task_names = [t["name"] for t in project_tasks]
        selected_task_name = st.selectbox("Select Parent Task", task_names)
        
        selected_task = next((t for t in project_tasks 
                            if t["name"] == selected_task_name), None)
        
        if not selected_task:
            st.warning("Please select a parent task.")
            return
        
        # Check if user can access this task
        if not can_access_task(user_id, selected_task["id"]):
            st.error("You don't have access to this task.")
            return
        
        # Get subtasks for the selected task
        task_subtasks = [s for s in st.session_state.subtasks 
                        if s["parent_task_id"] == selected_task["id"]]
        
        if not task_subtasks:
            st.warning("No subtasks available for this task.")
            return
        
        # Subtask selection
        subtask_names = [s["name"] for s in task_subtasks]
        selected_subtask_name = st.selectbox("Select Subtask", subtask_names)
        
        selected_subtask = next((s for s in task_subtasks 
                               if s["name"] == selected_subtask_name), None)
        
        if not selected_subtask:
            st.warning("Please select a subtask.")
            return
        
        # Display current subtask details
        st.subheader("Current Subtask Details")
        st.markdown(f"**Name:** {selected_subtask['name']}")
        st.markdown(f"**Description:** {selected_subtask['description']}")
        st.markdown(f"**Start Date:** {selected_subtask['start_date']}")
        st.markdown(f"**End Date:** {selected_subtask['end_date']}")
        st.markdown(f"**Status:** {selected_subtask['status']}")
        st.markdown(f"**Progress:** {selected_subtask['progress']}%")
        
        # Editable fields
        st.subheader("Propose Changes")
        
        with st.form("subtask_change_request_form"):
            description = st.text_area("Description", selected_subtask["description"])
            
            col1, col2 = st.columns(2)
            with col1:
                # Handle start date more safely
                start_date_value = None
                if selected_subtask["start_date"]:
                    try:
                        start_date_value = datetime.datetime.strptime(selected_subtask["start_date"], "%Y-%m-%d").date()
                    except:
                        start_date_value = datetime.date.today()
                else:
                    start_date_value = datetime.date.today()
                
                start_date = st.date_input("Start Date", value=start_date_value)
            
            with col2:
                # Handle end date more safely
                end_date_value = None
                if selected_subtask["end_date"]:
                    try:
                        end_date_value = datetime.datetime.strptime(selected_subtask["end_date"], "%Y-%m-%d").date()
                    except:
                        end_date_value = datetime.date.today() + datetime.timedelta(days=7)
                else:
                    end_date_value = datetime.date.today() + datetime.timedelta(days=7)
                
                end_date = st.date_input("End Date", value=end_date_value)
            
            status_options = ["Not Started", "In Progress", "Completed", "On Hold"]
            status = st.selectbox("Status", options=status_options, index=status_options.index(selected_subtask["status"]) if selected_subtask["status"] in status_options else 0)
            
            progress = st.slider("Progress (%)", 0, 100, selected_subtask["progress"])
            
            st.subheader("Change Request Details")
            
            change_reason = st.text_area("Reason for Change", 
                                         help="Explain why the current subtask cannot be completed as planned")
            
            impact_analysis = st.text_area("Impact Analysis", 
                                          help="Describe the potential effects and risks of making these changes")
            
            requires_meeting = st.checkbox("This change requires a team meeting", 
                                          help="Check if this change is significant enough to warrant team discussion")
            
            submit_btn = st.form_submit_button("Submit Change Request")
            
            if submit_btn:
                # Collect changes
                changes = {}
                
                if description != selected_subtask["description"]:
                    changes["description"] = description
                
                # Compare dates safely
                if selected_subtask["start_date"]:
                    try:
                        existing_start_date = datetime.datetime.strptime(selected_subtask["start_date"], "%Y-%m-%d").date()
                        if start_date != existing_start_date:
                            changes["start_date"] = start_date.strftime("%Y-%m-%d")
                    except:
                        changes["start_date"] = start_date.strftime("%Y-%m-%d")
                else:
                    changes["start_date"] = start_date.strftime("%Y-%m-%d")
                
                if selected_subtask["end_date"]:
                    try:
                        existing_end_date = datetime.datetime.strptime(selected_subtask["end_date"], "%Y-%m-%d").date()
                        if end_date != existing_end_date:
                            changes["end_date"] = end_date.strftime("%Y-%m-%d")
                    except:
                        changes["end_date"] = end_date.strftime("%Y-%m-%d")
                else:
                    changes["end_date"] = end_date.strftime("%Y-%m-%d")
                
                if status != selected_subtask["status"]:
                    changes["status"] = status
                
                if progress != selected_subtask["progress"]:
                    changes["progress"] = progress
                
                if not changes:
                    st.warning("No changes detected. Please modify at least one field.")
                else:
                    # Create change request
                    result = create_change_request("subtask", selected_subtask["id"], user_id, 
                                                  changes, requires_meeting, change_reason, impact_analysis)
                    
                    if result:
                        st.success("Change request submitted successfully!")
                    else:
                        st.error("Failed to submit change request. Please try again.")