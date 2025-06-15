# PRD: Fireflies to Obsidian Sync Tool

## Introduction/Overview

This tool addresses the critical need to automatically sync Fireflies.ai meeting transcripts into Obsidian for immediate access and long-term knowledge management. Currently, users must manually copy meeting notes from Fireflies to Obsidian, which is time-consuming and prone to being forgotten. This local polling service will run on macOS, checking for new meetings every 15 seconds and creating well-formatted Markdown notes in the user's Obsidian vault.

## Goals

1. **Automate Meeting Import**: Eliminate manual copying by automatically syncing all Fireflies meetings to Obsidian
2. **Rapid Access**: Make meeting transcripts available in Obsidian within 15-30 seconds of processing completion
3. **Organized Storage**: Create a clean, searchable archive of all meetings in a dedicated Obsidian folder
4. **AI-Ready Formatting**: Format notes optimally for both human reading and AI ingestion
5. **Reliable Operation**: Run continuously with minimal errors and clear status notifications. 

## User Stories

1. **As a meeting participant**, I want my Fireflies transcripts automatically added to my Obsidian vault so that I can reference them immediately without manual intervention.

2. **As a knowledge worker**, I want my meeting notes formatted consistently so that I can quickly scan for important information and my AI tools can process them effectively.

3. **As a power user**, I want to test the sync process with specific meetings so that I can verify the tool works correctly before running it on all meetings. I also want to be able to run the sync once, eventually, with all my historical meetings.

4. **As a Mac user**, I want clear notifications about sync status so that I know the tool is working without having to check logs.

5. **As an Obsidian user**, I want meetings organized chronologically by filename so that I can easily browse my meeting history.

## Functional Requirements

1. **The system must poll Fireflies API every 15 seconds** to check for new meetings
2. **The system must sync all meetings after June 13, 2024** on initial run to avoid overwhelming the system
3. **The system must track processed meetings** to avoid creating duplicate notes
4. **The system must create a "Fireflies" folder** in the Obsidian vault if it doesn't exist
5. **The system must name files using format**: `YYYY-MM-DD-HH-MM-[Meeting Title].md` for chronological sorting
6. **The system must include comprehensive metadata** in YAML frontmatter including:
   - Meeting ID
   - Title
   - Date and time
   - Duration
   - Host information
   - All participants
   - Meeting URL
7. **The system must format transcripts with clear speaker sections**, grouping consecutive statements by the same speaker under a single header
8. **The system must provide a test mode** that processes specific Meeting IDs from configuration
9. **The system must show macOS notifications** for sync status (new meetings found, sync complete, errors)
10. **The system must handle all meetings the user has access to**, not just meetings they organized
11. **The system must log all operations** to a file for debugging
12. **The system must gracefully handle API rate limits** with exponential backoff
13. **The system must continue running** even if individual meeting syncs fail

## Non-Goals (Out of Scope)

1. **Will NOT update existing notes** - once a meeting is synced, it won't be modified
2. **Will NOT download audio recordings** - only text content will be synced
3. **Will NOT provide a graphical user interface** - command-line only
4. **Will NOT support two-way sync** - changes in Obsidian won't sync back to Fireflies
5. **Will NOT delete meetings** from either Fireflies or Obsidian
6. **Will NOT support real-time webhooks** in this version
7. **Will NOT sync meetings before June 13, 2024** automatically (manual override possible)

## Design Considerations

### File Format Structure
```markdown
---
fireflies_id: abc123
title: Project Planning Meeting
date: 2024-06-15
time: "14:30"
duration_minutes: 45
host: John Smith (john@example.com)
participants:
  - John Smith (john@example.com)
  - Jane Doe (jane@example.com)
  - Bob Wilson (bob@example.com)
meeting_url: https://fireflies.ai/view/abc123
tags: [fireflies, meeting, project-planning]
synced_at: 2024-06-15T15:30:00Z
---

# Project Planning Meeting

## 📅 Meeting Details
**Date**: Saturday, June 15, 2024  
**Time**: 2:30 PM - 3:15 PM (45 minutes)  
**Host**: John Smith  
**Participants**: 3 people

## 👥 Attendees
- John Smith (john@example.com) - Host
- Jane Doe (jane@example.com)
- Bob Wilson (bob@example.com)

## 📝 Summary
[AI-generated summary from Fireflies]

## 🎯 Action Items
- [ ] John to create project timeline by Monday
- [ ] Jane to review budget proposal
- [ ] Bob to schedule follow-up with stakeholders

## 💡 Key Topics (from Fireflies)
### Project Timeline Discussion (0:05 - 0:15)
[Topic summary]

### Budget Considerations (0:15 - 0:30)
[Topic summary]

## 📋 Transcript

### John Smith (0:00 - 0:05)
Welcome everyone to today's project planning meeting. I wanted to start by reviewing where we are with the timeline.

As you all know, we've been working on this for the past two months and we need to finalize our approach for Q3.

### Jane Doe (0:05 - 0:08)
Thanks John. I've been looking at the budget implications and I think we need to be careful about scope creep.

The initial proposal was for X, but now we're talking about Y and Z as well.

### Bob Wilson (0:08 - 0:12)
[Continues with formatted transcript...]
```

### Notification Format
- **New Meeting Found**: "🎙️ New Fireflies meeting: [Title]"
- **Sync Complete**: "✅ Synced [X] meetings to Obsidian"
- **Error**: "⚠️ Failed to sync meeting: [Title] - Check logs"

## Technical Considerations

1. **Language**: Python 3.13.5 for better async support and type hints
2. **State Storage**: JSON file for simplicity, with option to migrate to SQLite if needed
3. **API Client**: Use `httpx` for async HTTP requests with GraphQL support
4. **Configuration**: `.env` file for sensitive data, `config.yaml` for user preferences
5. **Error Handling**: Implement circuit breaker pattern for API failures
6. **Performance**: Process meetings in batches of 5 to balance speed and API limits
7. **Security**: Store API keys in local config file

## Success Metrics

1. **Zero Manual Intervention**: 100% of meetings automatically synced without user action
2. **Sync Speed**: New meetings appear in Obsidian within 30 seconds of availability
3. **Reliability**: Tool runs for 30+ days without crashing or requiring restart
4. **Error Rate**: Less than 1% of meetings fail to sync on first attempt
5. **User Satisfaction**: Eliminates the need to ever open Fireflies web interface for meeting review

## Open Questions

1. **Historical Sync**: Should we provide a separate command to sync ALL historical meetings (pre-June 13)?
2. **Meeting Types**: Are there certain types of meetings (1-on-1s, team meetings, external) that need special handling?
3. **Duplicate Handling**: If a meeting title changes in Fireflies, should we create a new note or have a strategy to handle this?
4. **Performance**: Is 15-second polling too aggressive? Would 30 or 60 seconds be acceptable?
5. **Search Integration**: Should we add special markers or tags to optimize Obsidian search?
6. **Template Customization**: Should users be able to customize the Markdown template in future versions?
7. **Multi-vault Support**: Will you ever need to sync to multiple Obsidian vaults?