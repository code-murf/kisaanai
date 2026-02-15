# MCP Usage Rules & Guide

This document outlines the rules and best practices for using the configured Model Context Protocol (MCP) servers in this environment.

## 1. Filesystem MCP (`filesystem`)

**Purpose**: Access and manipulate files within the allowed directory (`C:/Users/Asus/Desktop/Aiforbharat`).

**Tools**:
- `list_directory`: List contents of a directory.
- `read_file`: Read content of a file.
- `write_file`: Create or overwrite a file.
- `search_files`: Search for files matching a pattern.
- `get_file_info`: Get metadata for a file.

**Rules**:
- **Always use absolute paths**.
- **Verify paths** exist before attempting to read or write, unless creating a new file.
- **Respect the allowed directory**. Operations outside `C:/Users/Asus/Desktop/Aiforbharat` may fail.

**Example**:
```json
{
  "name": "list_directory",
  "args": {
    "path": "C:/Users/Asus/Desktop/Aiforbharat/src"
  }
}
```

## 2. Memory MCP (`memory`)

**Purpose**: persistent knowledge graph for storing and retrieving structured information across sessions.

**Tools**:
- `create_entities`: Create nodes in the graph.
- `create_relations`: Create edges between nodes.
- `search_nodes`: Search for entities.
- `read_graph`: Read the entire graph (use with caution on large graphs).
- `delete_entities`: Remove entities.

**Rules**:
- **Use for long-term project context**, not temporary data.
- **Structure entities logically** (e.g., `feature`, `bug`, `decision`).
- **Clean up** test entities after verification.

**Example**:
```json
{
  "name": "create_entities",
  "args": {
    "entities": [
      {
        "name": "UserAuthFeature",
        "entityType": "Feature",
        "observations": ["Implements JWT authentication"]
      }
    ]
  }
}
```

## 3. Context7 MCP (`context7`)

**Purpose**: Retrieve documentation and library information for coding tasks.

**Tools**:
- `resolve-library-id`: Find the ID for a library (e.g., 'react').
- `query-docs`: Get documentation for a specific library ID.

**Rules**:
- **Resolve ID first**. Use `resolve-library-id` to get the correct ID before querying docs.
- **Be specific** in `query-docs` to get relevant results.

**Example**:
```json
{
  "name": "resolve-library-id",
  "args": {
    "libraryName": "react",
    "query": "react hooks"
  }
}
```

## 4. Playwright MCP (`playwright`)

**Purpose**: Browser automation for testing and verifying web applications.

**Tools**:
- `browser_navigate`: Go to a URL.
- `browser_take_screenshot`: Capture the current page.
- `browser_click`, `browser_type`, `browser_fill_form`: Interact with elements.

**Rules**:
- **Always close the browser** (or pages) when finished to free resources.
- **Use `browser_navigate`** before attempting interactions.
- **Use screenshots** to verify visual state.

**Example**:
```json
{
  "name": "browser_navigate",
  "args": {
    "url": "http://localhost:3000"
  }
}
```

## 5. Magic UI MCP (`magicui`)

**Purpose**: Access components and implementation details from the Magic UI library.

**Tools**:
- `getUIComponents`: Provides a comprehensive list of all Magic UI components.
- `getComponents`: Provides implementation details for marquee, terminal, hero-video-dialog, bento-grid, animated-list, dock, globe, tweet-card, client-tweet-card, orbiting-circles, avatar-circles, icon-cloud, animated-circular-progress-bar, file-tree, code-comparison, script-copy-btn, scroll-progress, lens, pointer components.
- `getDeviceMocks`: Provides implementation details for safari, iphone-15-pro, android components.
- `getSpecialEffects`: Provides implementation details for animated-beam, border-beam, shine-border, magic-card, meteors, neon-gradient-card, confetti, particles, cool-mode, scratch-to-reveal components.
- `getAnimations`: Provides implementation details for blur-fade components.
- `getTextAnimations`: Provides implementation details for text-animate, line-shadow-text, aurora-text, number-ticker, animated-shiny-text, animated-gradient-text, text-reveal, hyper-text, word-rotate, typing-animation, scroll-based-velocity, flip-text, box-reveal, sparkles-text, morphing-text, spinning-text components.
- `getButtons`: Provides implementation details for rainbow-button, shimmer-button, shiny-button, interactive-hover-button, animated-subscribe-button, pulsating-button, ripple-button components.
- `getBackgrounds`: Provides implementation details for warp-background, flickering-grid, animated-grid-pattern, retro-grid, ripple, dot-pattern, grid-pattern, interactive-grid-pattern components.

**Rules**:
- **Check component availability** with `getUIComponents` if unsure.
- **Use for frontend development** to quickly get high-quality UI code.

**Example**:
```json
{
  "name": "getComponents",
  "args": {
    "component": "marquee"
  }
}
```

---
**General Best Practices**:
- **Error Handling**: Always check tool outputs for errors.
- **Sequential Operations**: For dependent tasks (e.g., navigate -> click), ensure sequential execution.
- **Resource Management**: Clean up created resources (files, entities, browser pages).

---

# Verification Log (2026-02-15)

System verification performed at 03:33.

1.  **Filesystem MCP**: ✅ **VERIFIED**
    - Status: Active
    - Test: Successfully listed directory contents of workspace.

2.  **Memory MCP**: ✅ **VERIFIED**
    - Status: Active
    - Test: Successfully connected to knowledge graph.

3.  **Context7 MCP**: ✅ **VERIFIED**
    - Status: Active
    - Test: Successfully resolved library ID for 'react'.

4.  **Playwright MCP**: ✅ **VERIFIED**
    - Status: Active
    - Test: Successfully launched browser and navigated to google.com.

5.  **Magic UI MCP**: ⚠️ **PENDING RESTART**
    - Status: Configured Correctly
    - Note: Configuration files (`mcp_settings.json`, `mcp_config.json`) have been fixed.
    - Action Required: **Restart VS Code/MCP Client** to enable this server.
