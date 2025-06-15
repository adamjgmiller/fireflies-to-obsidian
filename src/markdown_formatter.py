"""
Markdown Formatter for Fireflies Meeting Data.

This module provides functionality to format meeting transcripts and metadata
from Fireflies API into structured Markdown files suitable for Obsidian.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownFormatter:
    """
    Formats Fireflies meeting data into structured Markdown documents.
    
    Provides template-based formatting with YAML frontmatter, transcript sections,
    and meeting metadata suitable for Obsidian vault organization.
    """
    
    def __init__(self, template_config: Optional[Dict] = None):
        """
        Initialize the Markdown formatter with optional template configuration.
        
        Args:
            template_config: Optional configuration for customizing the template
        """
        self.template_config = template_config or {}
        logger.info("Markdown formatter initialized")
    
    def format_meeting(self, meeting_data: Dict) -> str:
        """
        Format complete meeting data into structured Markdown.
        
        Args:
            meeting_data: Complete meeting data from Fireflies API
            
        Returns:
            str: Formatted Markdown document
        """
        logger.debug(f"Formatting meeting: {meeting_data.get('id', 'unknown')}")
        
        # Build the complete markdown document
        sections = []
        
        # Add YAML frontmatter
        sections.append(self._generate_frontmatter(meeting_data))
        
        # Add meeting header
        sections.append(self._generate_header(meeting_data))
        
        # Add meeting details section
        sections.append(self._generate_meeting_details(meeting_data))
        
        # Add attendees section
        sections.append(self._generate_attendees_section(meeting_data))
        
        # Add summary section
        sections.append(self._generate_summary_section(meeting_data))
        
        # Add transcript section
        sections.append(self._generate_transcript_section(meeting_data))
        
        # Join all sections
        markdown_content = '\n\n'.join(filter(None, sections))
        
        logger.debug("Meeting formatting completed")
        return markdown_content
    
    def _generate_frontmatter(self, meeting_data: Dict) -> str:
        """
        Generate YAML frontmatter with all meeting metadata.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: YAML frontmatter section
        """
        # Extract basic meeting info
        meeting_id = meeting_data.get('id', '') or ''
        title = meeting_data.get('title') or 'Untitled Meeting'
        date = meeting_data.get('date', '') or ''
        duration = meeting_data.get('duration', 0)
        organizer = meeting_data.get('organizer_email', '') or ''
        
        # Extract attendees
        attendees = []
        meeting_attendees = meeting_data.get('meeting_attendees', []) or []
        for attendee in meeting_attendees:
            if attendee.get('email'):
                attendees.append(attendee['email'])
        
        # Extract participants (fallback if meeting_attendees is empty)
        if not attendees:
            attendees = meeting_data.get('participants', []) or []
        
        # Extract summary data
        summary = meeting_data.get('summary', {}) or {}
        keywords = summary.get('keywords', []) or []
        action_items = summary.get('action_items', []) or []
        topics = summary.get('topics_discussed', []) or []
        meeting_type = summary.get('meeting_type', '')
        
        # Build frontmatter
        frontmatter_lines = [
            '---',
            f'title: "{title}"',
            f'meeting_id: "{meeting_id}"',
            f'date: "{date}"',
            f'duration: {duration}',
            f'organizer: "{organizer}"',
            f'meeting_type: "{meeting_type}"',
        ]
        
        # Add attendees list
        if attendees:
            frontmatter_lines.append('attendees:')
            for attendee in attendees:
                frontmatter_lines.append(f'  - "{attendee}"')
        
        # Add keywords
        if keywords:
            frontmatter_lines.append('keywords:')
            # Handle both string and list formats
            if isinstance(keywords, str):
                frontmatter_lines.append(f'  - "{keywords}"')
            else:
                for keyword in keywords:
                    frontmatter_lines.append(f'  - "{keyword}"')
        
        # Add topics
        if topics:
            frontmatter_lines.append('topics:')
            # Handle both string and list formats
            if isinstance(topics, str):
                frontmatter_lines.append(f'  - "{topics}"')
            else:
                for topic in topics:
                    frontmatter_lines.append(f'  - "{topic}"')
        
        # Add action items
        if action_items:
            frontmatter_lines.append('action_items:')
            # Handle both string and list formats
            if isinstance(action_items, str):
                # If it's a string, treat as single item
                frontmatter_lines.append(f'  - "{action_items}"')
            else:
                # If it's a list, iterate through items
                for item in action_items:
                    frontmatter_lines.append(f'  - "{item}"')
        
        # Add URLs
        transcript_url = meeting_data.get('transcript_url', '')
        meeting_link = meeting_data.get('meeting_link', '')
        if transcript_url:
            frontmatter_lines.append(f'transcript_url: "{transcript_url}"')
        if meeting_link:
            frontmatter_lines.append(f'meeting_link: "{meeting_link}"')
        
        # Add tags
        frontmatter_lines.append('tags:')
        frontmatter_lines.append('  - "fireflies"')
        frontmatter_lines.append('  - "meeting"')
        if meeting_type:
            frontmatter_lines.append(f'  - "{meeting_type}"')
        
        frontmatter_lines.append('---')
        
        return '\n'.join(frontmatter_lines)
    
    def _generate_header(self, meeting_data: Dict) -> str:
        """
        Generate the main header section.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Header section
        """
        title = meeting_data.get('title') or 'Untitled Meeting'
        date_string = meeting_data.get('dateString', '') or ''
        
        header_lines = [
            f'# {title}',
            '',
            f'**Date:** {date_string}',
        ]
        
        return '\n'.join(header_lines)
    
    def _generate_meeting_details(self, meeting_data: Dict) -> str:
        """
        Generate meeting details section.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Meeting details section
        """
        duration = meeting_data.get('duration', 0)
        organizer = meeting_data.get('organizer_email', '')
        transcript_url = meeting_data.get('transcript_url', '')
        meeting_link = meeting_data.get('meeting_link', '')
        
        # Convert duration to readable format
        duration_mins = duration // 60
        duration_secs = duration % 60
        duration_str = f"{duration_mins}m {duration_secs}s" if duration_secs else f"{duration_mins}m"
        
        details_lines = [
            '## Meeting Details',
            '',
            f'- **Duration:** {duration_str}',
            f'- **Organizer:** {organizer}',
        ]
        
        if transcript_url:
            details_lines.append(f'- **Transcript URL:** [View in Fireflies]({transcript_url})')
        
        if meeting_link:
            details_lines.append(f'- **Meeting Link:** [Join Meeting]({meeting_link})')
        
        return '\n'.join(details_lines)
    
    def _generate_attendees_section(self, meeting_data: Dict) -> str:
        """
        Generate attendees section.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Attendees section
        """
        meeting_attendees = meeting_data.get('meeting_attendees', []) or []
        participants = meeting_data.get('participants', []) or []
        
        attendees_lines = [
            '## Attendees',
            ''
        ]
        
        # Use meeting_attendees if available (more detailed)
        if meeting_attendees:
            for attendee in meeting_attendees:
                name = attendee.get('displayName') or attendee.get('name', 'Unknown')
                email = attendee.get('email', '')
                location = attendee.get('location', '')
                
                attendee_info = f'- **{name}**'
                if email:
                    attendee_info += f' ({email})'
                if location:
                    attendee_info += f' - {location}'
                
                attendees_lines.append(attendee_info)
        
        # Fallback to participants list
        elif participants:
            for participant in participants:
                attendees_lines.append(f'- {participant}')
        
        else:
            attendees_lines.append('- No attendee information available')
        
        return '\n'.join(attendees_lines)
    
    def _generate_summary_section(self, meeting_data: Dict) -> str:
        """
        Generate meeting summary section.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Summary section
        """
        summary = meeting_data.get('summary', {}) or {}
        
        summary_lines = [
            '## Summary',
            ''
        ]
        
        # Add overview
        overview = summary.get('overview') or summary.get('short_overview', '')
        if overview:
            summary_lines.extend([
                '### Overview',
                overview,
                ''
            ])
        
        # Add key points
        bullet_gist = summary.get('shorthand_bullet', '')
        if bullet_gist:
            summary_lines.extend([
                '### Key Points',
                bullet_gist,
                ''
            ])
        
        # Add action items
        action_items = summary.get('action_items', [])
        if action_items:
            summary_lines.extend([
                '### Action Items',
                ''
            ])
            for item in action_items:
                summary_lines.append(f'- [ ] {item}')
            summary_lines.append('')
        
        # Add topics discussed
        topics = summary.get('topics_discussed', [])
        if topics:
            summary_lines.extend([
                '### Topics Discussed',
                ''
            ])
            for topic in topics:
                summary_lines.append(f'- {topic}')
            summary_lines.append('')
        
        # Add keywords
        keywords = summary.get('keywords', [])
        if keywords:
            summary_lines.extend([
                '### Keywords',
                ', '.join(keywords),
                ''
            ])
        
        return '\n'.join(summary_lines)
    
    def _generate_transcript_section(self, meeting_data: Dict) -> str:
        """
        Generate transcript section with grouped speaker sections.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Transcript section
        """
        sentences = meeting_data.get('sentences', []) or []
        
        if not sentences:
            return '## Transcript\n\n*No transcript available*'
        
        transcript_lines = [
            '## Transcript',
            ''
        ]
        
        # Group sentences by speaker for better readability
        current_speaker = None
        current_speaker_text = []
        
        for sentence in sentences:
            speaker_name = sentence.get('speaker_name', 'Unknown Speaker')
            text = sentence.get('text', '')
            start_time = sentence.get('start_time', 0)
            
            # Convert start_time to readable format (minutes:seconds)
            mins = int(start_time // 60)
            secs = int(start_time % 60)
            timestamp = f"{mins:02d}:{secs:02d}"
            
            # If speaker changed, write previous speaker's content
            if current_speaker and current_speaker != speaker_name:
                if current_speaker_text:
                    combined_text = ' '.join(current_speaker_text)
                    transcript_lines.append(f'**{current_speaker}:** {combined_text}')
                    transcript_lines.append('')
                current_speaker_text = []
            
            # Update current speaker and add text
            current_speaker = speaker_name
            current_speaker_text.append(text)
        
        # Write the last speaker's content
        if current_speaker and current_speaker_text:
            combined_text = ' '.join(current_speaker_text)
            transcript_lines.append(f'**{current_speaker}:** {combined_text}')
        
        return '\n'.join(transcript_lines)
    
    def format_filename(self, meeting_data: Dict) -> str:
        """
        Generate a filename for the meeting based on Fireflies data.
        
        Format: YYYY-MM-DD-HH-MM-[Meeting Title].md
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            str: Formatted filename
        """
        try:
            # Parse the date (could be ISO string or timestamp)
            date_value = meeting_data.get('date', '')
            if date_value:
                if isinstance(date_value, str):
                    # Parse ISO format: "2024-06-15T14:30:00.000Z"
                    dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                elif isinstance(date_value, (int, float)):
                    # Handle timestamp (assume milliseconds if large number)
                    timestamp = date_value / 1000 if date_value > 1e10 else date_value
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    # Fallback to current time
                    dt = datetime.now()
                date_part = dt.strftime('%Y-%m-%d-%H-%M')
            else:
                # Fallback to current time
                date_part = datetime.now().strftime('%Y-%m-%d-%H-%M')
            
            # Clean up meeting title for filename
            title = meeting_data.get('title', 'Untitled Meeting')
            # Remove invalid filename characters
            safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            # Replace multiple spaces with single spaces, then convert to dashes
            import re
            safe_title = re.sub(r'\s+', ' ', safe_title)
            safe_title = safe_title.replace(' ', '-')
            # Remove consecutive dashes
            safe_title = re.sub(r'-+', '-', safe_title)
            
            # Truncate if too long
            if len(safe_title) > 50:
                safe_title = safe_title[:50].rstrip('-')
            
            filename = f"{date_part}-{safe_title}.md"
            
            logger.debug(f"Generated filename: {filename}")
            return filename
        
        except Exception as e:
            logger.error(f"Error generating filename: {e}")
            # Fallback filename
            return f"meeting-{meeting_data.get('id', 'unknown')}.md" 