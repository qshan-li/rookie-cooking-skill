#!/usr/bin/env python3
"""Run cross-agent QA checks for rookie-cooking."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys


SKILL_NAME = "rookie-cooking"


@dataclass(frozen=True)
class TestCase:
    case_id: str
    flow: str
    prompt: str
    expectation: str


@dataclass(frozen=True)
class InstallCheck:
    agent: str
    installed: bool
    paths: tuple[Path, ...]
    install_hint: str


@dataclass(frozen=True)
class Evaluation:
    status: str
    reason: str


@dataclass(frozen=True)
class RunRecord:
    agent: str
    case_id: str
    command: list[str]
    returncode: int
    output_path: str
    evaluation: Evaluation


TEST_CASES = {
    "A": TestCase(
        "A",
        "Recipe Generation",
        "Use $rookie-cooking 生成番茄炒蛋。",
        "Missing recipe output mode should trigger Interactive QA or default fallback.",
    ),
    "B": TestCase(
        "B",
        "Recipe Generation",
        "Use $rookie-cooking 生成番茄炒蛋，只要厨房版。",
        "Explicit kitchen-only request should not ask output-strength QA.",
    ),
    "C": TestCase(
        "C",
        "Recipe Generation",
        "Use $rookie-cooking 生成 2 人份青椒肉丝，选择默认。",
        "Explicit default request should output the full explanation version.",
    ),
    "D": TestCase(
        "D",
        "Recipe Generation",
        "Use $rookie-cooking 生成 4 人份红烧肉，家里是电磁炉，选择厨房执行版。",
        "Explicit kitchen execution request should output kitchen execution steps.",
    ),
    "E": TestCase(
        "E",
        "Troubleshooting",
        "Use $rookie-cooking 诊断：我做的蒸蛋有很多蜂窝，表面还出水。",
        "Troubleshooting should not trigger output-strength QA.",
    ),
    "F": TestCase(
        "F",
        "Learning",
        "Use $rookie-cooking 为什么炒青菜会出水？",
        "Learning should explain the principle and not trigger Recipe Generation QA.",
    ),
    "G": TestCase(
        "G",
        "Meal Planning",
        "Use $rookie-cooking 两菜一汤给 3 个人，怎么安排？",
        "Meal Planning should output schedule and conflicts, not Recipe Generation QA.",
    ),
    "H": TestCase(
        "H",
        "Recipe Import",
        "Use $rookie-cooking 把这个菜谱改写成新手版：鸡蛋两个，番茄两个，炒熟即可。",
        "Recipe Import should rewrite into draft schema, not output-strength QA.",
    ),
    "I": TestCase(
        "I",
        "Memory Init / Update",
        "Use $rookie-cooking 以后默认 4 人份。",
        "Memory update should show a write preview and require confirmation.",
    ),
}

AGENTS = ("codex", "claude", "gemini", "hermes")


def local_install_checks(root: Path, home: Path) -> list[InstallCheck]:
    candidates = {
        "codex": (
            home / ".codex" / "skills" / SKILL_NAME / "SKILL.md",
            home / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
            root / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
        ),
        "claude": (
            root / ".claude" / "skills" / SKILL_NAME / "SKILL.md",
            home / ".claude" / "skills" / SKILL_NAME / "SKILL.md",
        ),
        "gemini": (
            root / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
            home / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
            home / ".gemini" / "skills" / SKILL_NAME / "SKILL.md",
        ),
        "hermes": (
            home / ".hermes" / "skills" / SKILL_NAME / "SKILL.md",
            root / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
            home / ".agents" / "skills" / SKILL_NAME / "SKILL.md",
        ),
    }
    hints = {
        "codex": "Install as a Codex skill/plugin or link/copy into a configured Codex skill source; root SKILL.md is not enough.",
        "claude": "Use .claude/skills/rookie-cooking/SKILL.md or ~/.claude/skills/rookie-cooking/SKILL.md.",
        "gemini": "Run: gemini skills link <repo-path> --scope workspace --consent",
        "hermes": "Install or enable through hermes skills, then verify with: hermes skills list",
    }

    checks: list[InstallCheck] = []
    for agent, paths in candidates.items():
        checks.append(
            InstallCheck(
                agent=agent,
                installed=any(path.exists() for path in paths),
                paths=paths,
                install_hint=hints[agent],
            )
        )
    return checks


def has_all(text: str, snippets: tuple[str, ...]) -> bool:
    return all(snippet in text for snippet in snippets)


def has_any(text: str, snippets: tuple[str, ...]) -> bool:
    return any(snippet in text for snippet in snippets)


def final_answer_text(text: str) -> str:
    lines = text.splitlines()
    answer_start = 0
    for index, line in enumerate(lines):
        if line.startswith("[thinking]"):
            answer_start = index + 1

    answer_lines = lines[answer_start:]
    while answer_lines:
        first = answer_lines[0]
        if first.startswith("[") or first.startswith(" ") or not first.strip():
            answer_lines = answer_lines[1:]
            continue
        break

    if answer_lines and answer_lines[-1].startswith("[done]"):
        answer_lines = answer_lines[:-1]

    final_text = "\n".join(answer_lines).strip()
    if final_text:
        return final_text
    return text


def has_delivery_choice(text: str) -> bool:
    return (
        has_any(text, ("请选择后续交付方式", "后续交付方式", "交付方式"))
        and has_any(text, ("生成 PDF", "生成PDF", "生成厨房执行版 PDF"))
        and "直接打印" in text
        and has_any(text, ("暂不需要", "不需要"))
    )


def has_first_run_adaptation_choice(text: str) -> bool:
    return (
        has_any(text, ("首次适配", "本次适配", "first-run", "First-Run"))
        and has_any(text, ("继续使用默认值", "Use defaults and continue", "使用默认"))
        and has_any(text, ("仅适配本次", "Adapt this recipe only"))
        and has_any(text, ("初始化长期偏好", "Initialize long-term preferences"))
    )


def has_default_adaptation_statement(text: str) -> bool:
    return has_any(
        text,
        (
            "本次使用默认适配继续",
            "继续使用默认值",
            "Use defaults and continue",
            "default adaptation",
        ),
    )


def has_removed_recipe_output_mode(text: str) -> bool:
    return has_any(text, ("快速输出", "精准输出", "输出强度", "Quick output", "Precise output"))


def has_kitchen_section_heading(text: str) -> bool:
    return has_any(text, ("\n## 厨房执行版", "\n# 厨房执行版")) or " 厨房执行版\n\n份量" in text


def has_kitchen_print_card_body(text: str) -> bool:
    return has_all(text, ("## 备料", "## 做法")) and has_any(text, ("出错怎么办", "## 安全 / 补救"))


def has_kitchen_execution_output(text: str) -> bool:
    return "厨房执行版" in text or has_kitchen_print_card_body(text)


def has_kitchen_critical_checks(text: str) -> bool:
    return has_any(text, ("安全", "食品安全")) and has_any(text, ("失败信号", "出错怎么办", "补救"))


def has_safety_judgment(text: str) -> bool:
    return has_any(text, ("安全判断", "安全分诊", "Safety Triage", "safety judgment"))


def has_memory_action(text: str) -> bool:
    return has_any(
        text,
        (
            "Record feedback only",
            "Save durable preference",
            "Do not record",
            "记录反馈",
            "保存长期偏好",
            "不要记录",
        ),
    )


def has_learning_expansion(text: str) -> bool:
    return has_any(
        text,
        (
            "Full principle card",
            "Explain through one dish",
            "Diagnose my failed result",
            "完整原理卡",
            "结合一道菜",
            "诊断",
            "展开说",
            "用一道菜",
            "验证这个原理",
            "动手验证",
            "想展开",
            "还可以看",
        ),
    )


def has_write_preview(text: str) -> bool:
    return has_any(text, ("Write preview", "写入预览", "Will write")) and has_any(
        text,
        ("Confirm write", "Edit values", "Cancel", "确认写入", "编辑", "取消"),
    )


def has_shopping_mode_choice(text: str) -> bool:
    return has_any(text, ("购物清单模式", "shopping list mode")) and has_any(
        text,
        ("完整购物清单", "Full shopping list"),
    ) and has_any(text, ("缺货检查清单", "Missing-items checklist")) and has_any(
        text,
        ("跳过购物清单", "Skip shopping list"),
    )


def has_full_shopping_list_body(text: str) -> bool:
    return has_any(text, ("### 主料", "| 食材 | 总量 |", "| ingredient | total"))


def has_import_intent_split(text: str) -> bool:
    return has_any(text, ("导入意图", "Import intent")) and has_any(
        text,
        ("持久化目标", "persistence target"),
    ) and has_any(text, ("输出形态", "output shape"))


def evaluate_output(test_case: TestCase, text: str) -> Evaluation:
    text = final_answer_text(text)

    if test_case.case_id == "A":
        if has_removed_recipe_output_mode(text):
            return Evaluation("fail", "interactive QA included removed recipe output modes")
        if has_kitchen_section_heading(text) or has_kitchen_print_card_body(text):
            return Evaluation("fail", "default output included kitchen execution body")
        if has_all(text, ("默认", "厨房执行版")) and has_any(text, ("选择输出模式", "请选择菜谱输出模式", "菜谱输出模式")):
            if has_first_run_adaptation_choice(text):
                return Evaluation("pass", "interactive QA choice presented with first-run adaptation")
            return Evaluation("fail", "interactive QA omitted first-run adaptation choice")
        if (
            "完整解释版" in text
            and has_any(text, ("默认", "未指定输出模式"))
            and has_default_adaptation_statement(text)
            and has_delivery_choice(text)
        ):
            return Evaluation("pass", "default fallback used with delivery choice")
        if "完整解释版" in text and has_any(text, ("PDF", "pdf", "打印")):
            return Evaluation("fail", "default fallback used plain delivery question instead of choice")
        return Evaluation("fail", "missing interactive QA and default fallback")

    if test_case.case_id == "B":
        if "完整解释版" in text:
            return Evaluation("fail", "kitchen-only request included full explanation")
        if has_kitchen_execution_output(text) and has_kitchen_critical_checks(text) and has_delivery_choice(text):
            return Evaluation("pass", "kitchen-only output retained critical checks")
        return Evaluation("fail", "missing kitchen execution output or delivery choice")

    if test_case.case_id == "C":
        if "完整解释版" in text and has_delivery_choice(text):
            return Evaluation("pass", "explicit default output produced full version with delivery choice")
        return Evaluation("fail", "explicit default output missing full version or delivery choice")

    if test_case.case_id == "D":
        if "完整解释版" in text:
            return Evaluation("fail", "kitchen execution request included full explanation")
        if has_kitchen_execution_output(text) and has_delivery_choice(text):
            return Evaluation("pass", "explicit kitchen execution output produced with delivery choice")
        return Evaluation("fail", "explicit kitchen execution output missing kitchen version or delivery choice")

    if test_case.case_id == "E":
        if "输出模式" in text:
            return Evaluation("fail", "troubleshooting incorrectly triggered output-mode QA")
        if (
            has_safety_judgment(text)
            and has_any(text, ("原因", "可能"))
            and has_any(text, ("下次", "调整", "修正"))
            and has_memory_action(text)
        ):
            return Evaluation("pass", "troubleshooting diagnosis produced with safety and memory action")
        return Evaluation("fail", "missing troubleshooting safety judgment, diagnosis, or memory action")

    if test_case.case_id == "F":
        if "输出模式" in text:
            return Evaluation("fail", "learning incorrectly triggered output-mode QA")
        if has_any(text, ("一句话解释", "短答", "原理", "水分", "锅温")) and has_learning_expansion(text):
            return Evaluation("pass", "learning short answer produced with progressive disclosure or expansion choices")
        return Evaluation("fail", "missing learning short answer or progressive disclosure hook")

    if test_case.case_id == "G":
        if "输出模式" in text:
            return Evaluation("fail", "meal planning incorrectly triggered output-mode QA")
        if has_full_shopping_list_body(text) and not has_shopping_mode_choice(text):
            return Evaluation("fail", "meal plan dumped full shopping list before mode choice")
        if has_any(text, ("菜单", "menu")) and has_any(text, ("时间线", "排程", "厨房排程", "timeline")):
            return Evaluation("pass", "meal plan produced")
        return Evaluation("fail", "missing meal plan structure")

    if test_case.case_id == "H":
        if "输出模式" in text:
            return Evaluation("fail", "recipe import incorrectly triggered output-mode QA")
        if has_import_intent_split(text) and has_any(text, ("draft", "完整解释版", "厨房执行版")):
            return Evaluation("pass", "recipe import rewrite produced with import intent split")
        return Evaluation("fail", "missing imported recipe import intent split")

    if test_case.case_id == "I":
        if "输出模式" in text:
            return Evaluation("fail", "memory update incorrectly triggered output-mode QA")
        if has_write_preview(text):
            return Evaluation("pass", "memory update write preview produced")
        return Evaluation("fail", "missing memory write preview")

    raise ValueError(f"Unknown test case: {test_case.case_id}")


def build_headless_command(agent: str, prompt: str, root: Path, output_path: Path) -> list[str]:
    if agent == "codex":
        return [
            "codex",
            "exec",
            "--cd",
            str(root),
            "--sandbox",
            "read-only",
            "--ask-for-approval",
            "never",
            "--output-last-message",
            str(output_path),
            prompt,
        ]
    if agent == "claude":
        return ["claude", "--print", "--permission-mode", "dontAsk", prompt]
    if agent == "gemini":
        return ["gemini", "--prompt", prompt, "--skip-trust", "--output-format", "text"]
    if agent == "hermes":
        return ["hermes", "chat", "--query", prompt, "--skills", SKILL_NAME, "--quiet", "--source", "skill-qa"]
    raise ValueError(f"Unknown agent: {agent}")


def build_acp_check_command(agent: str) -> list[str] | None:
    if agent in {"codex", "claude", "gemini"}:
        return ["npx", "-y", "acpx", agent, "--help"]
    if agent == "hermes":
        return ["hermes", "acp", "--check"]
    raise ValueError(f"Unknown agent: {agent}")


def build_acp_command(agent: str, prompt: str, root: Path) -> list[str]:
    base = [
        "npx",
        "-y",
        "acpx",
        "--cwd",
        str(root),
        "--format",
        "text",
        "--timeout",
        "180",
        "--approve-all",
    ]
    if agent in {"codex", "claude", "gemini"}:
        return [*base, agent, "exec", prompt]
    if agent == "hermes":
        return [*base, "--agent", "hermes acp --accept-hooks", "exec", prompt]
    raise ValueError(f"Unknown agent: {agent}")


def command_available(command: list[str]) -> bool:
    executable = command[0]
    return shutil.which(executable) is not None


def run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )


def print_install_checks(root: Path, home: Path) -> int:
    for check in local_install_checks(root, home):
        status = "installed" if check.installed else "missing"
        print(f"{check.agent}: {status}")
        for path in check.paths:
            exists = "yes" if path.exists() else "no"
            print(f"  [{exists}] {path}")
        if not check.installed:
            print(f"  hint: {check.install_hint}")
    return 0


def print_plan(root: Path, home: Path, output_dir: Path) -> int:
    print("# Agent Skill QA Harness Plan\n")
    print("## Local install checks\n")
    print_install_checks(root, home)
    print("\n## Test cases\n")
    print("| Case | Flow | Expectation |")
    print("| --- | --- | --- |")
    for test_case in TEST_CASES.values():
        print(f"| {test_case.case_id} | {test_case.flow} | {test_case.expectation} |")
    print("\n## Headless commands\n")
    first_case = next(iter(TEST_CASES.values()))
    for agent in AGENTS:
        command = build_headless_command(
            agent,
            first_case.prompt,
            root,
            output_dir / f"{agent}-{first_case.case_id}.txt",
        )
        availability = "available" if command_available(command) else "missing executable"
        print(f"- {agent} example ({availability}): {' '.join(command)}")
    print("\nRun without --case to execute the full A-I case matrix.")
    print("\n## ACP checks\n")
    for agent in AGENTS:
        command = build_acp_check_command(agent)
        if command is None:
            print(f"- {agent}: no native ACP command detected in this CLI; use headless fallback.")
            continue
        availability = "available" if command_available(command) else "missing executable"
        print(f"- {agent} ({availability}): {' '.join(command)}")
    return 0


def run_headless(root: Path, agents: list[str], case_ids: list[str], output_dir: Path, timeout_seconds: int) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[RunRecord] = []
    exit_code = 0
    for agent in agents:
        for case_id in case_ids:
            test_case = TEST_CASES[case_id]
            output_path = output_dir / f"{agent}-{case_id}.txt"
            command = build_headless_command(agent, test_case.prompt, root, output_path)
            if not command_available(command):
                evaluation = Evaluation("fail", f"missing executable: {command[0]}")
                records.append(RunRecord(agent, case_id, command, 127, str(output_path), evaluation))
                exit_code = 1
                continue

            completed = run_command(command, timeout_seconds)
            output = completed.stdout
            if agent == "codex" and output_path.exists():
                output = output_path.read_text(encoding="utf-8")
            else:
                output_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")

            evaluation = evaluate_output(test_case, output)
            records.append(RunRecord(agent, case_id, command, completed.returncode, str(output_path), evaluation))
            if completed.returncode != 0 or evaluation.status == "fail":
                exit_code = 1

    report_path = output_dir / "agent-skill-qa-report.jsonl"
    with report_path.open("w", encoding="utf-8") as report:
        for record in records:
            report.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    for record in records:
        print(f"{record.agent} {record.case_id}: {record.evaluation.status} - {record.evaluation.reason}")
    print(f"report: {report_path}")
    return exit_code


def run_acp(root: Path, agents: list[str], case_ids: list[str], output_dir: Path, timeout_seconds: int) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[RunRecord] = []
    exit_code = 0
    for agent in agents:
        for case_id in case_ids:
            test_case = TEST_CASES[case_id]
            output_path = output_dir / f"acp-{agent}-{case_id}.txt"
            command = build_acp_command(agent, test_case.prompt, root)
            if not command_available(command):
                evaluation = Evaluation("fail", f"missing executable: {command[0]}")
                records.append(RunRecord(agent, case_id, command, 127, str(output_path), evaluation))
                exit_code = 1
                continue

            completed = run_command(command, timeout_seconds)
            output_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
            evaluation = evaluate_output(test_case, completed.stdout + completed.stderr)
            records.append(RunRecord(agent, case_id, command, completed.returncode, str(output_path), evaluation))
            if evaluation.status == "fail":
                exit_code = 1

    report_path = output_dir / "agent-skill-qa-acp-report.jsonl"
    with report_path.open("w", encoding="utf-8") as report:
        for record in records:
            report.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    for record in records:
        print(f"acp {record.agent} {record.case_id}: {record.evaluation.status} - {record.evaluation.reason}")
    print(f"report: {report_path}")
    return exit_code


def run_acp_check(agents: list[str], timeout_seconds: int, execute: bool) -> int:
    exit_code = 0
    for agent in agents:
        command = build_acp_check_command(agent)
        if not execute:
            print(f"{agent}: {' '.join(command)}")
            continue
        if not command_available(command):
            print(f"{agent}: missing executable {command[0]}")
            exit_code = 1
            continue
        completed = run_command(command, timeout_seconds)
        status = "ok" if completed.returncode == 0 else "fail"
        print(f"{agent}: {status}")
        if completed.returncode != 0:
            print(completed.stderr.strip())
            exit_code = 1
    return exit_code


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Home directory for local install checks")
    parser.add_argument("--output-dir", type=Path, default=Path("output/agent-skill-qa"), help="Output directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("plan", help="Print install checks and commands without model calls")
    subparsers.add_parser("check-install", help="Check common agent skill install locations")

    run_parser = subparsers.add_parser("run-headless", help="Run selected cases through headless agent CLIs")
    run_parser.add_argument("--agent", choices=AGENTS, action="append", default=[], help="Agent to run")
    run_parser.add_argument("--case", choices=tuple(TEST_CASES), action="append", default=[], help="Case id to run")
    run_parser.add_argument("--timeout", type=int, default=180, help="Per-command timeout in seconds")

    acp_run_parser = subparsers.add_parser("run-acp", help="Run selected cases through acpx ACP client")
    acp_run_parser.add_argument("--agent", choices=AGENTS, action="append", default=[], help="Agent to run")
    acp_run_parser.add_argument("--case", choices=tuple(TEST_CASES), action="append", default=[], help="Case id to run")
    acp_run_parser.add_argument("--timeout", type=int, default=240, help="Per-command timeout in seconds")

    acp_parser = subparsers.add_parser("acp-check", help="Print or run ACP command checks")
    acp_parser.add_argument("--agent", choices=AGENTS, action="append", default=[], help="Agent to check")
    acp_parser.add_argument("--execute", action="store_true", help="Execute ACP check commands")
    acp_parser.add_argument("--timeout", type=int, default=30, help="Per-command timeout in seconds")

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    home = args.home.resolve()
    output_dir = args.output_dir

    if args.command == "plan":
        return print_plan(root, home, output_dir)
    if args.command == "check-install":
        return print_install_checks(root, home)
    if args.command == "run-headless":
        agents = args.agent or list(AGENTS)
        case_ids = args.case or list(TEST_CASES)
        return run_headless(root, agents, case_ids, output_dir, args.timeout)
    if args.command == "run-acp":
        agents = args.agent or list(AGENTS)
        case_ids = args.case or list(TEST_CASES)
        return run_acp(root, agents, case_ids, output_dir, args.timeout)
    if args.command == "acp-check":
        agents = args.agent or list(AGENTS)
        return run_acp_check(agents, args.timeout, args.execute)

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
