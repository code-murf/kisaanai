# Comprehensive MCP Server Usage Rules

## Overview

This document provides complete guidelines for using all available MCP (Model Context Protocol) servers in this project. MCP servers extend the capabilities of Kilo Code by providing additional tools and resources.

---

## Table of Contents

1. [Global Guidelines](#global-guidelines)
2. [Memory MCP Server](#1-memory-mcp-server)
3. [Playwright MCP Server](#2-playwright-mcp-server)
4. [Context7 MCP Server](#3-context7-mcp-server)
5. [Filesystem MCP Server](#4-filesystem-mcp-server)
6. [MagicUI MCP Server](#5-magicui-mcp-server)
7. [Tool Selection Matrix](#tool-selection-matrix)
8. [Security Rules](#security-rules)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Global Guidelines

### Core Principles
- **Use tools only when required** - Do not overuse MCP tools
- **Prefer read-only operations first** - Always read before writing
- **Never expose API keys or secrets** - Keep credentials secure
- **Confirm before destructive actions** - Ask user before deletions
- **Execute one tool at a time** - Wait for response before next call
- **Do not fabricate tool outputs** - Always return real results
- **Follow tool-specific rules** - Each MCP has unique requirements

---

## 1. Memory MCP Server

**Purpose:** Persistent knowledge graph storage for entities, relations, and observations.

### Available Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `mcp--memory--create_entities` | Create new entities in knowledge graph | Storing project information, decisions, code reviews |
| `mcp--memory--create_relations` | Create relations between entities | Linking related concepts, dependencies |
| `mcp--memory--add_observations` | Add observations to existing entities | Updating entity information |
| `mcp--memory--delete_entities` | Delete entities and their relations | Removing outdated information |
| `mcp--memory--delete_observations` | Delete specific observations | Correcting specific data points |
| `mcp--memory--delete_relations` | Delete relations between entities | Removing outdated connections |
| `mcp--memory--read_graph` | Read entire knowledge graph | Retrieving all stored information |
| `mcp--memory--search_nodes` | Search for nodes by query | Finding specific entities |
| `mcp--memory--open_nodes` | Open specific nodes by name | Retrieving detailed entity data |

### Usage Rules

```markdown
## Memory Server Rules

### When to Use
- Storing project context and decisions
- Recording code review findings
- Tracking architectural decisions
- Maintaining entity relationships

### Best Practices
1. Use descriptive entity names: "Code Review 2026-02-14" not "review1"
2. Use appropriate entity types: "security_issue", "code_quality_issue", "project"
3. Create relations in active voice: "identified", "depends_on", "blocks"
4. Add observations as discrete facts, not paragraphs

### Example Usage
```json
{
  "entities": [
    {
      "name": "User Authentication Module",
      "entityType": "feature",
      "observations": [
        "Implements JWT-based authentication",
        "Located in backend/app/services/auth.py",
        "Depends on python-jose library"
      ]
    }
  ]
}
```

### Restrictions
- Do not store sensitive data (API keys, passwords)
- Do not create duplicate entities
- Use search before creating new entities

---

## 2. Playwright MCP Server

**Purpose:** Browser automation for web navigation, screenshots, and interactions.

### Available Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `mcp--playwright--browser_navigate` | Navigate to URL | Opening web pages |
| `mcp--playwright--browser_click` | Click on elements | Button clicks, link navigation |
| `mcp--playwright--browser_type` | Type text into elements | Form filling, search inputs |
| `mcp--playwright--browser_fill_form` | Fill multiple form fields | Complete form submission |
| `mcp--playwright--browser_select_option` | Select dropdown option | Select menus |
| `mcp--playwright--browser_hover` | Hover over element | Tooltips, hover states |
| `mcp--playwright--browser_snapshot` | Get accessibility snapshot | Page structure analysis |
| `mcp--playwright--browser_take_screenshot` | Capture page screenshot | Visual documentation |
| `mcp--playwright--browser_evaluate` | Execute JavaScript | Custom page interactions |
| `mcp--playwright--browser_tabs` | Manage browser tabs | Multi-tab operations |
| `mcp--playwright--browser_close` | Close browser | Cleanup |
| `mcp--playwright--browser_wait_for` | Wait for condition | Async content loading |
| `mcp--playwright--browser_press_key` | Press keyboard key | Keyboard navigation |
| `mcp--playwright--browser_drag` | Drag and drop | Drag operations |
| `mcp--playwright--browser_file_upload` | Upload files | File input handling |
| `mcp--playwright--browser_handle_dialog` | Handle alerts/dialogs | Popup handling |
| `mcp--playwright--browser_console_messages` | Get console logs | Debugging |
| `mcp--playwright--browser_network_requests` | Get network requests | API debugging |
| `mcp--playwright--browser_resize` | Resize browser window | Responsive testing |
| `mcp--playwright--browser_navigate_back` | Go to previous page | Navigation |
| `mcp--playwright--browser_install` | Install browser | Setup |

### Usage Rules

```markdown
## Playwright Server Rules

### When to Use
- Website navigation and testing
- Taking screenshots for documentation
- Form filling and submission
- Web scraping (with permission)
- UI/UX testing
- Responsive design verification

### Workflow
1. Navigate to page: browser_navigate
2. Get snapshot: browser_snapshot
3. Interact with elements: browser_click, browser_type
4. Verify results: browser_snapshot or browser_take_screenshot
5. Close when done: browser_close

### Element Reference Format
Use the ref attribute from snapshots:
- Click: ref=e3 (from snapshot)
- Type: ref=e5 (from snapshot)

### Best Practices
1. Always use browser_snapshot before interactions
2. Use refs from snapshots for element targeting
3. Close browser when task is complete
4. Handle async content with browser_wait_for
5. Take screenshots for documentation

### Restrictions
- Do not use --no-sandbox flag
- Prefer headless mode for automation
- Avoid login automation unless necessary
- Respect robots.txt and terms of service
- Do not scrape protected content

### Example Flow
```
1. browser_navigate(url="https://example.com")
2. browser_snapshot() -> get refs
3. browser_click(element="Submit button", ref="e10")
4. browser_wait_for(text="Success")
5. browser_take_screenshot(filename="result.png")
6. browser_close()
```

---

## 3. Context7 MCP Server

**Purpose:** Retrieve up-to-date documentation and code examples for libraries and frameworks.

### Available Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `mcp--context7--resolve___library___id` | Resolve library name to Context7 ID | Finding library documentation |
| `mcp--context7--query___docs` | Query documentation for library | Getting code examples and API docs |

### Usage Rules

```markdown
## Context7 Server Rules

### When to Use
- Getting library documentation
- Finding framework references
- API usage help
- Code examples for libraries

### Mandatory Flow
1. First: resolve-library-id
   - Input: library name (e.g., "fastapi", "react")
   - Output: Context7-compatible library ID

2. Then: query-docs
   - Input: library ID from step 1
   - Output: Documentation and code examples

### Limits
- Maximum 3 calls per query
- Do not send secrets in queries

### Best Practices
1. Always call resolve-library-id first
2. Use specific library names
3. Formulate specific queries
4. Include relevant context in queries

### Example Usage
```
Step 1: resolve-library-id
  libraryName: "fastapi"
  query: "How to create a FastAPI route with authentication"

Step 2: query-docs
  libraryId: "/websites/fastapi_tiangolo"
  query: "How to create a FastAPI route with authentication"
```

### Query Formulation Tips
- Be specific about what you need
- Include context about your use case
- Ask about specific features or patterns

### Restrictions
- Do not include API keys in queries
- Do not include sensitive project data
- Limit to 3 calls per question

---

## 4. Filesystem MCP Server

**Purpose:** File system operations including read, write, search, and manage files.

### Available Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `mcp--filesystem--read_file` | Read single file content | Viewing file contents |
| `mcp--filesystem--read_multiple_files` | Read multiple files | Comparing files |
| `mcp--filesystem--write_file` | Create or overwrite file | Creating new files |
| `mcp--filesystem--edit_file` | Make line-based edits | Modifying existing files |
| `mcp--filesystem--create_directory` | Create directory | Setting up project structure |
| `mcp--filesystem--list_directory` | List directory contents | Exploring project structure |
| `mcp--filesystem--directory_tree` | Get JSON tree view | Understanding project layout |
| `mcp--filesystem--move_file` | Move or rename files | Reorganizing files |
| `mcp--filesystem--search_files` | Search by pattern | Finding specific files |
| `mcp--filesystem--get_file_info` | Get file metadata | Checking file details |
| `mcp--filesystem--list_allowed_directories` | List accessible paths | Understanding permissions |

### Usage Rules

```markdown
## Filesystem Server Rules

### Allowed Paths
- C:\Users\Asus\Desktop\Aiforbharat (primary workspace)

### When to Use
- Reading source code files
- Creating new files
- Editing existing code
- Searching for files
- Managing project structure

### Best Practices
1. Always read file before editing
2. Use dryRun for major edits
3. Never delete files automatically
4. Use list_directory to explore first
5. Use search_files to find specific files

### File Operations Flow
1. Read: Understand current state
2. Edit/Write: Make changes
3. Verify: Read again to confirm

### Edit File Usage
```json
{
  "path": "/path/to/file.txt",
  "edits": [
    {
      "oldText": "exact text to find",
      "newText": "replacement text"
    }
  ],
  "dryRun": false
}
```

### Restrictions
- Only operate within allowed directories
- Always read before editing
- Use dryRun for preview before major changes
- Never delete files without user confirmation
- Do not expose sensitive file contents

### Example Workflows

#### Creating a New File
```
1. list_directory(path="/project/src") -> understand structure
2. write_file(path="/project/src/newfile.ts", content="...")
```

#### Editing Existing File
```
1. read_file(path="/project/src/existing.ts")
2. edit_file(path="/project/src/existing.ts", edits=[...])
```

#### Finding Files
```
1. search_files(path="/project", pattern="*.test.ts")
2. read_multiple_files(paths=[...])
```

---

## 5. MagicUI MCP Server

**Purpose:** Access Magic UI components for building modern user interfaces.

### Available Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `mcp--magicui--getUIComponents` | List all UI components | Discovering available components |
| `mcp--magicui--getComponents` | Get component implementations | marquee, terminal, bento-grid, etc. |
| `mcp--magicui--getDeviceMocks` | Get device mock components | safari, iphone-15-pro, android |
| `mcp--magicui--getSpecialEffects` | Get special effect components | animated-beam, border-beam, meteors |
| `mcp--magicui--getAnimations` | Get animation components | blur-fade animations |
| `mcp--magicui--getTextAnimations` | Get text animation components | text-animate, aurora-text, etc. |
| `mcp--magicui--getButtons` | Get button components | rainbow-button, shimmer-button, etc. |
| `mcp--magicui--getBackgrounds` | Get background components | warp-background, grid-pattern, etc. |

### Usage Rules

```markdown
## MagicUI Server Rules

### When to Use
- Building React/Next.js UI components
- Adding animations and effects
- Creating visually appealing interfaces
- Implementing modern UI patterns

### Component Categories
1. **UI Components**: marquee, terminal, bento-grid, dock, globe
2. **Device Mocks**: safari, iphone-15-pro, android
3. **Special Effects**: animated-beam, border-beam, meteors, confetti
4. **Animations**: blur-fade transitions
5. **Text Animations**: text-animate, aurora-text, number-ticker
6. **Buttons**: rainbow-button, shimmer-button, pulsating-button
7. **Backgrounds**: warp-background, flickering-grid, dot-pattern

### Best Practices
1. Call appropriate getter for component type
2. Review component implementation before use
3. Ensure dependencies are installed
4. Customize styles as needed

### Example Usage
```
1. getUIComponents() -> see all available
2. getComponents() -> get specific component code
3. Integrate into React/Next.js project
```

---

## Tool Selection Matrix

| Task Type | Primary Tool | Alternative |
|-----------|--------------|-------------|
| Website automation | Playwright | - |
| File operations | Filesystem | - |
| Library documentation | Context7 | - |
| Knowledge storage | Memory | - |
| UI components | MagicUI | - |
| Web scraping | Playwright | - |
| Code examples | Context7 | - |
| Screenshot capture | Playwright | - |
| Project structure | Filesystem | - |
| Entity relationships | Memory | - |

---

## Security Rules

### Absolute Prohibitions
- **Never** expose API keys or secrets
- **Never** run shell commands through MCP
- **Never** bypass security checks
- **Never** perform illegal actions
- **Never** scrape protected content without permission

### Data Handling
- Do not store sensitive data in Memory MCP
- Do not include credentials in Context7 queries
- Do not expose file contents with secrets
- Do not automate login without necessity

### Confirmation Required
- Before deleting files
- Before destructive edits
- Before major changes
- Before external API calls

---

## Error Handling

### Standard Error Flow
```
1. Try tool operation
2. If fails, retry once
3. If still fails, report error to user
4. Do not guess or fabricate results
```

### Error Reporting Format
```markdown
**Error**: [Tool name] failed
**Details**: [Error message]
**Action**: [What was attempted]
**Suggestion**: [Recommended next step]
```

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Path not allowed" | Outside allowed directories | Use paths within allowed directories |
| "Element not found" | Invalid ref or selector | Take new snapshot, use correct ref |
| "Library not found" | Invalid library name | Check spelling, try alternative name |
| "File not found" | Path doesn't exist | Verify path with list_directory |
| "Rate limited" | Too many requests | Wait before retrying |

---

## Best Practices

### General
1. **Plan before executing** - Know what you need before using tools
2. **Use read-only first** - Understand current state before changes
3. **One tool at a time** - Wait for response before next call
4. **Verify results** - Confirm operations succeeded
5. **Handle errors gracefully** - Report issues clearly

### Memory MCP
1. Search before creating entities
2. Use descriptive names and types
3. Create meaningful relations
4. Keep observations discrete and factual

### Playwright MCP
1. Always get snapshot before interactions
2. Use refs from snapshots
3. Wait for async content
4. Close browser when done

### Context7 MCP
1. Always resolve library ID first
2. Be specific in queries
3. Limit to 3 calls per question
4. Don't include sensitive data

### Filesystem MCP
1. Read before edit
2. Use dryRun for major changes
3. Confirm before deletions
4. Stay within allowed paths

---

## Quick Reference

### Memory
```
create_entities -> Store information
search_nodes -> Find information
read_graph -> Get everything
```

### Playwright
```
browser_navigate -> Open page
browser_snapshot -> Get structure
browser_click -> Interact
browser_close -> Cleanup
```

### Context7
```
resolve-library-id -> Find library
query-docs -> Get documentation
```

### Filesystem
```
read_file -> View content
write_file -> Create/overwrite
edit_file -> Modify
search_files -> Find files
```

### MagicUI
```
getUIComponents -> List all
get[Category] -> Get specific type
```

---

## Configuration

Current MCP servers configured:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.38"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/Asus/Desktop/Aiforbharat"]
    },
    "magicui": {
      "command": "npx",
      "args": ["-y", "@magicuidesign/mcp@latest"]
    }
  }
}
```

---

*Last Updated: 2026-02-14*
*Version: 1.0.0*
