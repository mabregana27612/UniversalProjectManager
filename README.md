# Universal Project Management Information System (UPMIS)

A comprehensive Project Management Information System (PMIS) built with Streamlit to support various types of projects from planning through completion and archival.

## Features

- Project creation and management with different project types (infrastructure, goods procurement, small-scale)
- Work breakdown structure and task management with dependencies
- Timeline visualization with interactive Gantt charts
- Team management with role assignment and qualification tracking
- Document management and sharing
- Project monitoring with KPI dashboards
- Reporting with PDF generation
- Project archiving and historical records

## Getting Started

1. Install the required dependencies:
   ```
   pip install streamlit pandas plotly matplotlib reportlab numpy pillow
   ```

2. Run the application:
   ```
   streamlit run app.py
   ```

## Application Structure

- `app.py`: Main application entry point with dashboard and navigation
- `utils/`: Utility functions for data management, visualization, and PDF generation
- `pages/`: Individual page components for different application features

## Data Storage

The application uses pickle files for data persistence:
- `data/projects.pkl`: Project information
- `data/tasks.pkl`: Task and milestone data
- `data/team_members.pkl`: Team member information
- `data/documents.pkl`: Document metadata and content

## Usage Guide

1. **Project Creation**: Start by creating a new project with details like name, type, budget, and timeline.
2. **Task Planning**: Create tasks, set dependencies, and mark milestones on the Timeline page.
3. **Team Assignment**: Add team members and assign them to your project.
4. **Document Management**: Upload and manage project documents.
5. **Monitoring**: Track progress on the Dashboard and generate reports.
6. **Project Completion**: Archive completed projects for historical reference.

## Project Types Supported

- Infrastructure Development (e.g., transformer installation)
- Goods Procurement
- Small-Scale Local Projects
