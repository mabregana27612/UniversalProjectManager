import streamlit as st
import datetime
import pandas as pd
from utils.data_management import add_project, update_project, get_project, delete_project, load_data

def show_project_creation():
    st.title("📝 Project Creation & Management")
    
    # Display project creation image
    st.image("https://pixabay.com/get/g5b8d2e8fcfa0c3e1077c69c38f1f76ec052a1767732e84f24d686719b25f9dfd9c762f8dc89d0a241836c844d39a4ce441f411116c7deb540b9a5523569505ee_1280.jpg", 
             caption="Project Planning", use_container_width=True)
    
    # Determine if we're editing an existing project
    editing = st.session_state.current_project_id is not None
    
    # Get existing project data if editing
    project_data = {}
    if editing:
        project = get_project(st.session_state.current_project_id)
        if project:
            project_data = project
        else:
            st.error("Project not found!")
            return
    
    # Project Name
    name = st.text_input(
        "Project Name",
        value=project_data.get('name', ''),
        help="Enter a descriptive name for your project"
    )
    
    # Project Type
    project_types = ["Infrastructure", "Goods Procurement", "Small-Scale", "Development", "Marketing", "Other"]
    # Handle existing project type safely
    if 'type' in project_data:
        type_value = project_data.get('type', 'Infrastructure')
        if type_value in project_types:
            index_value = project_types.index(type_value)
        else:
            index_value = 0
    else:
        index_value = 0
        
    project_type = st.selectbox(
        "Project Type",
        project_types,
        index=index_value,
        help="Select the type of project you're planning"
    )
    
    # Project Description
    description = st.text_area(
        "Project Description",
        value=project_data.get('description', ''),
        help="Provide a detailed description of the project"
    )
    
    # Budget
    budget = st.number_input(
        "Budget (USD)",
        min_value=0.0,
        value=float(project_data.get('budget', 0.0)),
        format="%.2f",
        help="Enter the total budget for the project"
    )
    
    # Timeline
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.datetime.strptime(project_data.get('start_date', datetime.datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
            help="Select the planned start date"
        )
    
    with col2:
        default_end = datetime.datetime.now() + datetime.timedelta(days=90)
        if 'end_date' in project_data:
            default_end = datetime.datetime.strptime(project_data['end_date'], '%Y-%m-%d')
        
        end_date = st.date_input(
            "End Date",
            value=default_end,
            help="Select the planned end date"
        )
    
    # Project Status (only shown when editing)
    status = "Planning"  # Default for new projects
    if editing:
        status_options = ["Planning", "In Progress", "On Hold", "Completed"]
        status = st.selectbox(
            "Project Status",
            status_options,
            index=status_options.index(project_data.get('status', 'Planning')),
            help="Update the current status of the project"
        )
    
    # Form submission
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Project"):
            if not name:
                st.error("Project name is required!")
            elif start_date >= end_date:
                st.error("End date must be after start date!")
            else:
                project_data = {
                    'name': name,
                    'type': project_type,
                    'description': description,
                    'budget': budget,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'status': status
                }
                
                if editing:
                    success = update_project(st.session_state.current_project_id, project_data)
                    if success:
                        st.success("Project updated successfully!")
                        # Refresh projects in session state
                        from utils.data_management import load_data
                        st.session_state.projects = load_data('projects')
                    else:
                        st.error("Failed to update project!")
                else:
                    project_id = add_project(project_data)
                    if project_id:
                        st.success(f"Project created with ID: {project_id}")
                        st.session_state.current_project_id = project_id
                        # Refresh projects in session state
                        from utils.data_management import load_data
                        st.session_state.projects = load_data('projects')
                    else:
                        st.error("Failed to create project!")
    
    # Delete button (only shown when editing)
    if editing:
        with col2:
            if st.button("Delete Project", type="secondary"):
                if st.session_state.current_project_id:
                    if delete_project(st.session_state.current_project_id):
                        st.success("Project deleted successfully!")
                        st.session_state.current_project_id = None
                        # Refresh projects in session state
                        from utils.data_management import load_data
                        st.session_state.projects = load_data('projects')
                        # Return to dashboard
                        st.session_state.current_page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Failed to delete project!")
    
    # Project creation guidelines
    with st.expander("Project Creation Guidelines"):
        st.markdown("""
        ### Creating Effective Projects
        
        1. **Clear Objectives**: Define what the project aims to achieve.
        2. **Realistic Budget**: Ensure your budget covers all expected expenses.
        3. **Reasonable Timeline**: Set achievable deadlines with buffer time.
        4. **Detailed Description**: Provide comprehensive details for better understanding.
        5. **Appropriate Type Selection**: Choose the right project type for proper categorization.
        
        After creating your project, you can add tasks, assign team members, and upload documents.
        """)
