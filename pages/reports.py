import streamlit as st
import datetime
import pandas as pd
import io
from utils.data_management import get_project, get_project_tasks, get_project_team, get_project_documents
from utils.visualization import create_project_progress_chart
from utils.pdf_generator import generate_project_report, generate_timeline_report, generate_team_report

def show_reports():
    st.title("📊 Reports & Analytics")
    
    # Check if a project is selected
    if not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first!")
        return
    
    # Get project data
    project_id = st.session_state.current_project_id
    project = get_project(project_id)
    tasks = get_project_tasks(project_id)
    team = get_project_team(project_id)
    documents = get_project_documents(project_id)
    
    if not project:
        st.error("Project not found!")
        return
    
    # Display reports image
    st.image("https://pixabay.com/get/gc6c00fa2ea156d3c99148dbadb7685efff41e6f16c335960c0eb627b53a962093b32922386366b9135434ef562123a96dbfd635d99be03485baa2f2266a67eca_1280.jpg", 
             caption="Project Reports", use_container_width=True)
    
    # Project reports header
    st.subheader(f"Reports for: {project['name']}")
    
    # Create tabs for different report types
    tab1, tab2, tab3, tab4 = st.tabs(["Project Overview", "Timeline Analysis", "Team Analysis", "Export Reports"])
    
    with tab1:
        # Project overview
        st.subheader("Project Overview Report")
        
        # Project summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Project Details")
            st.write(f"**Name:** {project['name']}")
            st.write(f"**Type:** {project['type']}")
            st.write(f"**Status:** {project['status']}")
            st.write(f"**Budget:** ${project['budget']:,.2f}")
            st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
        
        with col2:
            st.markdown("### Project Statistics")
            st.write(f"**Tasks:** {len(tasks)}")
            st.write(f"**Team Members:** {len(team)}")
            st.write(f"**Documents:** {len(documents)}")
            
            # Calculate completion metrics
            if tasks:
                completed_tasks = sum(1 for task in tasks if task['status'] == 'Completed')
                completion_percentage = round((completed_tasks / len(tasks)) * 100)
                st.write(f"**Completion:** {completion_percentage}%")
            else:
                st.write("**Completion:** N/A")
        
        # Project progress chart
        if tasks:
            st.subheader("Project Progress")
            fig = create_project_progress_chart(project_id, tasks)
            st.plotly_chart(fig, use_container_width=True)
        
        # Project description
        st.subheader("Project Description")
        st.write(project['description'])
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Combine and sort activities by date
        activities = []
        
        # Add task updates
        for task in tasks:
            activities.append({
                'date': task.get('created_at', project['created_at']),
                'type': 'Task Created',
                'description': f"Task '{task['name']}' was created"
            })
        
        # Add document uploads
        for doc in documents:
            activities.append({
                'date': doc.get('uploaded_at', project['created_at']),
                'type': 'Document Uploaded',
                'description': f"Document '{doc['name']}' was uploaded"
            })
        
        # Sort by date (newest first)
        activities = sorted(activities, key=lambda x: x['date'], reverse=True)
        
        # Display recent activities
        if activities:
            for i, activity in enumerate(activities[:5]):  # Show only the 5 most recent
                st.write(f"**{activity['date']}** - {activity['type']}: {activity['description']}")
        else:
            st.info("No recent activities found.")
    
    with tab2:
        # Timeline analysis
        st.subheader("Timeline Analysis")
        
        if tasks:
            # Timeline metrics
            project_start = datetime.datetime.strptime(project['start_date'], '%Y-%m-%d')
            project_end = datetime.datetime.strptime(project['end_date'], '%Y-%m-%d')
            project_duration = (project_end - project_start).days + 1
            
            # Calculate days elapsed and remaining
            today = datetime.datetime.now().date()
            days_elapsed = (today - project_start.date()).days
            days_remaining = (project_end.date() - today).days
            
            if days_elapsed < 0:
                days_elapsed = 0
            if days_remaining < 0:
                days_remaining = 0
            
            # Display timeline metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Duration", f"{project_duration} days")
            
            with col2:
                st.metric("Days Elapsed", f"{days_elapsed} days")
            
            with col3:
                st.metric("Days Remaining", f"{days_remaining} days")
            
            # Calculate expected vs. actual progress
            if project_duration > 0:
                expected_progress = min(100, round((days_elapsed / project_duration) * 100))
                
                completed_tasks = sum(1 for task in tasks if task['status'] == 'Completed')
                actual_progress = round((completed_tasks / len(tasks)) * 100)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Expected Progress", f"{expected_progress}%")
                
                with col2:
                    progress_diff = actual_progress - expected_progress
                    st.metric("Actual Progress", f"{actual_progress}%", delta=f"{progress_diff}%")
            
            # Task status breakdown
            st.subheader("Task Status Breakdown")
            
            status_counts = {}
            for task in tasks:
                status = task['status']
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            # Display as a horizontal bar chart
            status_df = pd.DataFrame({
                'Status': list(status_counts.keys()),
                'Count': list(status_counts.values())
            })
            
            # Calculate percentages
            status_df['Percentage'] = (status_df['Count'] / status_df['Count'].sum() * 100).round(1)
            status_df['Display'] = status_df['Count'].astype(str) + ' (' + status_df['Percentage'].astype(str) + '%)'
            
            # Create the chart using plotly express
            import plotly.express as px
            fig = px.bar(
                status_df, 
                y='Status', 
                x='Count',
                text='Display',
                orientation='h',
                color='Status',
                color_discrete_map={
                    'Not Started': 'lightgrey',
                    'In Progress': 'royalblue',
                    'Completed': 'green',
                    'Delayed': 'crimson'
                },
                title="Task Status Distribution"
            )
            
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Critical path analysis (simplified)
            st.subheader("Critical Path Tasks")
            
            # For simplicity, we'll consider tasks with dependencies as critical
            critical_tasks = [task for task in tasks if task.get('dependencies', [])]
            
            if critical_tasks:
                critical_df = pd.DataFrame([
                    {
                        'Task': task['name'],
                        'Start': task['start_date'],
                        'End': task['end_date'],
                        'Status': task['status']
                    }
                    for task in critical_tasks
                ])
                
                st.dataframe(critical_df, use_container_width=True)
            else:
                st.info("No critical path tasks identified (tasks with dependencies).")
        else:
            st.info("No tasks found. Add tasks to see timeline analysis.")
    
    with tab3:
        # Team analysis
        st.subheader("Team Analysis")
        
        if team:
            # Team composition
            st.markdown("### Team Composition")
            
            # Count roles
            role_counts = {}
            for member in team:
                role = member['role']
                if role in role_counts:
                    role_counts[role] += 1
                else:
                    role_counts[role] = 1
            
            # Display as pie chart
            import plotly.express as px
            
            role_df = pd.DataFrame({
                'Role': list(role_counts.keys()),
                'Count': list(role_counts.values())
            })
            
            fig = px.pie(
                role_df,
                values='Count',
                names='Role',
                title='Team Composition by Role',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Team qualifications
            st.markdown("### Team Qualifications")
            
            # Collect all qualifications
            all_qualifications = {}
            for member in team:
                if 'qualifications' in member:
                    for qual in member['qualifications']:
                        if qual in all_qualifications:
                            all_qualifications[qual] += 1
                        else:
                            all_qualifications[qual] = 1
            
            if all_qualifications:
                # Display as bar chart
                qual_df = pd.DataFrame({
                    'Qualification': list(all_qualifications.keys()),
                    'Count': list(all_qualifications.values())
                })
                
                qual_df = qual_df.sort_values('Count', ascending=False)
                
                fig = px.bar(
                    qual_df,
                    x='Qualification',
                    y='Count',
                    title='Team Qualifications',
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No qualifications recorded for team members.")
            
            # Team directory
            st.markdown("### Team Directory")
            
            # Create dataframe for team
            team_df = pd.DataFrame([
                {
                    'Name': member['name'],
                    'Role': member['role'],
                    'Email': member['email'],
                    'Phone': member.get('phone', 'N/A')
                }
                for member in team
            ])
            
            st.dataframe(team_df, use_container_width=True)
        else:
            st.info("No team members assigned to this project. Add team members to see team analysis.")
    
    with tab4:
        # Export reports
        st.subheader("Export Reports")
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            ["Project Summary Report", "Timeline Report", "Team Report"]
        )
        
        # Generate report button
        if st.button("Generate Report"):
            if report_type == "Project Summary Report":
                # Generate project summary report
                pdf_buffer = generate_project_report(project_id)
                
                if pdf_buffer:
                    # Create download button
                    st.download_button(
                        label="Download Project Summary Report",
                        data=pdf_buffer,
                        file_name=f"{project['name']}_Summary_Report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate report!")
            
            elif report_type == "Timeline Report":
                # Generate timeline report
                pdf_buffer = generate_timeline_report(project_id)
                
                if pdf_buffer:
                    # Create download button
                    st.download_button(
                        label="Download Timeline Report",
                        data=pdf_buffer,
                        file_name=f"{project['name']}_Timeline_Report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate report!")
            
            elif report_type == "Team Report":
                # Generate team report
                pdf_buffer = generate_team_report(project_id)
                
                if pdf_buffer:
                    # Create download button
                    st.download_button(
                        label="Download Team Report",
                        data=pdf_buffer,
                        file_name=f"{project['name']}_Team_Report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate report!")
        
        # Custom report options
        with st.expander("Custom Report Options"):
            st.write("Select specific data to include in your report:")
            
            include_project_details = st.checkbox("Project Details", value=True)
            include_tasks = st.checkbox("Tasks", value=True)
            include_team = st.checkbox("Team Members", value=True)
            include_documents = st.checkbox("Documents", value=True)
            include_charts = st.checkbox("Charts and Graphs", value=True)
            
            # This is just a UI placeholder - would need to implement custom report generation
            if st.button("Generate Custom Report"):
                st.info("Custom report generation is not implemented in this demo.")
                
                # For a complete implementation, you would use the selections above
                # to generate a customized report with only the selected sections
    
    # Reporting best practices
    with st.expander("Reporting Best Practices"):
        st.markdown("""
        ### Effective Project Reporting
        
        1. **Regular Updates**: Generate reports at consistent intervals for trend analysis.
        2. **Focus on KPIs**: Emphasize the most important metrics for your project type.
        3. **Visual Presentation**: Use charts and graphs to make data more accessible.
        4. **Concise Summaries**: Include executive summaries with key findings.
        5. **Action Items**: Highlight needed actions based on report findings.
        6. **Distribute Appropriately**: Share reports with relevant stakeholders.
        
        Good reporting practices improve project visibility and help identify issues early.
        """)
