# Cooking Memory Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local, privacy-first cooking memory layer that reads and writes user cooking preferences outside the skill repository.

**Architecture:** Implement one standard-library Python CLI, `scripts/cooking_memory.py`, as the only read/write path for memory files under `~/.rookie-cooking/` or `ROOKIE_COOKING_HOME`. Keep generated profile data as a small YAML subset and append feedback/candidate events as JSONL. Update skill instructions and repository checks to route memory behavior through the script.

**Tech Stack:** Python standard library, `unittest`, Markdown documentation.

---

### Task 1: Memory CLI Tests

**Files:**
- Create: `tests/test_cooking_memory.py`
- Create later: `scripts/cooking_memory.py`

- [ ] Add tests that load `scripts/cooking_memory.py` through `importlib`.
- [ ] Cover `ROOKIE_COOKING_HOME`, no-memory reads, profile reads, dish feedback filtering, diner filtering, candidate lifecycle, sensitive-write confirmation, malformed profile handling, malformed JSONL skipping, and profile atomic updates.
- [ ] Run `python -m unittest tests.test_cooking_memory` and confirm tests fail because the script does not exist yet.

### Task 2: Memory CLI Implementation

**Files:**
- Create: `scripts/cooking_memory.py`

- [ ] Add path resolution, small YAML read/write helpers, JSONL read/append helpers, and CLI argument parsing.
- [ ] Implement `read`, `init-profile`, `view`, `update-profile`, `add-feedback`, `list-candidates`, `confirm-candidate`, `reject-candidate`, `delete`, and `ignore-once`.
- [ ] Run `python -m unittest tests.test_cooking_memory` and make it pass.

### Task 3: Repository Gates

**Files:**
- Modify: `scripts/check_skill_completeness.py`
- Modify: `tests/test_check_skill_completeness.py`

- [ ] Add `scripts/cooking_memory.py` to required structure paths.
- [ ] Add/update the structure test assertion.
- [ ] Run `python -m unittest tests.test_check_skill_completeness`.

### Task 4: Skill and Reference Docs

**Files:**
- Modify: `SKILL.md`
- Modify: `references/cooking-memory-layer.md`
- Modify: `references/memory-merge-rules.md`
- Modify: `README.md`

- [ ] Document `scripts/cooking_memory.py` as the preferred memory read/write path.
- [ ] Document `~/.rookie-cooking/`, `ROOKIE_COOKING_HOME`, `profile.yaml`, `feedback.jsonl`, and `memory-candidates.jsonl`.
- [ ] Clarify that pending feedback is labeled as a suggestion, not a default.
- [ ] Add user-facing command examples to README.

### Task 5: Final Verification

**Files:**
- Verify all touched files.

- [ ] Run `python -m unittest discover -s tests`.
- [ ] Run `python scripts/check_skill_completeness.py`.
- [ ] Review `git diff --check`.
- [ ] Review `git diff --stat` and confirm only memory-layer files plus the plan changed.
