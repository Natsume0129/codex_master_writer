# Patch-Based Updates

Post-write updates are proposals. Drafting, outlining, continuation, and rewrite work must generate patch files under `pending_updates/` instead of directly overwriting core bible files.

## Patch Schema

```yaml
patch_id: ""
branch: "main"
chapter: null
created_at: ""
source_draft: ""
status: "pending"
updates:
  characters: []
  relationships: []
  worldbuilding: []
  locations: []
  organizations: []
  items: []
  terms: []
  timeline: []
  foreshadowing_added: []
  foreshadowing_paid_off: []
  open_questions_added: []
  hard_constraints_added: []
  continuity_issues: []
potential_conflicts: []
requires_user_confirmation: []
notes: ""
```

## Merge Rules

- `confirmed` facts can be merged when directly sourced.
- `inferred` stays inferred unless supported by later evidence.
- `uncertain` must not be promoted automatically.
- `user_override` has the highest priority.
- `deprecated` should not enter context packs unless the user requests history.
- Major plot changes require user confirmation.

## Relationship to Bible Files

`canon/` and branch bible files are durable knowledge. `pending_updates/` is a review queue. Codex should show or summarize patches, ask for confirmation on major changes, then apply only explicitly approved changes.

## Changelog and Rollback

When applying an approved patch, append a brief entry to `changelog.md`:

- timestamp
- patch id
- affected files
- summary
- whether user confirmation was required

Rollback means reverting the applied patch effects manually or from version control. v0.1 does not provide automated rollback.

## Forbidden Defaults

Do not directly rewrite `characters.yaml`, `world_bible.md`, `timeline.yaml`, `foreshadowing.yaml`, or `relationships.yaml` as a side effect of drafting.
