# AI Live Research Assistant Design

**Date:** 2026-03-15
**Branch:** `ai-live-research-assistant`
**Status:** Approved

## Goal

Replace the current local/hybrid assistant with a live-only research assistant that uses public web retrieval and model reasoning to produce a Markdown research report. The assistant must strongly prioritize evidence related to the target project while still allowing cross-project evidence when the relationship is explicit and relevant.

## Problems In The Current Assistant

- Local evidence ranking is rule-based and does not recognize project intent from the query text.
- Hybrid mode mixes unrelated local evidence into the answer prompt before any relevance validation.
- The generated answer is short, list-like, and not suitable for research use.
- The frontend renders plain text and source cards, not a readable report.

## Product Direction

The AI console becomes a `live-only` research workspace.

- The primary value is high-quality public-web analysis, not local knowledge lookup.
- Local project metadata remains useful only for query understanding and entity expansion.
- The final answer is a Markdown report with explicit reasoning and source attribution.

## User Experience

### Input

- Keep one main question field.
- Keep optional filters for project, category, and timeframe.
- Remove the `local / hybrid / live` mode selector.

### Output

The answer panel shows a Markdown research report with these sections by default:

1. `结论摘要`
2. `近期变化`
3. `主要方向`
4. `关键证据`
5. `相关项目联动`
6. `不确定性与风险`
7. `建议下一步`
8. `引用来源`

The evidence panel remains visible, but it becomes secondary to the report. Each evidence row must show:

- title
- source type
- project relation
- published time if known
- URL

## Backend Architecture

### Request Pipeline

The assistant query flow becomes:

1. `query planner`
2. `search query generation`
3. `web retrieval`
4. `page extraction`
5. `evidence reranking`
6. `report generation`

### 1. Query Planner

The model first transforms the user query into a structured plan. The planner output must include:

- `intent`
- `primary_entities`
- `related_entities`
- `timeframe`
- `must_include_terms`
- `must_exclude_terms`
- `search_queries`

Project metadata from `snapshot["projects"]` is used here to normalize aliases and identify likely target projects.

### 2. Search Query Generation

The backend executes multiple focused queries instead of one raw query. Example categories:

- target project release/update query
- target project docs/changelog query
- target project + related technology query
- target project + timeframe query

### 3. Web Retrieval

Default retrieval uses HTTP search and page fetching.

- Search engine result pages are fetched first.
- Candidate URLs are deduplicated.
- Known low-value domains can be filtered or penalized.

### 4. Page Extraction

Two fetch modes are supported:

- `http`: existing search result page + HTML extraction path
- `browser`: browser-assisted extraction for GitHub, JS-heavy docs sites, or low-quality HTTP extraction

Browser mode is a fallback, not the default path.

### 5. Evidence Reranking

Evidence passes through a strict relevance filter before report generation.

Evidence is accepted if either condition is true:

- it directly matches the primary entity or its aliases
- it is about a related entity and explicitly explains its relationship to the primary entity

Evidence must be dropped when it only matches generic infrastructure topics with no demonstrated relation to the user query.

This is the key fix for the `openclaw -> cuda` failure case.

### 6. Report Generation

The report generator receives:

- the original query
- the normalized plan
- the filtered evidence set

The model is instructed to:

- write a Markdown research report
- lead with analysis, not list raw items
- justify every cross-project claim
- call out missing evidence instead of inventing conclusions

## Data Model Changes

The assistant response payload should become:

- `report_markdown`
- `report_outline`
- `evidence`
- `sources`
- `search_trace`
- `applied_plan`

`search_trace` is for debugging and later UX improvements. It should include the generated queries and fetch mode used for each source.

## Frontend Changes

### AI Console

The AI console should:

- remove the mode selector
- label itself as a live research assistant
- render Markdown output in the answer area
- show evidence with relation labels, timestamps, and source links
- optionally expose search trace in a compact collapsible block

### Rendering

Use a Markdown renderer that supports:

- headings
- emphasis
- lists
- blockquotes
- links
- code fences

The output should remain readable on mobile and desktop.

## Error Handling

- If planner generation fails, fall back to a minimal plan built from raw query + selected filters.
- If browser extraction fails, fall back to HTTP extraction.
- If no relevant evidence survives reranking, return a report that explicitly says evidence is insufficient.
- If search succeeds but extraction quality is weak, the report should lower confidence and say so.

## Testing Strategy

### Backend

Add tests for:

- planner-driven primary entity extraction
- unrelated evidence filtering
- allowed cross-project evidence when relation is explicit
- browser fallback path
- live-only response payload shape

### Frontend

Add tests for:

- removed mode selector
- Markdown report rendering
- evidence timestamp and relation display
- compact trace rendering

## Scope

Included:

- AI console redesign
- backend live-only assistant pipeline
- planner/reranker/report prompts
- Markdown report rendering

Excluded:

- vector database or embeddings
- long-term browsing session memory
- replacing the sync pipeline

## Recommendation

Ship this in one branch and merge to `main` after backend and frontend verification. The design intentionally keeps the scope inside the assistant flow so the rest of the dashboard remains stable.
