import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime
import streamlit as st
from utils.data_management import get_project_tasks

# Create chart for project statuses
def create_project_status_chart(projects):
    status_counts = {}
    for project in projects:
        status = project['status']
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Status': list(status_counts.keys()),
        'Count': list(status_counts.values())
    })
    
    # Create pie chart
    fig = px.pie(
        df, 
        values='Count', 
        names='Status', 
        title='Project Status Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.3
    )
    
    # Update layout
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return fig

# Create chart for project types
def create_project_type_chart(projects):
    type_counts = {}
    for project in projects:
        project_type = project['type']
        if project_type in type_counts:
            type_counts[project_type] += 1
        else:
            type_counts[project_type] = 1
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Type': list(type_counts.keys()),
        'Count': list(type_counts.values())
    })
    
    # Create bar chart
    fig = px.bar(
        df, 
        x='Type', 
        y='Count', 
        title='Projects by Type',
        color='Type',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Project Type",
        yaxis_title="Number of Projects"
    )
    
    return fig

# Create Gantt chart for project timeline
def create_gantt_chart(project_id, tasks):
    if not tasks:
        return None
    
    # Convert tasks to DataFrame for Gantt chart
    df = pd.DataFrame([
        {
            'Task': task['name'],
            'Start': task['start_date'],
            'Finish': task['end_date'],
            'Status': task['status'],
            'Progress': task.get('progress', 0),
            'ID': task['id'],
            # 'Milestone': task.get('is_milestone', False)  # Add default value
            # Safeguard for missing 'Milestone' column
            if 'Milestone' in df.columns:
                milestones = df[df['Milestone']]
            else:
                milestones = None  # Or handle it differently if milestones are crucial
            
        }
        for task in tasks
    ])
    
    # Convert dates to datetime
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])
    
    # Sort by start date
    df = df.sort_values('Start')
    
    # Create color map for task status
    color_map = {
        'Not Started': 'lightgrey',
        'In Progress': 'royalblue',
        'Completed': 'green',
        'Delayed': 'crimson'
    }
    
    # Create Gantt chart
    fig = px.timeline(
        df, 
        x_start='Start', 
        x_end='Finish', 
        y='Task',
        color='Status',
        color_discrete_map=color_map,
        title="Project Timeline",
        labels={"Task": "Task Name", "Start": "Start Date", "Finish": "End Date"},
        hover_data=['Progress', 'ID']
    )
    
    # Add markers for milestones
    milestones = df[df['Milestone']]
    if not milestones.empty:
        fig.add_trace(
            go.Scatter(
                x=milestones['Start'],
                y=milestones['Task'],
                mode='markers',
                marker=dict(symbol='diamond', size=12, color='red'),
                name='Milestone'
            )
        )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Timeline",
        yaxis_title="Tasks",
        showlegend=True,
        height=400 + (len(df) * 30),  # Adjust height based on number of tasks
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d'
        )
    )
    
    # Update y-axis
    fig.update_yaxes(autorange="reversed")  # Reverse the y-axis to show tasks from top to bottom
    
    return fig

# Create burndown chart
def create_burndown_chart(project_id, tasks):
    if not tasks:
        return None
    
    # Get project information
    project = None
    for p in st.session_state.projects:
        if p['id'] == project_id:
            project = p
            break
    
    if not project:
        return None
    
    # Extract start and end dates
    start_date = datetime.datetime.strptime(project['start_date'], '%Y-%m-%d')
    end_date = datetime.datetime.strptime(project['end_date'], '%Y-%m-%d')
    
    # Calculate total days
    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return None
    
    # Calculate total work and work completed
    total_work = len(tasks)
    
    # Create DataFrame with date range
    date_range = pd.date_range(start=start_date, end=end_date)
    df = pd.DataFrame(date_range, columns=['date'])
    
    # Calculate ideal burndown line
    df['ideal_remaining'] = [total_work - (i * total_work / total_days) for i in range(len(df))]
    
    # Calculate actual burndown based on task completion
    actual_remaining = []
    for date in df['date']:
        remaining = sum(1 for task in tasks if 
                        datetime.datetime.strptime(task['end_date'], '%Y-%m-%d') >= date and
                        (task['status'] != 'Completed' or 
                         datetime.datetime.strptime(task['end_date'], '%Y-%m-%d').date() == date.date()))
        actual_remaining.append(remaining)
    
    df['actual_remaining'] = actual_remaining
    
    # Create burndown chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ideal_remaining'],
        mode='lines',
        name='Ideal Burndown',
        line=dict(color='green', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['actual_remaining'],
        mode='lines+markers',
        name='Actual Burndown',
        line=dict(color='blue')
    ))
    
    # Update layout
    fig.update_layout(
        title="Project Burndown Chart",
        xaxis_title="Date",
        yaxis_title="Remaining Tasks",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Create team allocation chart
def create_team_allocation_chart(team_members):
    if not team_members:
        return None
    
    # Count roles
    role_counts = {}
    for member in team_members:
        role = member['role']
        if role in role_counts:
            role_counts[role] += 1
        else:
            role_counts[role] = 1
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Role': list(role_counts.keys()),
        'Count': list(role_counts.values())
    })
    
    # Create horizontal bar chart
    fig = px.bar(
        df, 
        y='Role', 
        x='Count', 
        title='Team Allocation by Role',
        orientation='h',
        color='Role',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Number of Team Members",
        yaxis_title="Role"
    )
    
    return fig

# Create project progress chart
def create_project_progress_chart(project_id, tasks):
    if not tasks:
        return None
    
    # Calculate progress for each status
    status_counts = {
        'Not Started': 0,
        'In Progress': 0,
        'Completed': 0,
        'Delayed': 0
    }
    
    for task in tasks:
        status = task['status']
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts['Not Started'] += 1  # Default status
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Status': list(status_counts.keys()),
        'Count': list(status_counts.values())
    })
    
    # Calculate percentages
    total = df['Count'].sum()
    df['Percentage'] = (df['Count'] / total * 100).round(1)
    
    # Create color map
    color_map = {
        'Not Started': 'lightgrey',
        'In Progress': 'royalblue',
        'Completed': 'green',
        'Delayed': 'crimson'
    }
    
    # Create pie chart
    fig = px.pie(
        df, 
        values='Count', 
        names='Status', 
        title='Task Status Distribution',
        color='Status',
        color_discrete_map=color_map,
        hole=0.4,
        hover_data=['Percentage']
    )
    
    # Calculate overall progress percentage
    completed_tasks = status_counts['Completed']
    completion_percentage = round((completed_tasks / total) * 100)
    
    # Add completion percentage in the middle
    fig.add_annotation(
        text=f"{completion_percentage}%<br>Complete",
        x=0.5, y=0.5,
        font_size=20,
        showarrow=False
    )
    
    # Update layout
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return fig
