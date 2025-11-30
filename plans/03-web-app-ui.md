# Plan 03: Web Application UI

## Overview
This plan implements the complete web application frontend using jQuery, jQuery UI, Bootstrap, and CodeMirror. This includes the project selector, session editor, snippet browser, and all modal dialogs.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Backend API endpoints working

## Module Dependencies
- app.py (API endpoints)
- templates/base.html
- Bootstrap, jQuery, jQuery UI, CodeMirror from CDN

## Tasks

### Task 3.1: Base Layout and Navigation

#### 3.1.1 - Implement: HTML structure and base layout
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Update templates/index.html with complete layout:
  - Header bar with logo, project selector, New/Export buttons
  - Left sidebar for snippet browser
  - Main content area with tab navigation
  - Loading spinner overlay
- Create static/css/main.css with:
  - Layout styles (header, sidebar, main area)
  - Responsive grid using Bootstrap
  - Color scheme and typography
  - Spacing and padding
- Create static/js/utils.js with utility functions:
  - `showLoading()` / `hideLoading()`
  - `showError(message)`
  - `showSuccess(message)`
  - `debounce(func, wait)`
  - `formatDate(timestamp)`

**Files to Modify**:
- `templates/index.html`

**Files to Create**:
- `static/css/main.css`
- `static/css/widgets.css`
- `static/js/utils.js`

#### 3.1.2 - Test: Layout rendering test
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Layout renders correctly in browser
- All CDN resources load successfully
- CSS is properly applied
- No console errors
- Responsive layout works on different screen sizes
- Loading spinner appears/disappears correctly

#### 3.1.3 - Validate: Base layout review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- HTML is semantic and accessible
- CSS follows best practices
- No layout issues or visual bugs
- All utility functions work correctly

---

### Task 3.2: Project Selector Component

#### 3.2.1 - Implement: Project selector dropdown
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/project.js with:
  - `loadProjects()` - fetches projects from API
  - `selectProject(name)` - loads project and updates UI
  - `createProject()` - shows create project modal
  - `exportProject()` - triggers project export
  - `deleteProject(name)` - confirms and deletes project
  - Project dropdown population
  - Event handlers for selection change
- Project selector dropdown shows:
  - Project name and description
  - Currently selected project highlighted
  - Separator before "Create New..." and "Import..." options
- Auto-loads last selected project from state.json on page load

**Files to Create**:
- `static/js/project.js`

#### 3.2.2 - Test: Project selector functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Project selector loads projects on page load
- Selecting a project loads its session
- Create/Import/Export buttons work
- Dropdown updates when projects are created/deleted
- Selected project persists across page reloads
- Error handling for API failures

#### 3.2.3 - Validate: Project selector review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- AJAX calls are correct
- Error handling is comprehensive
- UI updates smoothly
- No race conditions

---

### Task 3.3: Session Editor - Model Configuration

#### 3.3.1 - Implement: Model configuration section
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `loadSession()` - fetches and displays session
  - `saveSession(debounced=true)` - saves session to API
  - `renderModelConfig(session)` - renders model configuration form
  - Form fields:
    - Model dropdown (hardcoded list of Claude models)
    - Max tokens input (number, 1-200000)
    - Temperature slider (0-1, with value display)
  - Auto-save on change (500ms debounce)
  - Validation messages for out-of-range values

**Files to Create**:
- `static/js/session.js`

#### 3.3.2 - Test: Model configuration functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Model configuration loads from session
- Changes auto-save with debouncing
- Validation prevents invalid values
- UI updates immediately on change
- No excessive API calls

#### 3.3.3 - Validate: Model configuration review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Form inputs work correctly
- Validation is comprehensive
- Auto-save is reliable
- UI is intuitive

---

### Task 3.4: Session Editor - System Prompts Section

#### 3.4.1 - Implement: System prompts collapsible section
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `renderSystemPrompts(systemBlocks)` - renders system prompts section
  - Collapsible section with count: "▼ System Prompts (2)"
  - Each system block shows:
    - Type indicator (text/image icon)
    - Content preview (first 100 chars)
    - Cache control badge if present
    - Edit/Delete buttons
    - Drag handle for reordering
  - jQuery UI Sortable for reordering
  - "Add System Prompt" button opens modal
  - Click on block opens edit modal
  - Collapsed state shows preview text
  - Expand/collapse state saved to state.json

**Files to Modify**:
- `static/js/session.js`

#### 3.4.2 - Test: System prompts section functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- System prompts render correctly
- Collapse/expand works
- Reordering works and auto-saves
- Add/Edit/Delete buttons work
- State persistence works
- Drag handle appears on hover

#### 3.4.3 - Validate: System prompts section review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- UI is responsive and smooth
- Sortable doesn't conflict with other events
- State updates correctly
- No visual glitches

---

### Task 3.5: Session Editor - Tools Section

#### 3.5.1 - Implement: Tools collapsible section
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `renderTools(tools)` - renders tools section
  - Collapsible section with count: "▼ Tools (3)"
  - Each tool shows:
    - Tool name
    - Brief description (first 100 chars)
    - Remove button
  - "Add Tool" dropdown populated from project tools
  - Tool selection adds to session
  - Remove button removes from session and auto-saves
  - Expand/collapse state saved

**Files to Modify**:
- `static/js/session.js`

#### 3.5.2 - Test: Tools section functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Tools render correctly
- Adding tools works
- Removing tools works and auto-saves
- Collapse/expand works
- Tool descriptions are truncated properly

#### 3.5.3 - Validate: Tools section review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Tool management works correctly
- No duplicate tools
- Auto-save works
- UI is clear

---

### Task 3.6: Session Editor - Messages Section

#### 3.6.1 - Implement: Messages collapsible section
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `renderMessages(messages)` - renders messages section
  - Collapsible section with count: "▼ Messages (5)"
  - Each message shows:
    - Role icon (👤 for user, 🤖 for assistant)
    - Content blocks preview
    - Edit/Delete buttons
    - Drag handle for reordering
  - jQuery UI Sortable for reordering
  - "Add Message" button opens message editor modal
  - Click on message opens edit modal
  - Tool use blocks show: 🔧 ToolName (parameters...)
  - Tool result blocks show: ✓ ToolName result or ✗ Error
  - Individual messages can collapse/expand
  - Reordering auto-saves

**Files to Modify**:
- `static/js/session.js`

#### 3.6.2 - Test: Messages section functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Messages render correctly
- Different content block types display properly
- Reordering works and auto-saves
- Add/Edit/Delete works
- Collapse/expand works for section and individual messages
- Drag handle appears correctly

#### 3.6.3 - Validate: Messages section review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Message display is clear and organized
- Reordering is smooth
- Content blocks are properly formatted
- No performance issues with many messages

---

### Task 3.7: Snippet Browser Sidebar

#### 3.7.1 - Implement: Snippet browser tree view
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/snippets.js with:
  - `loadSnippets()` - fetches snippets from API
  - `renderSnippetTree(snippets)` - renders hierarchical tree
  - Tree view with categories and snippets:
    - 📁 Category (collapsible)
    - └─ 📄 Snippet name
  - Click on snippet shows preview tooltip
  - Right-click context menu:
    - Edit Snippet
    - Delete Snippet
    - New Category (on root)
    - Rename Category (on category)
    - Delete Category (on category)
  - Buttons at bottom:
    - [+ New Snippet]
    - [+ New Category]
  - Expand/collapse state persisted to state.json
  - Scroll position persisted

**Files to Create**:
- `static/js/snippets.js`

#### 3.7.2 - Test: Snippet browser functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Snippet tree renders correctly
- Categories expand/collapse
- Click on snippet works
- Right-click menu works
- State persistence works
- Create/delete operations work

#### 3.7.3 - Validate: Snippet browser review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Tree view is intuitive
- Context menu is properly positioned
- State updates correctly
- Performance is good with many snippets

---

### Task 3.8: Drag and Drop - Snippets to Editor

#### 3.8.1 - Implement: Snippet drag and drop functionality
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/snippets.js:
  - Make snippets draggable (jQuery UI Draggable)
  - Drop zones in session editor:
    - System Prompts section
    - Messages section
    - Individual message widgets
  - Drop on System Prompts → creates new system block
  - Drop on Messages → creates new user message
  - Drop on message widget → appends to message text
  - Visual drop zone highlighting on drag over
  - Helper ghost during drag shows snippet name
  - Auto-saves after drop

**Files to Modify**:
- `static/js/snippets.js`
- `static/js/session.js`

#### 3.8.2 - Test: Drag and drop functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Dragging snippets works
- Drop zones highlight correctly
- Dropping creates/appends content correctly
- Auto-save works after drop
- Visual feedback is clear
- Works in all target areas

#### 3.8.3 - Validate: Drag and drop review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Drag and drop is smooth and intuitive
- No conflicts with sortable
- Drop zones are clear
- Content is inserted correctly

---

### Task 3.9: Modal System

#### 3.9.1 - Implement: Base modal system
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/modal.js with:
  - `showModal(options)` - creates and shows modal
  - `hideModal(modalId)` - closes modal
  - Modal options:
    - title
    - content (HTML or DOM element)
    - size (small, medium, large, fullscreen)
    - buttons (array of {text, class, onclick})
    - onClose callback
  - Uses Bootstrap modal component
  - ESC key closes modal
  - Click outside closes modal (optional)
  - Multiple modals stack properly
- Create templates/partials/modals.html with base modal structure

**Files to Create**:
- `static/js/modal.js`
- `templates/partials/modals.html`

#### 3.9.2 - Test: Modal system functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modals open and close correctly
- ESC key works
- Click outside works
- Multiple modals stack
- Buttons work correctly
- Callbacks fire properly

#### 3.9.3 - Validate: Modal system review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal system is reusable
- No memory leaks
- Z-index stacking works
- Focus management is correct

---

### Task 3.10: System Prompt Editor Modal

#### 3.10.1 - Implement: System prompt editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `showSystemPromptEditor(blockIndex)` - opens editor modal
  - Modal contains:
    - Type selector (text/image)
    - For text: CodeMirror editor
    - For image: URL input and preview
    - Cache control checkbox
    - Preview pane (for text: rendered markdown)
    - Save/Cancel buttons
  - Split view: editor on left, preview on right
  - Live preview updates (debounced 300ms)
  - Save updates session and auto-saves
  - New vs Edit mode

**Files to Modify**:
- `static/js/session.js`

#### 3.10.2 - Test: System prompt editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal opens with correct content
- CodeMirror editor works
- Type switching works
- Cache control checkbox works
- Preview updates correctly
- Save updates session
- Cancel discards changes

#### 3.10.3 - Validate: System prompt editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is functional and intuitive
- Preview is accurate
- No data loss
- CodeMirror configuration is appropriate

---

### Task 3.11: Message Editor Modal

#### 3.11.1 - Implement: Message editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `showMessageEditor(messageIndex)` - opens editor modal
  - Modal contains:
    - Role dropdown (user/assistant)
    - Content blocks section (array)
    - Each block has:
      - Type selector (text, tool_use, tool_result, image)
      - Appropriate editor for type
      - Remove button
      - Drag handle for reordering
    - Add content block button
    - Save/Cancel buttons
  - For text blocks: CodeMirror editor
  - For tool_use blocks:
    - Tool name dropdown
    - Auto-generated tool_use_id
    - Parameters (JSON editor with schema validation)
  - For tool_result blocks:
    - tool_use_id dropdown (populated from previous tool_use blocks)
    - Result content editor
    - is_error checkbox
  - Content blocks are sortable

**Files to Modify**:
- `static/js/session.js`

#### 3.11.2 - Test: Message editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal opens with correct message
- Role switching works
- Content block types work correctly
- Adding/removing blocks works
- Reordering blocks works
- tool_use parameter validation works
- tool_result dropdown shows available IDs
- Save updates session correctly

#### 3.11.3 - Validate: Message editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Complex message editing works smoothly
- Validation prevents invalid tool_use/tool_result
- UI is not overwhelming
- Data structures are correct

---

### Task 3.12: Snippet Editor Modal

#### 3.12.1 - Implement: Snippet editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/snippets.js:
  - `showSnippetEditor(snippetPath)` - opens editor modal
  - Modal layout:
    - Name input at top
    - Category dropdown (optional, includes "None")
    - Split view: CodeMirror on left, markdown preview on right
    - Live preview (debounced 300ms)
    - Save/Delete/Cancel buttons
  - Save calls API to create/update snippet
  - Delete confirms and calls API
  - New vs Edit mode

**Files to Modify**:
- `static/js/snippets.js`

#### 3.12.2 - Test: Snippet editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal opens correctly
- CodeMirror editor works
- Preview updates
- Category selection works
- Save creates/updates snippet
- Delete removes snippet
- Error handling for API failures

#### 3.12.3 - Validate: Snippet editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is user-friendly
- Preview is accurate
- API calls are correct
- File paths are handled properly

---

### Task 3.13: Session Browser Modal

#### 3.13.1 - Implement: Session history browser modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `showSessionBrowser()` - opens browser modal
  - Modal displays:
    - List of session backups
    - Each backup shows:
      - 📄 Timestamp (formatted)
      - Message count, tool count
      - [Restore] [Preview] [Delete] buttons
    - Sorted by timestamp (newest first)
  - Restore button confirms and loads backup
  - Preview button shows readonly session view
  - Delete button confirms and removes backup
  - Close button

**Files to Modify**:
- `static/js/session.js`

#### 3.13.2 - Test: Session browser functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal lists backups correctly
- Restore works
- Preview shows session (readonly)
- Delete removes backup
- Sorting is correct
- Empty state shown if no backups

#### 3.13.3 - Validate: Session browser review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Backup management is clear
- Restore confirmation prevents accidents
- Preview is helpful
- API calls are correct

---

### Task 3.14: Raw JSON Editor Modal (Error Recovery)

#### 3.14.1 - Implement: Raw JSON editor for error recovery
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - `showRawJsonEditor(errorMessage, jsonContent)` - opens editor
  - Triggered when session load fails with JSONDecodeError
  - Modal displays:
    - Error message at top (prominent)
    - Explanation text
    - CodeMirror JSON editor with:
      - Line numbers
      - JSON syntax highlighting
      - Error indicators
    - [Validate JSON] button (tries to parse, shows result)
    - [Save] button (writes back even if invalid, with confirmation)
    - [Cancel] button (offers to restore backup or create new)
  - Full-screen modal for editing large sessions

**Files to Modify**:
- `static/js/session.js`

#### 3.14.2 - Test: Raw JSON editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal opens on JSON error
- Editor shows error location
- Validate button works
- Save with invalid JSON shows confirmation
- Cancel offers recovery options
- CodeMirror configuration is appropriate

#### 3.14.3 - Validate: Raw JSON editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Error recovery is user-friendly
- No data loss possible
- Editor is functional
- Backup restoration works

---

### Task 3.15: Create/Import Project Modals

#### 3.15.1 - Implement: Create and import project modals
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/project.js:
  - `showCreateProjectModal()` - opens create project modal:
    - Project name input
    - Description textarea (optional)
    - Create/Cancel buttons
    - Name validation (alphanumeric, hyphens, max 50 chars)
    - Calls POST /api/projects
  - `showImportProjectModal()` - opens import modal:
    - File upload input (accept .zip)
    - Upload/Cancel buttons
    - Progress indicator during upload
    - Calls POST /api/projects/import
  - Both modals update project list on success

**Files to Modify**:
- `static/js/project.js`

#### 3.15.2 - Test: Create/import modal functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Create modal validates input
- Create calls API correctly
- Import modal accepts zip files
- Import shows progress
- Both update UI on success
- Error handling for API failures

#### 3.15.3 - Validate: Create/import modals review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modals are user-friendly
- Validation is clear
- File upload works correctly
- Error messages are helpful

---

### Task 3.16: Application Initialization

#### 3.16.1 - Implement: Main application initialization
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/app.js with:
  - `init()` - main initialization function:
    - Load global UI state
    - Load project list
    - Load last selected project (or show welcome)
    - Initialize all components
    - Set up event handlers
    - Restore UI state (expanded sections, scroll positions)
  - `saveUIState()` - saves UI state (debounced 1s)
  - Global error handler for AJAX failures
  - Window beforeunload handler (auto-save)
- Update templates/index.html to call app.init() on document ready

**Files to Create**:
- `static/js/app.js`

**Files to Modify**:
- `templates/index.html`

#### 3.16.2 - Test: Application initialization
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Application loads without errors
- Last project is restored
- UI state is restored
- All components initialize correctly
- Auto-save on page unload works
- Global error handler catches failures

#### 3.16.3 - Validate: Application initialization review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Initialization sequence is correct
- No race conditions
- Error handling is comprehensive
- Performance is acceptable

---

## Integration Tests

### Task 3.17: UI End-to-End Integration Test

#### 3.17.1 - Implement: Complete UI workflow test
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Manual testing checklist for complete UI workflow:
  1. Load application in browser
  2. Create new project
  3. Verify project selector updates
  4. Modify model configuration
  5. Add system prompt
  6. Add tool
  7. Add user message
  8. Add assistant message with tool_use
  9. Add user message with tool_result
  10. Reorder messages
  11. Create session backup
  12. Restore session
  13. Create snippet
  14. Drag snippet to message
  15. Export project
  16. Delete project
- Verify:
  - All features work correctly
  - UI is responsive
  - No console errors
  - Auto-save works throughout
  - State persists across page reload

#### 3.17.2 - Validate: Complete UI validation
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- All UI components work together
- No visual bugs or glitches
- Performance is good
- UX is intuitive
- Mobile/tablet layout works (responsive)
- Browser compatibility (Chrome, Firefox, Safari)

---

## Deliverables

1. Complete HTML templates (index.html, modals.html)
2. CSS files (main.css, widgets.css)
3. JavaScript modules:
   - app.js (main application)
   - project.js (project management)
   - session.js (session editor)
   - snippets.js (snippet browser)
   - modal.js (modal system)
   - utils.js (utilities)
4. All modals implemented and working
5. Drag and drop functionality
6. Auto-save system
7. State persistence
8. Manual testing checklist completed

## Success Criteria

- All UI components render correctly
- All AJAX calls work correctly
- Auto-save is reliable
- Drag and drop works smoothly
- Modals are functional
- State persists across page reload
- No console errors
- UI is responsive and intuitive
- Code follows jQuery/JavaScript best practices

## Notes

- Use Bootstrap 5.3.x for layout and components
- jQuery 3.7.x for DOM manipulation
- jQuery UI 1.13.x for drag/drop and sortable
- CodeMirror 5.65.x for code editing
- Marked.js 9.x for markdown rendering
- All libraries loaded from CDN
- Auto-save debounce: 500ms for session changes, 1s for UI state
- Use console.log for debugging during development
- Implement loading spinners for all AJAX operations
- Use Bootstrap's toast component for notifications
- Follow accessibility best practices (ARIA labels, keyboard navigation)
