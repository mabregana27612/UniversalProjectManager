import streamlit as st
import datetime
import pandas as pd
from utils.data_management import load_data, get_project, archive_project, get_archived_projects

def show_archives():
    st.title("🗄️ Project Archives")
    
    # Get all projects
    all_projects = load_data('projects')
    
    # Display archive image
    st.image("https://pixabay.com/get/gd21063290330766ce55f4a6cdfeb7bb22074f6b47bc8e9b36c218b5e27fb6b58f702a3ab2be8817d7346fa0af7c5f548b3ceec586c11dc9d41036f31d57bce3e_1280.jpg", 
             caption="Project Archives", use_container_width=True)
    
    # Create tabs for Archive Browse and Archive Management
    tab1, tab2 = st.tabs(["Browse Archives", "Archive Management"])
    
    with tab1:
        # Browse archives
        st.subheader("Archived Projects")
        
        # Get archived projects
        archived_projects = [p for p in all_projects if p.get('archived', False)]
        
        if archived_projects:
            # Create filters
            col1, col2 = st.columns(2)
            
            with col1:
                # Project type filter
                project_types = list(set(p['type'] for p in archived_projects))
                selected_type = st.multiselect(
                    "Filter by Type",
                    options=project_types,
                    default=[]
                )
            
            with col2:
                # Date range filter
                min_date = min(datetime.datetime.strptime(p['created_at'].split()[0], '%Y-%m-%d') for p in archived_projects)
                max_date = max(datetime.datetime.strptime(p.get('archived_at', p['created_at']).split()[0], '%Y-%m-%d') for p in archived_projects)
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Search box
            search_query = st.text_input("Search Archives", "")
            
            # Apply filters
            filtered_projects = archived_projects
            
            # Type filter
            if selected_type:
                filtered_projects = [p for p in filtered_projects if p['type'] in selected_type]
            
            # Date filter
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_projects = [
                    p for p in filtered_projects 
                    if start_date <= datetime.datetime.strptime(p.get('archived_at', p['created_at']).split()[0], '%Y-%m-%d').date() <= end_date
                ]
            
            # Search filter
            if search_query:
                search_query = search_query.lower()
                filtered_projects = [
                    p for p in filtered_projects
                    if search_query in p['name'].lower() or 
                    search_query in p['description'].lower() or
                    search_query in p['type'].lower()
                ]
            
            # Display filtered archived projects
            if filtered_projects:
                # Sort by archived date (newest first)
                sorted_projects = sorted(
                    filtered_projects,
                    key=lambda x: x.get('archived_at', x['created_at']),
                    reverse=True
                )
                
                for project in sorted_projects:
                    with st.expander(f"{project['name']} ({project['type']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Description:** {project['description']}")
                            st.write(f"**Budget:** ${project['budget']:,.2f}")
                            st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
                        
                        with col2:
                            st.write(f"**Status:** {project['status']}")
                            st.write(f"**Created:** {project['created_at']}")
                            st.write(f"**Archived:** {project.get('archived_at', 'N/A')}")
                        
                        # View project button
                        if st.button(f"View Project Details", key=f"view_{project['id']}"):
                            st.session_state.current_project_id = project['id']
                            st.session_state.current_page = "Reports"
                            st.rerun()
            else:
                st.info("No archived projects match your search criteria.")
        else:
            st.info("No archived projects found.")
    
    with tab2:
        # Archive management
        st.subheader("Archive Management")
        
        # Only show active projects (not archived)
        active_projects = [p for p in all_projects if not p.get('archived', False) and p['status'] == 'Completed']
        
        if active_projects:
            st.markdown("### Archive Completed Projects")
            st.write("Select completed projects to archive:")
            
            for project in active_projects:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{project['name']}** ({project['type']}) - Completed on {project.get('updated_at', 'N/A')}")
                
                with col2:
                    if st.button(f"Archive", key=f"archive_{project['id']}"):
                        if archive_project(project['id']):
                            st.success(f"Project '{project['name']}' archived successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to archive project!")
        else:
            st.info("No completed projects available for archiving.")
        
        # Archive restoration (unarchive)
        st.markdown("### Restore Archived Projects")
        
        archived_projects = [p for p in all_projects if p.get('archived', False)]
        
        if archived_projects:
            st.write("Select archived projects to restore:")
            
            for project in archived_projects:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{project['name']}** ({project['type']}) - Archived on {project.get('archived_at', 'N/A')}")
                
                with col2:
                    if st.button(f"Restore", key=f"restore_{project['id']}"):
                        # Unarchive project
                        all_projects = load_data('projects')
                        for i, p in enumerate(all_projects):
                            if p['id'] == project['id']:
                                all_projects[i]['archived'] = False
                                if 'archived_at' in all_projects[i]:
                                    del all_projects[i]['archived_at']
                                from utils.data_management import save_data
                                save_data('projects', all_projects)
                                st.success(f"Project '{project['name']}' restored successfully!")
                                st.rerun()
                                break
        else:
            st.info("No archived projects available for restoration.")
    
    # Archiving best practices
    with st.expander("Archiving Best Practices"):
        st.markdown("""
        ### Project Archiving Guidelines
        
        1. **Complete Documentation**: Ensure all project documentation is finalized before archiving.
        2. **Final Reports**: Generate and store final project reports for historical reference.
        3. **Lessons Learned**: Document lessons learned and best practices from the project.
        4. **Asset Management**: Catalog and appropriately store any project assets.
        5. **Access Control**: Define who can access archived project information.
        6. **Retention Policy**: Follow organization's data retention policies.
        
        Proper archiving ensures organizational knowledge is preserved and can be accessed for future projects.
        """)
