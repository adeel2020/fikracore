# gbrain MCP Capabilities

Generated: 2026-09-10T13:45:49.263488+00:00

## Discovery

- Backend env source: `backend/.env`
- Live MCP endpoint: `http://localhost:3131/mcp`
- Live tools/list status: `ok`
- Live tool count: `96`
- Token handling: loaded in-process only; not printed or persisted.

## Required Tool Contracts

### get_active_schema_pack

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `[]`

### schema_graph

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `[]`

### schema_stats

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `[]`

### schema_lint

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `['pack']`

### schema_review_orphans

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `['limit']`

### list_pages

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `['include_deleted', 'limit', 'offset', 'sort', 'tag', 'type', 'updated_after']`

### get_page

- Available in checked-in schema: `True`
- Required args: `['slug']`
- Properties: `['fuzzy', 'include_deleted', 'slug']`

### get_links

- Available in checked-in schema: `True`
- Required args: `['slug']`
- Properties: `['slug']`

### get_backlinks

- Available in checked-in schema: `True`
- Required args: `['slug']`
- Properties: `['slug']`

### traverse_graph

- Available in checked-in schema: `True`
- Required args: `['slug']`
- Properties: `['depth', 'direction', 'link_type', 'slug']`

### resolve_slugs

- Available in checked-in schema: `True`
- Required args: `['partial']`
- Properties: `['partial']`

### query

- Available in checked-in schema: `True`
- Required args: `[]`
- Properties: `['adaptive_return', 'autocut', 'cross_modal', 'detail', 'embedding_column', 'expand', 'image', 'image_mime', 'lang', 'limit', 'mode', 'near_symbol', 'offset', 'query', 'recency', 'relational', 'salience', 'since', 'source_id', 'symbol_kind', 'until', 'walk_depth']`

### search

- Available in checked-in schema: `True`
- Required args: `['query']`
- Properties: `['limit', 'mode', 'offset', 'query']`

### add_link

- Available in checked-in schema: `True`
- Required args: `['from', 'to']`
- Properties: `['context', 'from', 'link_source', 'link_type', 'to']`

### remove_link

- Available in checked-in schema: `True`
- Required args: `['from', 'to']`
- Properties: `['from', 'link_source', 'link_type', 'to']`

### put_page

- Available in checked-in schema: `True`
- Required args: `['slug', 'content']`
- Properties: `['allow_empty', 'content', 'ingested_via', 'slug', 'source_kind', 'source_uri']`

### get_versions

- Available in checked-in schema: `True`
- Required args: `['slug']`
- Properties: `['slug']`
