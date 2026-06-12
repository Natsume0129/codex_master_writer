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

## v0.3 Apply Helper

`scripts/apply_patch.py` is a guarded helper, not a general YAML merge engine.

Dry-run first:

```bash
python scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml
```

Actually write limited updates only after review:

```bash
python scripts/apply_patch.py --project ./projects/my-novel --patch ./projects/my-novel/pending_updates/chapter_012_patch.yaml --confirm
```

If `requires_user_confirmation` is non-empty, `--confirm-major` is also required after explicit user approval.

The helper creates timestamped backups under `backups/`, appends `changelog.md`, and marks the patch `status: applied` when writing succeeds.

Automatically mergeable in v0.3:

- `updates.timeline` -> `branches/<branch>/timeline.yaml`
- `updates.foreshadowing_added` -> `branches/<branch>/foreshadowing.yaml`
- `updates.open_questions_added` -> `branches/<branch>/open_questions.md`
- `updates.continuity_issues` -> `branches/<branch>/continuity_log.md`

Review-only in v0.3:

- `updates.characters`
- `updates.relationships`
- `updates.worldbuilding`
- `updates.locations`
- `updates.organizations`
- `updates.items`
- `updates.terms`

## Relationship to Bible Files

`canon/` and branch bible files are durable knowledge. `pending_updates/` is a review queue. Codex should show or summarize patches, ask for confirmation on major changes, then apply only explicitly approved changes.

## Changelog and Rollback

When applying an approved patch, append a brief entry to `changelog.md`:

- timestamp
- patch id
- affected files
- summary
- whether user confirmation was required

Rollback means reverting the applied patch effects manually, using timestamped backups, or using version control. v0.3 does not provide semantic rollback.

## Forbidden Defaults

Do not directly rewrite `characters.yaml`, `world_bible.md`, `timeline.yaml`, `foreshadowing.yaml`, or `relationships.yaml` as a side effect of drafting.
