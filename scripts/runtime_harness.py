#!/usr/bin/env python3
"""Check and record local runtime capabilities for rookie-cooking."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys


DEFAULT_MEMORY_DIR = ".rookie-cooking"
ENV_MEMORY_HOME = "ROOKIE_COOKING_HOME"
RUNTIME_FILE = "runtime.json"
PYTHON_CANDIDATES = (("python3",), ("python",), ("py", "-3"))
COMMAND_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class PythonCheck:
    available: bool
    command: tuple[str, ...]
    version: str | None
    error: str | None


def memory_root(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = values.get(ENV_MEMORY_HOME)
    if override:
        return Path(override).expanduser()
    return Path.home() / DEFAULT_MEMORY_DIR


def parse_python_version(output: str) -> str | None:
    match = re.search(r"Python\s+(\d+\.\d+\.\d+)", output)
    if not match:
        return None
    return match.group(1)


def current_python_check() -> PythonCheck:
    return PythonCheck(
        available=True,
        command=(sys.executable,),
        version=platform.python_version(),
        error=None,
    )


def detect_python(
    candidates: tuple[tuple[str, ...], ...] = PYTHON_CANDIDATES,
    include_current: bool = True,
) -> PythonCheck:
    if include_current:
        return current_python_check()

    errors: list[str] = []
    for candidate in candidates:
        command = (*candidate, "--version")
        try:
            completed = subprocess.run(
                list(command),
                check=False,
                text=True,
                capture_output=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            errors.append(f"{' '.join(candidate)}: {error}")
            continue

        output = f"{completed.stdout}\n{completed.stderr}"
        version = parse_python_version(output)
        if completed.returncode == 0 and version:
            return PythonCheck(
                available=True,
                command=candidate,
                version=version,
                error=None,
            )
        errors.append(f"{' '.join(candidate)}: {output.strip() or 'not available'}")

    return PythonCheck(
        available=False,
        command=(),
        version=None,
        error="; ".join(errors) if errors else "No Python command found",
    )


def install_hint(platform_name: str) -> str:
    normalized = platform_name.lower()
    if normalized.startswith("windows"):
        return (
            "Windows PowerShell:\n"
            "winget install Python.Python.3.12\n"
            "py -3 -m pip install -r requirements.txt"
        )
    if normalized == "darwin":
        return (
            "macOS shell:\n"
            "brew install python\n"
            "python3 -m pip install -r requirements.txt"
        )
    return (
        "Linux shell:\n"
        "sudo apt install python3 python3-pip\n"
        "python3 -m pip install -r requirements.txt"
    )


def command_text(command: tuple[str, ...]) -> str | None:
    if not command:
        return None
    return " ".join(command)


def build_runtime_status(
    memory_root: Path,
    platform_name: str,
    python_result: PythonCheck,
) -> dict[str, object]:
    has_python = python_result.available
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform_name,
        "memory_root": str(memory_root),
        "python": {
            "available": has_python,
            "command": command_text(python_result.command),
            "version": python_result.version,
            "error": python_result.error,
        },
        "capabilities": {
            "memory": has_python,
            "pdf": has_python,
            "printing": has_python,
        },
        "install_hint": None if has_python else install_hint(platform_name),
    }


def runtime_path(root: Path) -> Path:
    return root / RUNTIME_FILE


def write_runtime_record(root: Path, status: dict[str, object]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    runtime_path(root).write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check rookie-cooking runtime dependencies and record the result."
    )
    parser.add_argument(
        "command",
        choices=("doctor", "check-python", "install-hint"),
        nargs="?",
        default="doctor",
        help="Runtime check to run.",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Print status without writing ~/.rookie-cooking/runtime.json.",
    )
    parser.add_argument(
        "--probe-path",
        action="store_true",
        help="Probe python3/python/py instead of reporting the current interpreter.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = memory_root()
    platform_name = platform.system() or "Unknown"

    if args.command == "install-hint":
        print(install_hint(platform_name))
        return 0

    python_result = detect_python(include_current=not args.probe_path)
    status = build_runtime_status(root, platform_name, python_result)

    if args.command == "check-python":
        payload = status["python"]
    else:
        payload = status
        if not args.no_record:
            write_runtime_record(root, status)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if python_result.available else 1


if __name__ == "__main__":
    raise SystemExit(main())
