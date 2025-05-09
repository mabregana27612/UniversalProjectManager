import streamlit as st
import datetime
import pandas as pd
from utils.data_management import (
    get_project, get_task, get_team_member, get_project_tasks, 
    get_project_team, get_team_members_by_leader, load_data, save_data
)

def show_team_meetings():
    """Display team meeting management interface"""
    # Check if user is logged in
    if not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return
    
    # Check if a project is selected
    if not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first!")
        return
    
    st.title("👥 Team Meetings")
    
    # Get current project
    project_id = st.session_state.current_project_id
    project = get_project(project_id)
    
    if not project:
        st.error("Project not found!")
        return
    
    st.subheader(f"Team Meetings for: {project['name']}")
    
    # Create tabs for different meeting functions
    schedule_tab, minutes_tab, action_tab = st.tabs(["Schedule Meeting", "Meeting Minutes", "Action Items"])
    
    with schedule_tab:
        show_meeting_scheduler(project_id)
    
    with minutes_tab:
        show_meeting_minutes(project_id)
    
    with action_tab:
        show_action_items(project_id)

def show_meeting_scheduler(project_id):
    """Interface for scheduling team meetings"""
    st.subheader("Schedule a Team Meeting")
    
    # Get team members for this project
    team_members = get_project_team(project_id)
    team_leaders = [m for m in team_members if m.get('is_team_leader', False)]
    
    # Check if current user is a team leader
    is_leader = False
    if st.session_state.get('team_member_id'):
        current_member = get_team_member(st.session_state.team_member_id)
        if current_member and current_member.get('is_team_leader', False):
            is_leader = True
    
    # Only team leaders and admins can schedule meetings
    if not (is_leader or st.session_state.user_role == 'admin'):
        st.info("Only team leaders and administrators can schedule meetings.")
        return
    
    # Meeting form
    with st.form("schedule_meeting_form"):
        meeting_title = st.text_input("Meeting Title", placeholder="Team Planning Session")
        
        col1, col2 = st.columns(2)
        with col1:
            meeting_date = st.date_input("Meeting Date", value=datetime.datetime.now() + datetime.timedelta(days=1))
        
        with col2:
            meeting_time = st.time_input("Meeting Time", value=datetime.time(9, 0))
        
        meeting_duration = st.slider("Duration (minutes)", min_value=15, max_value=180, value=60, step=15)
        meeting_location = st.text_input("Location", placeholder="Conference Room A or Virtual (Zoom)")
        
        meeting_agenda = st.text_area("Meeting Agenda", placeholder="1. Task assignments\n2. Project timeline review\n3. Open discussion")
        
        # Select participants
        st.subheader("Select Participants")
        
        # Always include the current user
        participant_ids = [st.session_state.team_member_id] if st.session_state.team_member_id else []
        
        if team_members:
            for member in team_members:
                # Don't show current user in the list (already included)
                if st.session_state.team_member_id and member['id'] == st.session_state.team_member_id:
                    continue
                    
                if st.checkbox(f"{member['name']} ({member['role']})", key=f"participant_{member['id']}"):
                    participant_ids.append(member['id'])
        
        # Submit button
        submit_button = st.form_submit_button("Schedule Meeting")
        
        if submit_button:
            if not meeting_title:
                st.error("Please enter a meeting title.")
            elif not meeting_agenda:
                st.error("Please provide a meeting agenda.")
            elif not participant_ids:
                st.error("Please select at least one participant.")
            else:
                # Create meeting
                meetings = load_data('meetings')
                
                # Generate new meeting ID
                new_id = 1
                if meetings:
                    new_id = max(m['id'] for m in meetings) + 1
                
                # Create meeting datetime
                meeting_datetime = datetime.datetime.combine(meeting_date, meeting_time)
                
                new_meeting = {
                    'id': new_id,
                    'project_id': project_id,
                    'title': meeting_title,
                    'datetime': meeting_datetime.strftime('%Y-%m-%d %H:%M'),
                    'duration': meeting_duration,
                    'location': meeting_location,
                    'agenda': meeting_agenda,
                    'participants': participant_ids,
                    'organized_by': st.session_state.team_member_id,
                    'status': 'Scheduled',
                    'minutes': '',
                    'action_items': []
                }
                
                meetings.append(new_meeting)
                save_data('meetings', meetings)
                
                st.success(f"Meeting '{meeting_title}' scheduled successfully!")
                st.rerun()
    
    # Display upcoming meetings
    show_upcoming_meetings(project_id)

def show_upcoming_meetings(project_id):
    """Display upcoming meetings for the project"""
    st.subheader("Upcoming Meetings")
    
    meetings = load_data('meetings')
    
    # Filter meetings for this project that are scheduled in the future
    now = datetime.datetime.now()
    upcoming_meetings = []
    
    for meeting in meetings:
        if meeting['project_id'] == project_id and meeting['status'] == 'Scheduled':
            meeting_time = datetime.datetime.strptime(meeting['datetime'], '%Y-%m-%d %H:%M')
            if meeting_time > now:
                upcoming_meetings.append(meeting)
    
    if upcoming_meetings:
        # Sort by meeting date
        # Add helper function to parse meeting datetime
        def parse_meeting_datetime(meeting_datetime):
            try:
                # Try with seconds
                return datetime.datetime.strptime(meeting_datetime, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Try without seconds
                    return datetime.datetime.strptime(meeting_datetime, '%Y-%m-%d %H:%M')
                except ValueError:
                    # Default fallback
                    return datetime.datetime.now()
                    
        upcoming_meetings.sort(key=lambda x: parse_meeting_datetime(x['datetime']))
        
        for meeting in upcoming_meetings:
            # Parse meeting datetime with flexible format
            meeting_time = parse_meeting_datetime(meeting['datetime'])
            organizer = get_team_member(meeting['organized_by']) if meeting.get('organized_by') else None
            organizer_name = organizer['name'] if organizer else "Unknown"
            
            with st.expander(f"{meeting['title']} - {meeting_time.strftime('%b %d, %Y at %I:%M %p')}"):
                st.write(f"**Organized by:** {organizer_name}")
                st.write(f"**Duration:** {meeting['duration']} minutes")
                st.write(f"**Location:** {meeting['location']}")
                
                st.subheader("Agenda")
                st.write(meeting['agenda'])
                
                st.subheader("Participants")
                participants = []
                for participant_id in meeting['participants']:
                    member = get_team_member(participant_id)
                    if member:
                        participants.append(f"- {member['name']} ({member['role']})")
                
                if participants:
                    for p in participants:
                        st.write(p)
                else:
                    st.write("No participants selected.")
                
                # Allow meeting cancellation or rescheduling
                if (st.session_state.team_member_id == meeting.get('organized_by') or 
                    st.session_state.user_role == 'admin'):
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Start Meeting", key=f"start_{meeting['id']}"):
                            start_meeting(meeting['id'])
                            st.success("Meeting started!")
                            st.rerun()
                    
                    with col2:
                        if st.button("Cancel Meeting", key=f"cancel_{meeting['id']}"):
                            cancel_meeting(meeting['id'])
                            st.success("Meeting cancelled!")
                            st.rerun()
    else:
        st.info("No upcoming meetings scheduled for this project.")

def show_meeting_minutes(project_id):
    """Display and record meeting minutes"""
    st.subheader("Meeting Minutes")
    
    meetings = load_data('meetings')
    
    # Filter active meetings for this project
    active_meetings = [m for m in meetings if m['project_id'] == project_id and m['status'] == 'In Progress']
    past_meetings = [m for m in meetings if m['project_id'] == project_id and m['status'] == 'Completed']
    
    tab1, tab2 = st.tabs(["Active Meetings", "Past Meetings"])
    
    with tab1:
        if active_meetings:
            for meeting in active_meetings:
                with st.expander(meeting['title'], expanded=True):
                    st.write(f"**Started at:** {meeting['datetime']}")
                    
                    # Display agenda
                    st.subheader("Agenda")
                    st.write(meeting['agenda'])
                    
                    # Meeting minutes form
                    st.subheader("Record Minutes")
                    meeting_notes = st.text_area(
                        "Meeting Notes", 
                        value=meeting.get('minutes', ''),
                        height=300,
                        key=f"notes_{meeting['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Minutes", key=f"save_{meeting['id']}"):
                            save_meeting_minutes(meeting['id'], meeting_notes)
                            st.success("Meeting minutes saved!")
                    
                    with col2:
                        if st.button("End Meeting", key=f"end_{meeting['id']}"):
                            end_meeting(meeting['id'])
                            st.success("Meeting completed!")
                            st.rerun()
        else:
            st.info("No active meetings for this project.")
    
    with tab2:
        if past_meetings:
            # Sort by date (most recent first)
            # Fix datetime format parsing - handle different formats
            def parse_meeting_datetime(meeting_datetime):
                try:
                    # Try with seconds
                    return datetime.datetime.strptime(meeting_datetime, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        # Try without seconds
                        return datetime.datetime.strptime(meeting_datetime, '%Y-%m-%d %H:%M')
                    except ValueError:
                        # Default fallback
                        return datetime.datetime.now()
                
            past_meetings.sort(key=lambda x: parse_meeting_datetime(x['datetime']), reverse=True)
            
            for meeting in past_meetings:
                with st.expander(f"{meeting['title']} - {meeting['datetime']}"):
                    st.subheader("Minutes")
                    if meeting.get('minutes'):
                        st.write(meeting['minutes'])
                    else:
                        st.info("No minutes recorded for this meeting.")
                    
                    # Display action items
                    if meeting.get('action_items'):
                        st.subheader("Action Items")
                        for item in meeting['action_items']:
                            status_color = "green" if item['status'] == "Completed" else "orange"
                            st.markdown(f"- **{item['description']}** (Assigned to: {item['assignee_name']}) "
                                       f"- <span style='color:{status_color}'>{item['status']}</span>", unsafe_allow_html=True)
        else:
            st.info("No past meetings for this project.")

def show_action_items(project_id):
    """Display and manage action items from meetings"""
    st.subheader("Meeting Action Items")
    
    meetings = load_data('meetings')
    
    # Get all action items across all meetings for this project
    all_action_items = []
    
    for meeting in meetings:
        if meeting['project_id'] == project_id and meeting.get('action_items'):
            for item in meeting['action_items']:
                # Add meeting info to each action item
                item_with_context = item.copy()
                item_with_context['meeting_id'] = meeting['id']
                item_with_context['meeting_title'] = meeting['title']
                item_with_context['meeting_date'] = meeting['datetime']
                all_action_items.append(item_with_context)
    
    # Create action items from current meeting
    active_meetings = [m for m in meetings if m['project_id'] == project_id and m['status'] == 'In Progress']
    
    if active_meetings:
        st.subheader("Create New Action Item")
        
        meeting_options = {m['id']: m['title'] for m in active_meetings}
        selected_meeting_id = st.selectbox(
            "Select Meeting",
            options=list(meeting_options.keys()),
            format_func=lambda x: meeting_options[x]
        )
        
        with st.form("new_action_item"):
            action_description = st.text_input("Action Description")
            
            # Get team members
            team_members = get_project_team(project_id)
            member_options = {m['id']: f"{m['name']} ({m['role']})" for m in team_members}
            
            assignee_id = st.selectbox(
                "Assign To",
                options=list(member_options.keys()),
                format_func=lambda x: member_options[x]
            )
            
            due_date = st.date_input("Due Date", value=datetime.datetime.now() + datetime.timedelta(days=7))
            
            submitted = st.form_submit_button("Create Action Item")
            
            if submitted:
                if not action_description:
                    st.error("Please enter a description for the action item.")
                else:
                    # Get the assignee name
                    assignee = get_team_member(assignee_id)
                    assignee_name = assignee['name'] if assignee else "Unknown"
                    
                    # Create new action item
                    new_action_item = {
                        'id': len(all_action_items) + 1,
                        'description': action_description,
                        'assignee_id': assignee_id,
                        'assignee_name': assignee_name,
                        'due_date': due_date.strftime('%Y-%m-%d'),
                        'status': 'In Progress',
                        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    
                    # Add action item to the meeting
                    for meeting in meetings:
                        if meeting['id'] == selected_meeting_id:
                            if 'action_items' not in meeting:
                                meeting['action_items'] = []
                            
                            meeting['action_items'].append(new_action_item)
                            break
                    
                    save_data('meetings', meetings)
                    st.success("Action item created successfully!")
                    st.rerun()
    
    # Display all action items
    tab1, tab2 = st.tabs(["Open Action Items", "Completed Action Items"])
    
    with tab1:
        open_items = [item for item in all_action_items if item['status'] != 'Completed']
        if open_items:
            # Sort by due date
            open_items.sort(key=lambda x: datetime.datetime.strptime(x['due_date'], '%Y-%m-%d'))
            
            for item in open_items:
                with st.expander(f"{item['description']} (Due: {item['due_date']})"):
                    st.write(f"**From Meeting:** {item['meeting_title']} on {item['meeting_date']}")
                    st.write(f"**Assigned to:** {item['assignee_name']}")
                    st.write(f"**Status:** {item['status']}")
                    
                    # Allow updating status if assigned to current user
                    if st.session_state.team_member_id and st.session_state.team_member_id == item['assignee_id']:
                        if st.button("Mark as Completed", key=f"complete_{item['id']}_{item['meeting_id']}"):
                            update_action_item_status(item['meeting_id'], item['id'], 'Completed')
                            st.success("Action item marked as completed!")
                            st.rerun()
        else:
            st.info("No open action items for this project.")
    
    with tab2:
        completed_items = [item for item in all_action_items if item['status'] == 'Completed']
        if completed_items:
            # Sort by due date
            completed_items.sort(key=lambda x: datetime.datetime.strptime(x['due_date'], '%Y-%m-%d'))
            
            for item in completed_items:
                with st.expander(f"{item['description']} (Completed)"):
                    st.write(f"**From Meeting:** {item['meeting_title']} on {item['meeting_date']}")
                    st.write(f"**Assigned to:** {item['assignee_name']}")
                    st.write(f"**Due Date:** {item['due_date']}")
        else:
            st.info("No completed action items for this project.")

def start_meeting(meeting_id):
    """Mark a meeting as started (in progress)"""
    meetings = load_data('meetings')
    
    for meeting in meetings:
        if meeting['id'] == meeting_id:
            meeting['status'] = 'In Progress'
            meeting['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            break
    
    save_data('meetings', meetings)

def end_meeting(meeting_id):
    """Mark a meeting as completed"""
    meetings = load_data('meetings')
    
    for meeting in meetings:
        if meeting['id'] == meeting_id:
            meeting['status'] = 'Completed'
            meeting['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            break
    
    save_data('meetings', meetings)

def cancel_meeting(meeting_id):
    """Cancel a scheduled meeting"""
    meetings = load_data('meetings')
    
    for meeting in meetings:
        if meeting['id'] == meeting_id:
            meeting['status'] = 'Cancelled'
            break
    
    save_data('meetings', meetings)

def save_meeting_minutes(meeting_id, minutes):
    """Save minutes for a meeting"""
    meetings = load_data('meetings')
    
    for meeting in meetings:
        if meeting['id'] == meeting_id:
            meeting['minutes'] = minutes
            break
    
    save_data('meetings', meetings)

def update_action_item_status(meeting_id, action_item_id, status):
    """Update the status of an action item"""
    meetings = load_data('meetings')
    
    for meeting in meetings:
        if meeting['id'] == meeting_id and meeting.get('action_items'):
            for item in meeting['action_items']:
                if item['id'] == action_item_id:
                    item['status'] = status
                    item['completed_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M') if status == 'Completed' else None
                    break
    
    save_data('meetings', meetings)