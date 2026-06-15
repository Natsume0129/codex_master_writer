# Style And Voice System

v0.8 adds a deterministic style and revision loop. Scripts create control artifacts, prompts, and report skeletons only. Codex/model does the actual style judgment, voice review, prose writing, and revision reasoning after reading the generated prompts.

## Artifacts

- `branches/<branch>/style/style_profile.yaml`: branch-local writing style profile. It records tone, rhythm, prose density, imagery policy, anti-AI-flavor rules, and source/status/confidence. It is not a fact source.
- `branches/<branch>/style/character_voice_sheet.yaml`: branch-local character voice guide. It records diction, sentence habits, information boundaries, silence patterns, and contrast notes. It does not override `canon/characters.yaml`.
- `branches/<branch>/outlines/chapter_XXX_scene_outline.yaml`: beat-level scene outline for one chapter. It connects the chapter function card to scene order, conflict, outcome, required facts, forbidden changes, and user-confirmation items.
- `branches/<branch>/reviews/chapter_XXX_style_audit.md`: style and voice review shell plus deterministic surface warnings. It complements the quality report; it is not an automatic rewrite.
- `branches/<branch>/revision/chapter_XXX_revision_plan.md`: revision plan and prompt built from the draft, context pack, quality report, style audit, and scene outline. It does not revise prose by itself.

## Workflow

1. Create or update the chapter function card.
2. Build a context pack.
3. Create `style_profile.yaml` and `character_voice_sheet.yaml` if missing.
4. Create a scene outline for the target chapter.
5. Rebuild the context pack with `--include-style-profile --include-voice-sheet --include-scene-outline`.
6. Generate a draft prompt with `--style-profile --voice-sheet --scene-outline`.
7. After drafting, create a quality report and style audit.
8. Create a revision plan before revising the draft.
9. Put continuity or bible changes in pending patches; do not edit canon directly.

## Boundaries

- Do not imitate living authors or named real writers.
- Do not store long copyrighted samples in style artifacts.
- Do not read `raw_text/full_text.txt`.
- Do not generate chapter prose from scripts.
- Do not auto-apply patches or auto-confirm major plot changes.
- If style/voice conflicts with canon, outline, context pack, or chapter function card, prefer the source-tracked project artifact and record the conflict.

## CLI Example

```bash
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-style-profile --project-root ./tmp/demo_novel --branch main --genre "玄幻" --title "主线文风档案" --prompt --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-voice-sheet --project-root ./tmp/demo_novel --branch main --characters protagonist,villain,mentor --prompt --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-scene-outline --project-root ./tmp/demo_novel --branch main --chapter 1 --prompt --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py build-context-pack --project-root ./tmp/demo_novel --branch main --task continue_story --chapter 1 --include-style-profile --include-voice-sheet --include-scene-outline --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-draft-prompt --project-root ./tmp/demo_novel --branch main --chapter 1 --style-profile branches/main/style/style_profile.yaml --voice-sheet branches/main/style/character_voice_sheet.yaml --scene-outline branches/main/outlines/chapter_001_scene_outline.yaml --anti-ai-flavor-level high --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-style-audit --project-root ./tmp/demo_novel --branch main --chapter 1 --prompt --force
python .agents/skills/chinese-novel-writing/scripts/novel_project.py create-revision-plan --project-root ./tmp/demo_novel --branch main --chapter 1 --force
```
