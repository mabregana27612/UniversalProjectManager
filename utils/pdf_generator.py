import io
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from utils.data_management import get_project, get_project_tasks, get_project_team, get_project_documents

def generate_project_report(project_id):
    """Generate a PDF report for a specific project"""
    # Get project data
    project = get_project(project_id)
    if not project:
        return None
    
    tasks = get_project_tasks(project_id)
    team = get_project_team(project_id)
    documents = get_project_documents(project_id)
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
    ))
    
    # Story is a list of flowables
    story = []
    
    # Add title
    title = Paragraph(f"Project Report: {project['name']}", styles['Center'])
    story.append(title)
    story.append(Spacer(1, 0.5 * inch))
    
    # Add project details
    story.append(Paragraph("Project Details", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    
    project_data = [
        ["Project Name:", project['name']],
        ["Project Type:", project['type']],
        ["Status:", project['status']],
        ["Budget:", f"${project['budget']:,.2f}"],
        ["Start Date:", project['start_date']],
        ["End Date:", project['end_date']]
    ]
    
    project_table = Table(project_data, colWidths=[2*inch, 3*inch])
    project_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(project_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Add description
    story.append(Paragraph("Project Description", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(project['description'], styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Add tasks
    if tasks:
        story.append(Paragraph("Project Tasks", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        task_data = [["Task Name", "Start Date", "End Date", "Status", "Progress"]]
        for task in tasks:
            task_data.append([
                task['name'],
                task['start_date'],
                task['end_date'],
                task['status'],
                f"{task['progress']}%"
            ])
        
        task_table = Table(task_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        task_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(task_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Add team
    if team:
        story.append(Paragraph("Project Team", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        team_data = [["Name", "Role", "Email"]]
        for member in team:
            team_data.append([
                member['name'],
                member['role'],
                member['email']
            ])
        
        team_table = Table(team_data, colWidths=[2*inch, 2*inch, 2*inch])
        team_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(team_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Add documents
    if documents:
        story.append(Paragraph("Project Documents", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        doc_data = [["Document Name", "Category", "Upload Date"]]
        for doc in documents:
            doc_data.append([
                doc['name'],
                doc['category'],
                doc['uploaded_at']
            ])
        
        doc_table = Table(doc_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        doc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(doc_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Add footer
    now = datetime.datetime.now()
    footer_text = f"Report generated on {now.strftime('%Y-%m-%d %H:%M:%S')}"
    footer = Paragraph(footer_text, styles['Normal'])
    story.append(Spacer(1, 1 * inch))
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF from buffer
    buffer.seek(0)
    return buffer

def generate_timeline_report(project_id):
    """Generate a timeline report for a specific project"""
    # Get project data
    project = get_project(project_id)
    if not project:
        return None
    
    tasks = get_project_tasks(project_id)
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
    ))
    
    # Story is a list of flowables
    story = []
    
    # Add title
    title = Paragraph(f"Timeline Report: {project['name']}", styles['Center'])
    story.append(title)
    story.append(Spacer(1, 0.5 * inch))
    
    # Add project timeline details
    story.append(Paragraph("Project Timeline", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    
    timeline_data = [
        ["Project Start:", project['start_date']],
        ["Project End:", project['end_date']],
        ["Duration:", f"{(datetime.datetime.strptime(project['end_date'], '%Y-%m-%d') - datetime.datetime.strptime(project['start_date'], '%Y-%m-%d')).days + 1} days"]
    ]
    
    timeline_table = Table(timeline_data, colWidths=[2*inch, 3*inch])
    timeline_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(timeline_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Add task timeline
    if tasks:
        story.append(Paragraph("Task Timeline", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Sort tasks by start date
        sorted_tasks = sorted(tasks, key=lambda x: x['start_date'])
        
        task_data = [["Task Name", "Start Date", "End Date", "Duration", "Status"]]
        for task in sorted_tasks:
            start_date = datetime.datetime.strptime(task['start_date'], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(task['end_date'], '%Y-%m-%d')
            duration = (end_date - start_date).days + 1
            
            task_data.append([
                task['name'],
                task['start_date'],
                task['end_date'],
                f"{duration} days",
                task['status']
            ])
        
        task_table = Table(task_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        task_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(task_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Add milestones section
        milestones = [task for task in tasks if task.get('is_milestone', False)]
        if milestones:
            story.append(Paragraph("Project Milestones", styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            milestone_data = [["Milestone", "Date", "Status"]]
            for milestone in sorted(milestones, key=lambda x: x['start_date']):
                milestone_data.append([
                    milestone['name'],
                    milestone['start_date'],
                    milestone['status']
                ])
            
            milestone_table = Table(milestone_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            milestone_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(milestone_table)
            story.append(Spacer(1, 0.3 * inch))
    
    # Add dependencies section
    tasks_with_dependencies = [task for task in tasks if task.get('dependencies', [])]
    if tasks_with_dependencies:
        story.append(Paragraph("Task Dependencies", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        dependency_data = [["Task", "Depends On"]]
        
        task_dict = {task['id']: task['name'] for task in tasks}
        
        for task in tasks_with_dependencies:
            dependencies = []
            for dep_id in task.get('dependencies', []):
                if dep_id in task_dict:
                    dependencies.append(task_dict[dep_id])
            
            if dependencies:
                dependency_data.append([
                    task['name'],
                    ", ".join(dependencies)
                ])
        
        if len(dependency_data) > 1:  # Check if we have actual dependencies beyond the header
            dependency_table = Table(dependency_data, colWidths=[3*inch, 3*inch])
            dependency_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(dependency_table)
            story.append(Spacer(1, 0.3 * inch))
    
    # Add footer
    now = datetime.datetime.now()
    footer_text = f"Timeline Report generated on {now.strftime('%Y-%m-%d %H:%M:%S')}"
    footer = Paragraph(footer_text, styles['Normal'])
    story.append(Spacer(1, 1 * inch))
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF from buffer
    buffer.seek(0)
    return buffer

def generate_team_report(project_id):
    """Generate a team report for a specific project"""
    # Get project data
    project = get_project(project_id)
    if not project:
        return None
    
    team = get_project_team(project_id)
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
    ))
    
    # Story is a list of flowables
    story = []
    
    # Add title
    title = Paragraph(f"Team Report: {project['name']}", styles['Center'])
    story.append(title)
    story.append(Spacer(1, 0.5 * inch))
    
    # Add project details
    story.append(Paragraph("Project Details", styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    
    project_data = [
        ["Project Name:", project['name']],
        ["Project Type:", project['type']],
        ["Status:", project['status']]
    ]
    
    project_table = Table(project_data, colWidths=[2*inch, 3*inch])
    project_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(project_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Add team summary
    if team:
        story.append(Paragraph("Team Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Count roles
        role_counts = {}
        for member in team:
            role = member['role']
            if role in role_counts:
                role_counts[role] += 1
            else:
                role_counts[role] = 1
        
        summary_data = [["Role", "Count"]]
        for role, count in role_counts.items():
            summary_data.append([role, str(count)])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Add detailed team info
        story.append(Paragraph("Team Members", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Sort team by role then name
        sorted_team = sorted(team, key=lambda x: (x['role'], x['name']))
        
        for member in sorted_team:
            story.append(Paragraph(f"{member['name']} - {member['role']}", styles['Heading3']))
            story.append(Spacer(1, 0.05 * inch))
            
            member_data = [
                ["Email:", member['email']],
                ["Phone:", member.get('phone', 'N/A')]
            ]
            
            member_table = Table(member_data, colWidths=[1.5*inch, 3.5*inch])
            member_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(member_table)
            story.append(Spacer(1, 0.1 * inch))
            
            # Add qualifications if any
            if 'qualifications' in member and member['qualifications']:
                story.append(Paragraph("Qualifications:", styles['Heading4']))
                for qual in member['qualifications']:
                    story.append(Paragraph(f"• {qual}", styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
            
            story.append(Spacer(1, 0.2 * inch))
    else:
        story.append(Paragraph("No team members assigned to this project.", styles['Normal']))
    
    # Add footer
    now = datetime.datetime.now()
    footer_text = f"Team Report generated on {now.strftime('%Y-%m-%d %H:%M:%S')}"
    footer = Paragraph(footer_text, styles['Normal'])
    story.append(Spacer(1, 1 * inch))
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF from buffer
    buffer.seek(0)
    return buffer
