#!/usr/bin/env python3
"""Lint SKILL.md files: check frontmatter has name+description and internal links resolve."""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Match [text](path) where path is relative (no scheme, no anchor-only)
LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<href>[^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return {"__error__": f"YAML parse error: {e}"}
    return data if isinstance(data, dict) else {"__error__": "frontmatter is not a mapping"}


def check_links(md_path: Path, errors: list[str]) -> None:
    text = md_path.read_text()
    for m in LINK_RE.finditer(text):
        href = m.group("href").strip()
        # skip external + anchor-only + mailto
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # strip query/fragment
        target_path = href.split("#", 1)[0].split("?", 1)[0]
        if not target_path:
            continue
        target = (md_path.parent / target_path).resolve()
        if not target.exists():
            errors.append(f"{md_path.relative_to(REPO_ROOT)}: broken link → {href}")


def lint_skill(skill_md: Path, errors: list[str]) -> None:
    text = skill_md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{skill_md.relative_to(REPO_ROOT)}: missing YAML frontmatter")
        return
    if "__error__" in fm:
        errors.append(f"{skill_md.relative_to(REPO_ROOT)}: {fm['__error__']}")
        return
    for required in ("name", "description"):
        if not fm.get(required):
            errors.append(f"{skill_md.relative_to(REPO_ROOT)}: frontmatter missing '{required}'")
    name = fm.get("name", "")
    expected = skill_md.parent.name
    if name and name != expected:
        errors.append(
            f"{skill_md.relative_to(REPO_ROOT)}: name '{name}' does not match folder '{expected}'"
        )


def main() -> int:
    errors: list[str] = []
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        print(f"error: no SKILL.md files found under {SKILLS_DIR}", file=sys.stderr)
        return 2

    for skill_md in skill_files:
        lint_skill(skill_md, errors)

    # Check links across all repo markdown
    md_files = list(REPO_ROOT.glob("*.md")) + list(SKILLS_DIR.rglob("*.md"))
    for md in md_files:
        check_links(md, errors)

    if errors:
        for err in errors:
            print(f"  - {err}")
        print(f"\n{len(errors)} issue(s) across {len(skill_files)} skill(s).")
        return 1

    print(f"OK: {len(skill_files)} skills, {len(md_files)} markdown files — all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
