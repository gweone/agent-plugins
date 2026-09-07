# SharpPS Agent Skills

This repository contains SharpPS workflow skills shared across AI agents.

## Skills

The canonical skill implementations remain under `plugins/*/skills/*/SKILL.md` for the existing Claude Code marketplace. They are exposed through `.agents/skills/` using relative symlinks so Codex and other Agent Skills-compatible clients can discover the same skills without maintaining a second copy.

## Rules

- Treat `SKILL.md` as the source of truth for a workflow.
- Do not duplicate or fork a skill into a provider-specific implementation unless compatibility requires it.
- When changing a skill, edit the canonical file under `plugins/*/skills/` and verify the `.agents/skills/` link still resolves.
- Skills may contain provider-specific references (for example Claude Code behavior); preserve those where they describe real constraints, but do not assume Claude Code is the only execution surface.
- User instructions take precedence over skill guidance.

## Validation

Run:

```bash
./scripts/install-agent-skills.sh --check
```

This checks that every Claude marketplace skill is exposed in `.agents/skills/` and that every target contains a valid `SKILL.md` with `name` and `description` frontmatter.
