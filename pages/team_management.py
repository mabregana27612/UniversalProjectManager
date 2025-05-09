import streamlit as st
import datetime
import pandas as pd
from utils.data_management import (
    get_project, get_project_team, add_team_member, update_team_member, load_data,
    get_team_member, get_project_team_leaders, get_team_members_by_leader, assign_member_to_leader
)
from utils.visualization import create_team_allocation_chart

def show_team_management():
    st.title("👥 Team Management")
    
    # Check if a project is selected
    if not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first!")
        return
    
    # Get project and team
    project_id = st.session_state.current_project_id
    project = get_project(project_id)
    team = get_project_team(project_id)
    
    if not project:
        st.error("Project not found!")
        return
    
    # Display team image
    st.image("https://pixabay.com/get/g1c86a0f87b27ecf0bba706ecc1bb597ee6ea308424d9fc422512a2631c8bdda54cbbc2f75a1bb0ba79e0ce49845ef93cb8a01123326b053018fe76661dbd334b_1280.jpg", 
             caption="Project Team", use_container_width=True)
    
    # Project team header
    st.subheader(f"Team for: {project['name']}")
    
    # Create tabs for Team View, Team Hierarchy and Member Management
    # Set active tab if coming from edit button
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Team Overview"
    
    # Figure out which tab should be active
    tabs = ["Team Overview", "Team Hierarchy", "Member Management"]
    active_tab_index = tabs.index(st.session_state.active_tab)
    
    tab1, tab2, tab3 = st.tabs(tabs)
    tabs_list = [tab1, tab2, tab3]
    # The active tab will be used
    
    with tab1:
        # Team visualization
        if team:
            # Team metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Team Size", len(team))
            
            with col2:
                roles = set(member['role'] for member in team)
                st.metric("Unique Roles", len(roles))
            
            with col3:
                qualifications = set()
                for member in team:
                    if 'qualifications' in member:
                        qualifications.update(member['qualifications'])
                st.metric("Qualifications", len(qualifications))
            
            # Team allocation chart
            st.subheader("Team Allocation")
            fig = create_team_allocation_chart(team)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Team member cards
            st.subheader("Team Members")
            
            # Sort team by role
            sorted_team = sorted(team, key=lambda x: x['role'])
            
            # Display team members in a grid
            cols = st.columns(3)
            for i, member in enumerate(sorted_team):
                with cols[i % 3]:
                    with st.container():
                        st.markdown(f"### {member['name']}")
                        st.caption(f"**Role:** {member['role']}")
                        if 'contact_email' in member and member['contact_email']:
                            st.write(f"**Email:** {member['contact_email']}")
                        if 'contact_phone' in member and member['contact_phone']:
                            st.write(f"**Phone:** {member['contact_phone']}")
                        
                        if 'qualifications' in member and member['qualifications']:
                            st.write("**Qualifications:**")
                            for qual in member['qualifications']:
                                st.write(f"- {qual}")
                        
                        # Edit button
                        if st.button(f"Edit", key=f"edit_{member['id']}"):
                            st.session_state.editing_member_id = member['id']
                            st.session_state.active_tab = "Member Management"  # Set active tab
                            st.rerun()
                        
                        st.markdown("---")
        else:
            st.info("No team members assigned to this project. Add team members in the Member Management tab.")
    
    with tab2:
        # Team hierarchy management
        st.subheader("Team Hierarchy Management")
        
        # Get team leaders
        team_leaders = [member for member in team if member.get('is_team_leader', False)]
        
        if not team_leaders:
            st.info("No team leaders assigned to this project. Designate team members as leaders in the Member Management tab.")
        else:
            st.subheader("Team Structure")
            
            # Display team hierarchy
            for leader in team_leaders:
                with st.expander(f"Team Lead: {leader['name']} ({leader['role']})", expanded=True):
                    # Get team members reporting to this leader
                    team_members_under_leader = []
                    
                    if 'team_members' in leader and leader['team_members']:
                        for member_id in leader['team_members']:
                            member = get_team_member(member_id)
                            if member and member_id != leader['id']:  # Avoid self-reference
                                team_members_under_leader.append(member)
                    
                    if team_members_under_leader:
                        st.write("Team Members:")
                        for member in team_members_under_leader:
                            st.write(f"- {member['name']} ({member['role']})")
                    else:
                        st.info("No team members assigned to this leader.")
                    
                    # Team member assignment
                    st.write("Assign Team Members:")
                    
                    # Filter members not assigned to any leader and part of this project
                    unassigned_members = [m for m in team if 
                                         (not m.get('reports_to') or m.get('reports_to') == leader['id']) and
                                         m['id'] != leader['id'] and
                                         not m.get('is_team_leader', False)]
                    
                    if unassigned_members:
                        # Create a dropdown to select members
                        member_options = {f"{m['name']} ({m['role']})": m['id'] for m in unassigned_members}
                        selected_member = st.selectbox(
                            "Select Team Member",
                            options=list(member_options.keys()),
                            key=f"select_member_{leader['id']}"
                        )
                        
                        if st.button("Assign to Leader", key=f"assign_to_{leader['id']}"):
                            member_id = member_options[selected_member]
                            success = assign_member_to_leader(member_id, leader['id'])
                            if success:
                                st.success(f"Successfully assigned member to {leader['name']}")
                                st.rerun()
                            else:
                                st.error("Failed to assign team member.")
                    else:
                        st.info("No available unassigned members in this project.")
            
            # Team hierarchy visualization
            st.subheader("Team Hierarchy Visualization")
            st.info("Hierarchical team structure visualization: Team leaders → Team members")
            
            # Create a simple visualization of the team hierarchy
            hierarchy_html = """
            <style>
                .hierarchy-container {
                    margin-top: 20px;
                }
                .leader-box {
                    background-color: #f0f2f6;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .member-container {
                    margin-left: 30px;
                    margin-bottom: 5px;
                }
                .member-box {
                    background-color: #e6f3ff;
                    border-radius: 5px;
                    padding: 8px;
                    margin-bottom: 5px;
                }
                .connecting-line {
                    border-left: 2px solid #ccc;
                    height: 15px;
                    margin-left: 15px;
                    margin-bottom: -5px;
                }
            </style>
            <div class="hierarchy-container">
            """
            
            for leader in team_leaders:
                hierarchy_html += f"""
                <div class="leader-box">
                    <b>{leader['name']}</b> - {leader['role']}
                </div>
                <div class="member-container">
                """
                
                # Get team members reporting to this leader
                if 'team_members' in leader and leader['team_members']:
                    for member_id in leader['team_members']:
                        member = get_team_member(member_id)
                        if member and member_id != leader['id']:
                            hierarchy_html += f"""
                            <div class="connecting-line"></div>
                            <div class="member-box">
                                {member['name']} - {member['role']}
                            </div>
                            """
                
                hierarchy_html += "</div>"
            
            hierarchy_html += "</div>"
            st.markdown(hierarchy_html, unsafe_allow_html=True)
        
    with tab3:
        # Team member management
        st.subheader("Team Member Management")
        
        # Create two columns for the layout
        member_list_col, member_form_col = st.columns([1, 1])
        
        with member_list_col:
            # Display existing team members
            st.subheader("Current Team Members")
            
            if team:
                for member in team:
                    st.write(f"**{member['name']}** - {member['role']}")
            else:
                st.info("No team members assigned. Add your first team member!")
            
            # Show all team members button
            if st.button("Show All Available Team Members"):
                st.session_state.show_all_members = True
                st.rerun()
            
            # Show all available team members
            if 'show_all_members' in st.session_state and st.session_state.show_all_members:
                st.subheader("All Available Team Members")
                
                all_members = load_data('team_members')
                
                if all_members:
                    # Get already assigned members
                    assigned_ids = [member['id'] for member in team]
                    
                    # Show unassigned members
                    unassigned = [m for m in all_members if m['id'] not in assigned_ids]
                    
                    if unassigned:
                        for member in unassigned:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{member['name']}** - {member['role']}")
                            with col2:
                                if st.button("Assign", key=f"assign_{member['id']}"):
                                    # Add project to member's projects
                                    if 'projects' not in member:
                                        member['projects'] = []
                                    
                                    member['projects'].append(project_id)
                                    success = update_team_member(member['id'], member)
                                    
                                    if success:
                                        st.success(f"Added {member['name']} to project!")
                                        st.session_state.show_all_members = False
                                        st.rerun()
                    else:
                        st.info("All available team members are already assigned to this project.")
                else:
                    st.info("No team members in the system. Create a new team member.")
                
                if st.button("Hide All Members"):
                    st.session_state.show_all_members = False
                    st.rerun()
        
        with member_form_col:
            # Team member creation/editing form
            editing_member = False
            current_member = {}
            
            if 'editing_member_id' in st.session_state and st.session_state.editing_member_id:
                st.subheader("Edit Team Member")
                editing_member = True
                
                # Find the member being edited
                all_members = load_data('team_members')
                for member in all_members:
                    if member['id'] == st.session_state.editing_member_id:
                        current_member = member
                        break
            else:
                st.subheader("Add New Team Member")
            
            # Member form
            member_name = st.text_input(
                "Name", 
                value=current_member.get('name', ''),
                key="member_name"
            )
            
            # Role selection
            roles = [
                "Project Manager",
                "Engineer",
                "Safety Officer",
                "Foreman",
                "Electrician",
                "Architect",
                "Technician",
                "Procurement Officer",
                "Quality Assurance",
                "Administrative",
                "Other"
            ]
            
            default_role_index = 0
            if 'role' in current_member and current_member['role'] in roles:
                default_role_index = roles.index(current_member['role'])
            elif 'role' in current_member:
                roles.append(current_member['role'])
                default_role_index = len(roles) - 1
            
            member_role = st.selectbox(
                "Role", 
                roles,
                index=default_role_index,
                key="member_role"
            )
            
            # If Other is selected, show a text input for custom role
            if member_role == "Other":
                custom_role = st.text_input(
                    "Specify Role",
                    value=current_member.get('role', '') if current_member.get('role', '') not in roles else '',
                    key="custom_role"
                )
                if custom_role:
                    member_role = custom_role
            
            # Contact information
            member_email = st.text_input(
                "Email", 
                value=current_member.get('contact_email', ''),
                key="member_email"
            )
            
            member_phone = st.text_input(
                "Phone (optional)", 
                value=current_member.get('contact_phone', ''),
                key="member_phone"
            )
            
            # Team Leadership
            is_team_leader = st.checkbox(
                "Designate as Team Leader",
                value=current_member.get('is_team_leader', False),
                key="is_team_leader",
                help="Team leaders can manage their team members and assign tasks"
            )
            
            # Qualifications
            st.subheader("Qualifications")
            
            # Get current qualifications
            current_qualifications = current_member.get('qualifications', [])
            
            # Handle dynamic qualifications list
            if 'qualifications' not in st.session_state:
                st.session_state.qualifications = current_qualifications.copy() if current_qualifications else ['']
            
            # Create a container for the qualifications inputs
            qual_container = st.container()
            
            # Add qualification button
            if st.button("Add Qualification"):
                st.session_state.qualifications.append('')
                st.rerun()
            
            # Show qualification fields
            qualifications = []
            with qual_container:
                for i, qual in enumerate(st.session_state.qualifications):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        qualification = st.text_input(
                            f"Qualification {i+1}", 
                            value=qual,
                            key=f"qual_{i}"
                        )
                        if qualification:
                            qualifications.append(qualification)
                    
                    with col2:
                        if st.button("Remove", key=f"remove_qual_{i}"):
                            st.session_state.qualifications.pop(i)
                            st.rerun()
            
            # Projects assignment
            if editing_member:
                # Only show this when editing an existing member
                member_projects = current_member.get('projects', [])
                
                if project_id not in member_projects:
                    if st.checkbox("Assign to current project", value=False, key="assign_current"):
                        member_projects.append(project_id)
                else:
                    if st.checkbox("Remove from current project", value=False, key="remove_current"):
                        member_projects.remove(project_id)
            else:
                # When creating a new member, always assign to current project
                member_projects = [project_id]
            
            # Submit button
            if editing_member:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Member"):
                        if not member_name:
                            st.error("Name is required!")
                        elif not member_email:
                            st.error("Email is required!")
                        else:
                            member_data = {
                                'name': member_name,
                                'role': member_role,
                                'contact_email': member_email,
                                'contact_phone': member_phone,
                                'qualifications': qualifications,
                                'projects': member_projects,
                                'is_team_leader': is_team_leader,
                                'reports_to': current_member.get('reports_to', None),
                                'team_members': current_member.get('team_members', [])
                            }
                            
                            success = update_team_member(st.session_state.editing_member_id, member_data)
                            if success:
                                st.success("Team member updated successfully!")
                                st.session_state.editing_member_id = None
                                st.session_state.qualifications = ['']
                                st.rerun()
                            else:
                                st.error("Failed to update team member!")
                
                with col2:
                    if st.button("Cancel Editing"):
                        st.session_state.editing_member_id = None
                        st.session_state.qualifications = ['']
                        st.rerun()
            else:
                if st.button("Add Team Member"):
                    if not member_name:
                        st.error("Name is required!")
                    elif not member_email:
                        st.error("Email is required!")
                    else:
                        member_data = {
                            'name': member_name,
                            'role': member_role,
                            'email': member_email,
                            'phone': member_phone,
                            'qualifications': qualifications,
                            'projects': [project_id],
                            'is_team_leader': is_team_leader,
                            'reports_to': None,
                            'team_members': []
                        }
                        
                        member_id = add_team_member(member_data)
                        if member_id:
                            st.success(f"Team member added with ID: {member_id}")
                            st.session_state.qualifications = ['']
                            st.rerun()
                        else:
                            st.error("Failed to add team member!")
    
    # Team management best practices
    with st.expander("Team Management Best Practices"):
        st.markdown("""
        ### Effective Team Management
        
        1. **Clear Roles**: Define specific responsibilities for each team member.
        2. **Balanced Skill Mix**: Ensure the team has all required competencies.
        3. **Documentation**: Keep records of team certifications and qualifications.
        4. **Resource Allocation**: Assign the right people to the right tasks.
        5. **Communication**: Establish clear communication channels.
        6. **Recognition**: Acknowledge team members' contributions and achievements.
        
        A well-managed team is essential for project success and efficient execution.
        """)
