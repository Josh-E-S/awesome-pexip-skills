# Contributing

Thanks for your interest. This is an opinionated skill bundle for Pexip Infinity webapp3 patterns. Contributions welcome — especially corrections cited against the webapp3 source.

## What makes a good PR

| Type | Bar |
|---|---|
| **Bug fix in a pattern** | Cite the webapp3 source line(s) that show the correct shape. The skill should match what webapp3 actually does. |
| **New skill** | Must cover a feature webapp3 implements with patterns that are non-obvious from the SDK alone. Add an entry to `README.md` and `ARCHITECTURE.md`. |
| **Trigger improvement** | If a skill *should* fire on a prompt but doesn't, add the prompt to `PROMPTS.md` and adjust the SKILL.md `description` frontmatter. |
| **Doc clarity** | No citation needed — just clearer prose. |

## Skill format

Every skill lives in `skills/<name>/SKILL.md` with this frontmatter:

```yaml
---
name: <skill-name>
description: <one-line description with concrete trigger keywords>
---
```

Larger skills can have sibling `*.md` files (see `chat/direct-messages.md`, `media-pipeline/video-effects.md`) for deep details. Keep `SKILL.md` itself under ~250 lines.

Skills must end with a **Reference source** section listing the webapp3 file paths the patterns came from. This is how readers verify the skill against their own version.

## Style

- **Lead with the pattern, not the API.** Show *why* webapp3 does it this way.
- **Code samples are illustrative, not copy-paste.** Trim imports, use `...` for context.
- **Cite, don't paraphrase.** When you describe a webapp3 behavior, point at the file.
- **No screenshots** unless they're load-bearing — text scales, screenshots rot.

## Local testing

```bash
# Install as a global skill set
cp -r skills/* ~/.claude/skills/

# Or symlink for live editing
ln -s "$PWD/skills" ~/.claude/skills/awesome-pexip-skills
```

Then open Claude Code in a Pexip project and run prompts from `PROMPTS.md` — the listed skill should fire.

## Versioning

`webapp3` evolves. When you upgrade `@pexip/*` packages and notice a skill is stale:

1. Find the equivalent file in your version's webapp3 source
2. Diff against the path the skill's "Reference source" lists
3. If only the SDK signature changed → update the snippet, keep the architectural prose
4. If the pattern itself changed → update both, and note the version in the PR

## License

By contributing, you agree your contributions will be licensed under the MIT License (see `LICENSE`).
