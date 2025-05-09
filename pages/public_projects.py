import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from utils.data_management import load_data
from utils.visualization import create_project_status_chart, create_project_type_chart

def show_public_projects():
    """Display public view of projects without requiring login"""
    st.title("🌐 Public Projects Overview")
    
    # Load projects data
    projects = load_data('projects')
    
    if not projects:
        st.info("No projects available to display.")
        return
    
    # Add an introduction at the top
    st.markdown("""
    ## Welcome to our Project Management System
    This is a public view of our ongoing, upcoming, and completed projects. 
    You can browse through project details, view timelines, and see project statuses.
    
    For more detailed information and to interact with projects, please log in.
    """)
    
    # Dashboard metrics
    st.subheader("Project Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Projects", len(projects))
    
    with col2:
        active_projects = sum(1 for p in projects if p['status'] != 'Completed')
        st.metric("Active Projects", active_projects)
    
    with col3:
        completed_projects = sum(1 for p in projects if p['status'] == 'Completed')
        st.metric("Completed Projects", completed_projects)
    
    # Project status and type charts
    st.subheader("Project Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Projects by Status")
        fig = create_project_status_chart(projects)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Projects by Type")
        fig = create_project_type_chart(projects)
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline view
    st.subheader("Project Timeline")
    
    # Create a Gantt chart for project timeline
    project_data = []
    
    for project in projects:
        start_date = datetime.datetime.strptime(project['start_date'], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(project['end_date'], '%Y-%m-%d')
        
        # Calculate a duration for plotting
        duration = (end_date - start_date).days
        
        project_data.append({
            'Project': project['name'],
            'Start': start_date,
            'End': end_date,
            'Duration': duration,
            'Status': project['status'],
            'Type': project['type']
        })
    
    if project_data:
        df = pd.DataFrame(project_data)
        
        fig = px.timeline(
            df, 
            x_start="Start", 
            x_end="End", 
            y="Project",
            color="Status",
            hover_name="Project",
            hover_data={"Type": True, "Duration": True, "Start": True, "End": True}
        )
        
        fig.update_layout(
            title="Project Timeline",
            xaxis_title="Timeline",
            yaxis_title="Projects",
            height=400,
            xaxis=dict(
                tickformat="%b %Y",
                tickangle=-45
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Project listings by category
    project_tabs = st.tabs(["Upcoming Projects", "Ongoing Projects", "Completed Projects"])
    
    with project_tabs[0]:  # Upcoming Projects
        upcoming_projects = [p for p in projects if datetime.datetime.strptime(p['start_date'], '%Y-%m-%d') > datetime.datetime.now()]
        
        if upcoming_projects:
            st.subheader(f"Upcoming Projects ({len(upcoming_projects)})")
            
            for project in upcoming_projects:
                with st.expander(f"{project['name']} ({project['type']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Description:** {project['description']}")
                        st.write(f"**Status:** {project['status']}")
                    with col2:
                        st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
                        st.write(f"**Type:** {project['type']}")
        else:
            st.info("No upcoming projects at this time.")
    
    with project_tabs[1]:  # Ongoing Projects
        ongoing_projects = [
            p for p in projects if (
                datetime.datetime.strptime(p['start_date'], '%Y-%m-%d') <= datetime.datetime.now() and
                datetime.datetime.strptime(p['end_date'], '%Y-%m-%d') >= datetime.datetime.now() and
                p['status'] != 'Completed'
            )
        ]
        
        if ongoing_projects:
            st.subheader(f"Ongoing Projects ({len(ongoing_projects)})")
            
            for project in ongoing_projects:
                with st.expander(f"{project['name']} ({project['type']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Description:** {project['description']}")
                        st.write(f"**Status:** {project['status']}")
                    with col2:
                        st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
                        st.write(f"**Progress:** {project.get('progress', 0)}%")
                        st.progress(int(project.get('progress', 0))/100)
        else:
            st.info("No ongoing projects at this time.")
    
    with project_tabs[2]:  # Completed Projects
        completed_projects = [p for p in projects if p['status'] == 'Completed']
        
        if completed_projects:
            st.subheader(f"Completed Projects ({len(completed_projects)})")
            
            for project in completed_projects:
                with st.expander(f"{project['name']} ({project['type']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Description:** {project['description']}")
                        st.write(f"**Status:** {project['status']}")
                    with col2:
                        st.write(f"**Timeline:** {project['start_date']} to {project['end_date']}")
                        st.write(f"**Type:** {project['type']}")
        else:
            st.info("No completed projects at this time.")
    
    # Add a login invitation at the bottom
    st.markdown("---")
    st.markdown("""
    ### Want to see more details or work on these projects?
    Please [log in](#User-Account) or register for an account to access additional features.
    """)