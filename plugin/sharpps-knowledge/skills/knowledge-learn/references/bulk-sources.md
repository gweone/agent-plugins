# Bulk source documents (optional detail)

Optional explanation only; `SKILL.md` carries the rules and works without this file or any helper.

Run from the directory containing the skill's `SKILL.md` (paths are relative to it; use the absolute location where a host mounts skills elsewhere). `python3` below stands for whichever launcher starts Python 3 on your host (`python3`, `python` or `py -3`):

```sh
python3 scripts/chunk_source.py <file-or-directory> [--offset N] [--limit N] [--max-chars N] [--ext md,txt]
```

The helper is offline and read-only, standard library only. It prints JSON with at most `--limit` chunks (default 10) and `next_offset` (null when finished). Each chunk has `source` (relative path), `heading_path`, `line_start`, `line_end`, `sha256` and `text`. A chunk that looks like it holds a credential is listed with `withheld` set and `text` null: skip it and tell the user. Identical chunks are deduplicated; very small chunks are skipped.

Steps:

1. Keep only chunks with reusable, checkable knowledge: a fact, checklist, procedure or lesson with a stated problem and solution. Skip boilerplate, narrative, changelogs and personal data.
2. Follow the extraction rules in `SKILL.md` for each kept chunk: problem, proposed solution, preconditions, environment, limitations, specializations and evidence references.
3. Evidence is source-document review: result `not_run` unless the user supplies real verification, with a summary naming the source path, heading path, line range and chunk `sha256`. Never invent a root cause or a verification.
4. Drafts stay conversational unless learning and contribution authority are enabled, exactly as `SKILL.md` requires. At most ten drafts per cycle; if `next_offset` is not null, offer to resume with `--offset <next_offset>`.
5. Nothing here submits, reviews or publishes.
