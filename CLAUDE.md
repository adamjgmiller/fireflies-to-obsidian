# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a "fireflies-to-obsidian" project that appears to be in initial setup phase. The project follows a structured AI-assisted development workflow using:

- **adams-rules/**: Contains project-specific development rules and guidelines
- **ai-dev-tasks/**: Structured workflow system for AI-assisted feature development with PRD (Product Requirements Document) creation and task management
- **ai-dev-tasks/tasks/**: Directory for storing PRDs and task lists

## Development Workflow

This project follows a specific AI development process:

1. **PRD Creation**: Use `ai-dev-tasks/create-prd.mdc` to create Product Requirements Documents
2. **Task Generation**: Use `ai-dev-tasks/generate-tasks-from-prd.mdc` to break PRDs into actionable tasks
3. **Implementation**: Use `ai-dev-tasks/process-task-list.mdc` for systematic task completion

## Key Rules to Follow

### Environment Management
- Always use virtual environments when possible
- Minimize impact and reliance on global environment
- Ask user before suggesting exceptions

### Documentation Requirements
- Update README.md proportional to task impact after every completed task
- Create/update relevant .md files in `/ai-notes` folder when learning important codebase information
- Follow README template structure from `adams-rules/README-template.md`

### AI Development Process
- For non-trivial tasks, always:
  1. Create PRD using `/ai-dev-tasks/create-prd.mdc`
  2. Generate task list using `/ai-dev-tasks/generate-tasks.mdc`
  3. Process tasks using `/ai-dev-tasks/process-task-list.mdc`

### File Management
- Save PRDs as `prd-[feature-name].md` in `/ai-dev-tasks/tasks/`
- Reference adams-rules files for project-specific guidelines
- Maintain living documentation with current examples

## Project Status

Currently in initial setup phase with foundational AI development workflow structure in place.