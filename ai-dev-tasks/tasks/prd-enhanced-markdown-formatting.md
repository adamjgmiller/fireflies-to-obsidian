# PRD: Enhanced Markdown Formatting for Fireflies-to-Obsidian

## Introduction/Overview

The Fireflies-to-Obsidian sync tool currently creates markdown files from meeting data but doesn't utilize all available fields from the Fireflies API. This enhancement will improve the markdown formatting to include additional valuable information, create better structure for Obsidian workflows, and add testing capabilities to ensure quality output.

## Goals

1. Utilize all valuable fields from the Fireflies API response to create richer meeting notes
2. Improve the organization and readability of meeting notes in Obsidian
3. Add speaker statistics and meeting insights for better meeting analysis
4. Implement comprehensive testing to ensure markdown quality
5. Maintain backward compatibility while enhancing the format

## User Stories

1. **As a meeting participant**, I want to see a one-line summary (gist) at the top of my notes so that I can quickly understand what the meeting was about without reading the entire document.

2. **As a manager**, I want to see speaker statistics (talk time, participation) so that I can understand meeting dynamics and ensure balanced participation.

3. **As a team member**, I want detailed attendee information (names, emails, locations) so that I can easily follow up with specific participants.

4. **As a user searching through meetings**, I want topics discussed as a separate section so that I can quickly find meetings about specific subjects.

5. **As someone reviewing long meetings**, I want chapter navigation based on transcript chapters so that I can jump to specific parts of the discussion.

6. **As a quality-conscious user**, I want the system to validate the markdown output so that I know my notes are properly formatted.

## Functional Requirements

1. **Enhanced Frontmatter**
   - Add `gist` field with one-line meeting summary
   - Add `meeting_type` field when available
   - Add `total_speakers` count
   - Keep all existing frontmatter fields

2. **Improved Attendee Section**
   - Display detailed attendee information when available (name, email, location)
   - Fall back to simple participant list when detailed info is not available
   - Format as a structured list with clear visual hierarchy

3. **Enhanced Summary Section**
   - Add "Meeting Gist" as the first item for quick understanding
   - Include "Topics Discussed" as a separate subsection when available
   - Add both `bullet_gist` and `shorthand_bullet` when they differ significantly
   - Preserve existing overview and action items sections

4. **Speaker Statistics Section** (New)
   - Calculate and display talk time for each speaker
   - Show percentage of meeting time for each speaker
   - Display total number of statements per speaker
   - Format as a clean table or structured list

5. **Chapter Navigation** (New, when available)
   - Create a table of contents when transcript_chapters has data
   - Include timestamps and chapter titles
   - Make chapters clickable links to transcript sections

6. **Enhanced Transcript Section**
   - Add speaker statistics summary at the top
   - Maintain current speaker grouping functionality
   - Add chapter markers in transcript when chapters are available

7. **Testing and Validation**
   - Save a copy of each generated markdown file to a temporary test directory
   - Validate markdown syntax
   - Ensure all required sections are present
   - Log any missing or malformed data

8. **Configuration Options**
   - Allow users to enable/disable specific enhancements via config
   - Provide options for speaker statistics format (table vs list)
   - Allow customization of which sections to include

## Non-Goals (Out of Scope)

1. Will NOT modify the existing file naming convention
2. Will NOT change the fundamental structure of the markdown files
3. Will NOT remove any currently included information
4. Will NOT integrate with external services beyond Fireflies and Obsidian
5. Will NOT modify the polling/sync mechanism
6. Will NOT change the state management system

## Design Considerations

1. **Obsidian Compatibility**
   - Ensure all markdown follows Obsidian's flavor
   - Use proper YAML frontmatter format
   - Consider Dataview plugin compatibility for metadata
   - Use collapsible sections for long content

2. **Visual Hierarchy**
   - Use consistent heading levels (H2 for main sections, H3 for subsections)
   - Employ markdown tables where appropriate
   - Use blockquotes for important callouts
   - Maintain clean spacing between sections

3. **File Size Management**
   - Keep transcript in collapsible section
   - Limit speaker statistics to essential information
   - Avoid duplicating information unnecessarily

## Technical Considerations

1. **Backward Compatibility**
   - New fields should be optional
   - Existing section structure should be preserved
   - Handle null/missing fields gracefully

2. **Performance**
   - Calculate speaker statistics efficiently
   - Avoid multiple passes through transcript data
   - Cache calculated values when possible

3. **Testing Infrastructure**
   - Create a `test_output` directory for validation
   - Implement markdown validation using existing libraries
   - Add unit tests for new formatting functions
   - Create integration tests with sample API responses

4. **Error Handling**
   - Gracefully handle missing or malformed API data
   - Log warnings for missing expected fields
   - Never fail to create a note due to enhancement issues

## Success Metrics

1. **Completeness**: 100% of available API fields are evaluated for inclusion
2. **Quality**: Zero markdown syntax errors in generated files
3. **Performance**: No measurable increase in sync time (< 5% overhead)
4. **User Satisfaction**: Enhanced notes provide more value without cluttering
5. **Reliability**: No increase in failed sync operations
6. **Testing**: 95%+ code coverage for new formatting functions

## Open Questions

1. Should we make speaker statistics calculation optional for performance reasons?
2. What's the preferred format for displaying speaker statistics (table, chart, list)?
3. Should we add support for custom templates in the future?
4. How should we handle meetings with more than 20 attendees?
5. Should the test output directory be configurable or always use a temp directory?
6. Do we need to support multiple language transcripts differently?
7. Should we add meeting duration breakdown by topic/chapter when available?