# Editorial Workbench Redesign Design

## Goal
Rebuild the entire frontend around a coherent editorial product instead of a collection of dashboard panels. The new product should feel like a technical magazine run by a research desk: readable, high-signal, operationally useful, and visually distinctive.

## Product Direction
The current UI has two core problems:

- The visual language is generic dashboard UI: large rounded white cards, soft gradients, low-contrast hierarchy, and repetitive modules.
- The information architecture mirrors implementation boundaries instead of user workflows.

The redesign should not be a surface-level reskin. It should reframe the product as a publication and operations desk with a clearer mental model.

## Chosen Experience
Use a `technical magazine + research editorial desk` visual language with a `duty desk` operational model.

Visual choices confirmed:

- Base tone: warm paper white instead of flat SaaS white
- Primary text/color: deep ink blue-black
- Accent color: electric blue
- Personality: technical magazine, not a glassmorphism console
- Operational emphasis: duty desk, not gallery browsing

## Information Architecture
Replace the current six-page structure with a new top-level navigation:

- `封面`
- `线索台`
- `专题库`
- `文档台`
- `研究台`
- `设置`

### Mapping From Current Pages
- `日报` becomes `封面`
- `同步监控` is absorbed into `线索台`
- `情报监控` becomes `专题库`
- `文档解读` becomes `文档台`
- `AI 控制台` becomes `研究台`
- `配置中心` remains `设置`

This keeps the underlying capabilities but organizes them around user intent instead of implementation categories.

## Visual System

### 1. Editorial Frame
The UI should feel like a publication issue rather than a stack of utility panels.

- Use a stronger masthead and section identity
- Add issue-like framing: section numbers, labels, datelines, subheads, deck copy
- Prefer structured columns and rails over floating cards everywhere
- Reduce giant rounded “capsules” and replace them with editorial panels, bordered modules, and compositional grids

### 2. Typography
The type system must create visible hierarchy.

- Display/headline type for page titles and cover stories
- Readable Chinese-first body type for all operational content
- Tighter rules for kicker, label, caption, stat, and narrative body copy
- Strong distinction between editorial headline zones and utility metadata zones

### 3. Color and Materials
The palette should support research reading and operations.

- Background: warm paper white
- Primary: deep ink blue-black
- Accent: electric blue for active state, current focus, and high-signal paths
- Support colors: neutral gray, pale cyan, restrained warning/danger tones
- Decoration: rule lines, grid overlays, issue labels, subtle print-like texture

### 4. Motion
Animation should communicate transitions, not decorate emptiness.

- Section-load stagger for major page modules
- Drawer and panel transitions that support orientation
- Lightweight hover/focus transitions only where they improve scanning
- Avoid generic micro-animations on every card

### 5. Responsive Behavior
Mobile should become a readable sequence, not a shrunk dashboard.

- Collapse left navigation into a drawer or top sheet
- Convert wide multi-column layouts into stacked editorial sections
- Keep current context visible with sticky page section labels where useful
- Preserve readability of logs, evidence, and long-form content

## Page Designs

### 封面
The cover page replaces the current “daily homepage.” It should feel like the front page of the current issue.

Structure:

- Masthead: product title, date, issue context, duty status
- Main story: the single most important current conclusion
- Secondary stories: three to five notable project or intel developments
- News strip: latest incremental changes, latest job summary, exception pulse
- Deep-link rail: guided entry to `线索台`, `专题库`, and `文档台`

Purpose:

- Answer what matters today
- Show whether the system is healthy enough to trust
- Direct the user to the correct drilldown path

This page is narrative-first, not metric-first.

### 线索台
The clue desk is the operational heart of the product. It should support duty decisions rather than general browsing.

Structure:

- Duty overview: whether anything is running, whether recent failures have recovered, whether high-priority updates exist
- Runway: current Job, recent Jobs, failure aggregation, source status
- Work queue: actionable new events, important analyses, and docs changes that deserve follow-up

Behavior:

- Sync monitoring becomes one section within the page, not the whole page identity
- Logs, failure reasons, and recent jobs stay close to the operational summary
- Actionable clues are separated from raw execution history

Purpose:

- Help the user decide whether there is work now
- Show where a process is blocked
- Point to the next click with minimal ambiguity

### 专题库
The topic library replaces the project monitor list view with a long-horizon editorial model.

Structure:

- Topic stream: curated project/topic cards with summary narratives
- Index mode: tool-like entry point for direct project lookup
- Per-topic frame: latest direction, why it matters, release motion, docs motion, suggested next action

Purpose:

- Support ongoing reading and monitoring
- Make each project feel like a dossier instead of a category bucket
- Separate long-term tracking from duty work

### 文档台
The docs desk becomes an editorial workspace for document interpretation.

Structure:

- Left rail: project, category, mode filters
- Center column: document event stream grouped by initial read / diff updates / page-level changes
- Right detail panel: selected event analysis, changed pages, page diff context

Purpose:

- Show what changed in docs and why it matters
- Make the workflow feel like active document review instead of raw structured output
- Support continuous inspection across event stream and page diff detail

### 研究台
The research desk becomes a real research workspace rather than a single form.

Structure:

- Left rail: query, scope, mode, filters
- Main center: report body as the primary surface
- Right rail: evidence, source list, search trace, suggested next steps

Purpose:

- Make research output feel like authored work
- Keep evidence constantly visible
- Reduce the “form-submit-result dump” feeling

### 设置
Settings remains utility-focused but should still inherit the editorial system.

Structure:

- Capability overview at the top
- LLM provider configuration with stronger effective-state presentation
- Assistant defaults and project/source onboarding as separate sections
- Administrative forms grouped by task, not by raw schema

Purpose:

- Maintain a cleaner operations boundary without visually dropping out of the product

## Shared Interaction Rules

### Navigation
The navigation should feel like section navigation in a publication.

- Strong active state with clear section identity
- Better distinction between section label and section description
- Compact but high-recognition iconography/tokens
- On smaller screens, preserve section naming and current-location clarity

### Hierarchy
Every page should have a visible hierarchy of:

- page identity
- section identity
- primary narrative or operational object
- secondary supporting material
- tertiary metadata or utilities

No page should present all modules at the same visual weight.

### Status Language
Operational states should remain explicit and accurate.

- Running work is visibly live
- Recovered or resolved failures are distinguishable from current failures
- Completed-with-failures is different from failed
- Historical runs should read as historical, not current danger

### Content Density
The redesign should improve density without feeling cramped.

- Editorial layouts should support reading and scanning at once
- Stats should be embedded in context, not sprayed across equal cards
- Empty states must still preserve editorial composition

## Implementation Strategy
The redesign should be incremental but architecture-aware.

### Phase 1: Core Shell and Design Tokens
- Replace root shell, navigation, page title framing, and global visual tokens
- Establish the new typography, spacing, surfaces, and responsive rules

### Phase 2: Cover and Clue Desk
- Rebuild `封面` and `线索台` first because they define the product narrative and duty workflow
- Reuse the recent Job work already completed, but restage it within the new desk layout

### Phase 3: Topic Library and Docs Desk
- Redesign long-form monitoring and document analysis pages around editorial reading flows

### Phase 4: Research Desk and Settings
- Rebuild the AI workspace and polish utility flows within the same system

## Testing Strategy

### Functional
- Existing page capabilities remain accessible through new IA
- Sync trigger, log drilldown, docs navigation, research flow, and config save still work
- Job selection and monitoring semantics continue to work after layout migration

### Visual
- Verify desktop and mobile layouts for all top-level pages
- Check hierarchy, contrast, and overflow on long content blocks
- Check sticky/rail behavior for navigation and side panels

### Regression
- Keep current frontend test coverage for sync-monitor behavior
- Add tests where navigation labels or page routing semantics change
- Run full frontend test suite after each major page migration

## Non-Goals
- Rebuilding backend APIs solely for cosmetic reasons
- Adding new data domains that do not support the editorial redesign
- Over-animating the interface
- Designing around generic SaaS conventions

## Success Criteria
The redesign is successful if:

- The product no longer feels like a collection of generic admin cards
- Users can immediately understand what matters today from the cover
- Users can operate the system from the clue desk without ambiguity
- Long-form reading, document inspection, and research feel intentional and authored
- The product has a recognizable visual identity distinct from default dashboard templates
