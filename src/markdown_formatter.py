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
        
        # Format date properly
        date_value = meeting_data.get('date', '') or ''
        if date_value:
            if isinstance(date_value, str):
                # Keep ISO string format for frontmatter
                formatted_date = date_value
            elif isinstance(date_value, (int, float)):
                # Convert timestamp to ISO format
                timestamp = date_value / 1000 if date_value > 1e10 else date_value
                dt = datetime.fromtimestamp(timestamp)
                formatted_date = dt.isoformat() + 'Z'
            else:
                formatted_date = str(date_value)
        else:
            formatted_date = ''
        
        # Format duration with reasonable precision
        duration_raw = meeting_data.get('duration', 0)
        duration = round(duration_raw, 2) if isinstance(duration_raw, float) else duration_raw
        
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
        
        # Build frontmatter with Obsidian-specific properties
        frontmatter_lines = [
            '---',
            f'title: "{title}"',
            f'meeting_id: "{meeting_id}"',
            f'date: "{formatted_date}"',
            f'created: "{datetime.now().isoformat()}Z"',
            f'duration: {duration}',
            f'organizer: "{organizer}"',
            f'meeting_type: "{meeting_type}"',
        ]
        
        # Add aliases for better Obsidian linking
        aliases = [title]
        if meeting_id:
            aliases.append(meeting_id)
        # Add short title if title is long
        if len(title) > 30:
            short_title = title[:30].strip()
            if short_title not in aliases:
                aliases.append(short_title)
        
        if aliases:
            frontmatter_lines.append('aliases:')
            for alias in aliases:
                frontmatter_lines.append(f'  - "{alias}"')
        
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
        
        # Add comprehensive tags for Obsidian
        tags = ['fireflies', 'meeting']
        
        # Add meeting type if available
        if meeting_type and meeting_type.lower() != 'none':
            tags.append(meeting_type.lower().replace(' ', '-'))
        
        # Add year and month tags for temporal organization
        if formatted_date:
            try:
                if isinstance(formatted_date, str) and 'T' in formatted_date:
                    dt = datetime.fromisoformat(formatted_date.replace('Z', '+00:00'))
                    tags.extend([
                        f"year-{dt.year}",
                        f"month-{dt.strftime('%Y-%m')}"
                    ])
            except:
                pass
        
        # Add keyword-based tags (first 3 keywords only)
        if keywords:
            keyword_list = keywords if isinstance(keywords, list) else [keywords]
            for keyword in keyword_list[:3]:  # Limit to prevent tag bloat
                clean_keyword = keyword.lower().replace(' ', '-').replace('_', '-')
                if clean_keyword not in tags:
                    tags.append(clean_keyword)
        
        # Add organizer domain as tag
        if organizer and '@' in organizer:
            domain = organizer.split('@')[1].split('.')[0]
            tags.append(f"org-{domain}")
        
        frontmatter_lines.append('tags:')
        for tag in tags:
            frontmatter_lines.append(f'  - "{tag}"')
        
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
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
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
            # Handle both string and list formats
            if isinstance(action_items, str):
                # Parse the formatted action items string
                parsed_items = self._parse_action_items_string(action_items)
                for item in parsed_items:
                    summary_lines.append(f'- [ ] {item}')
            else:
                # If it's a list, iterate through items
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
        
        # Get unique speakers for summary
        speakers = set()
        for sentence in sentences:
            speakers.add(sentence.get('speaker_name', 'Unknown Speaker'))
        
        transcript_lines = [
            '## Transcript',
            '',
            f'**Participants:** {", ".join(sorted(speakers))}',
            f'**Total Duration:** {self._format_duration_from_sentences(sentences)}',
            '',
            '<details>',
            '<summary>Click to expand full transcript</summary>',
            ''
        ]
        
        # Group sentences by speaker for better readability
        current_speaker = None
        current_speaker_text = []
        current_start_time = None
        
        for sentence in sentences:
            speaker_name = sentence.get('speaker_name', 'Unknown Speaker')
            text = sentence.get('text', '')
            start_time = sentence.get('start_time', 0)
            
            # If speaker changed, write previous speaker's content
            if current_speaker and current_speaker != speaker_name:
                if current_speaker_text:
                    combined_text = ' '.join(current_speaker_text)
                    timestamp = self._format_timestamp(current_start_time)
                    transcript_lines.append(f'**{current_speaker}** `[{timestamp}]`: {combined_text}')
                    transcript_lines.append('')
                current_speaker_text = []
                current_start_time = start_time
            
            # Update current speaker and add text
            if current_speaker != speaker_name:
                current_start_time = start_time
            current_speaker = speaker_name
            current_speaker_text.append(text)
        
        # Write the last speaker's content
        if current_speaker and current_speaker_text:
            combined_text = ' '.join(current_speaker_text)
            timestamp = self._format_timestamp(current_start_time)
            transcript_lines.append(f'**{current_speaker}** `[{timestamp}]`: {combined_text}')
        
        transcript_lines.extend(['', '</details>'])
        
        return '\n'.join(transcript_lines)
    
    def _parse_action_items_string(self, action_items_str):
        """
        Parse a formatted action items string into individual action items.
        
        Expected format:
        **Person Name**
        Action item 1 (timestamp)
        Action item 2 (timestamp)
        
        **Another Person**
        Another action item (timestamp)
        """
        items = []
        if not action_items_str.strip():
            return items
        
        # Split by person sections (lines starting with **)
        sections = []
        current_section = []
        
        for line in action_items_str.strip().split('\n'):
            line = line.strip()
            if line.startswith('**') and line.endswith('**'):
                # Start of new person section
                if current_section:
                    sections.append(current_section)
                current_section = [line]
            elif line and current_section:
                # Action item for current person
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
        
        # Process each person's section
        for section in sections:
            if len(section) < 2:
                continue
            
            person = section[0]  # **Person Name**
            action_lines = section[1:]
            
            for action_line in action_lines:
                if action_line.strip():
                    # Combine person and action
                    items.append(f"{person} {action_line}")
        
        return items
    
    def _format_timestamp(self, start_time):
        """Format timestamp to MM:SS format."""
        if start_time is None:
            return "00:00"
        mins = int(start_time // 60)
        secs = int(start_time % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _format_duration_from_sentences(self, sentences):
        """Calculate total duration from sentences."""
        if not sentences:
            return "0m 0s"
        
        # Get the last sentence's end time
        last_sentence = sentences[-1]
        end_time = last_sentence.get('end_time', last_sentence.get('start_time', 0))
        
        mins = int(end_time // 60)
        secs = int(end_time % 60)
        return f"{mins}m {secs}s"
    
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