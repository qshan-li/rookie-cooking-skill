#!/usr/bin/env python3
"""Sync this skill repository into local agent skill directories."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


SKILL_NAME = "rookie-cooking-skill"
EXCLUDED_NAMES = {
    ".git",
    ".agents",
    ".claude",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "output",
    "tmp",
}


@dataclass(frozen=True)
class SyncResult:
    synced_paths: tuple[Path, ...]
    linked_paths: tuple[Path, ...]


def central_install_path(home: Path) -> Path:
    return home / ".local" / "share" / "agent-skills" / SKILL_NAME


def agent_link_paths(home: Path) -> tuple[Path, ...]:
    return (
        home / ".codex" / "skills" / SKILL_NAME,
        home / ".claude" / "skills" / SKILL_NAME,
        home / ".gemini" / "skills" / SKILL_NAME,
        home / ".hermes" / "skills" / SKILL_NAME,
    )


def should_ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_NAMES or name.endswith(".pyc")}


def resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def ensure_install_target_is_safe(source: Path, target: Path) -> None:
    source_resolved = resolved(source)
    target_resolved = target.expanduser().resolve(strict=False)
    if target_resolved == source_resolved:
        raise ValueError(f"Refusing to sync onto source directory: {target}")
    if source_resolved in target_resolved.parents:
        raise ValueError(f"Refusing to sync inside source directory: {target}")


def copy_skill(source: Path, target: Path) -> None:
    ensure_install_target_is_safe(source, target)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=should_ignore)


def ensure_link(link: Path, target: Path) -> bool:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return True
        link.unlink()
    elif link.exists():
        return False
    link.symlink_to(target, target_is_directory=True)
    return True


def sync_skill(source: Path, home: Path, include_agent_links: bool = True) -> SyncResult:
    source = resolved(source)
    home = home.expanduser().resolve(strict=False)
    if not (source / "SKILL.md").exists():
        raise ValueError(f"Source does not look like a skill repository: {source}")

    central_target = central_install_path(home)
    copy_skill(source, central_target)

    linked_paths: list[Path] = []
    if include_agent_links:
        for link in agent_link_paths(home):
            if ensure_link(link, central_target):
                linked_paths.append(link)

    return SyncResult(synced_paths=(central_target,), linked_paths=tuple(linked_paths))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync rookie-cooking-skill into local agent skill directories.")
    parser.add_argument("--source", type=Path, default=Path("."), help="Skill repository root.")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Home directory containing agent skill dirs.")
    parser.add_argument(
        "--no-agent-links",
        action="store_true",
        help="Only update ~/.local/share/agent-skills, without creating agent skill symlinks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = sync_skill(args.source, args.home, include_agent_links=not args.no_agent_links)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    for path in result.synced_paths:
        print(f"synced: {path}")
    for path in result.linked_paths:
        print(f"linked: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
