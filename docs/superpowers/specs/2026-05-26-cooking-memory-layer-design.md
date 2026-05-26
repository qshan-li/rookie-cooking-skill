# Rookie Cooking Memory Layer Design

Date: 2026-05-26
Status: Approved for planning

## Context

`rookie-cooking-skill` already defines memory boundaries in `SKILL.md`,
`references/cooking-memory-layer.md`, `references/user-profile.example.yaml`,
`references/feedback-log.example.yaml`, and
`references/memory-merge-rules.md`. The missing piece is an actual
persistence contract that lets the skill read and update user cooking
preferences without committing private user data into the skill repository.

The design follows three observed patterns from mature skill systems:

- Keep real user state outside the skill source tree.
- Make memory structured, inspectable, and explicitly scoped.
- Treat low-confidence or sensitive memory as a candidate until the user
  confirms it.

GStack's local learnings model is the closest fit: project-scoped structured
state lives in a user-owned local directory and is read by many skills. Compound
Engineering's `docs/solutions/` model is useful for durable team knowledge, but
cooking preferences are personal and privacy-sensitive, so they should not
default to a repo-tracked docs directory.

## Goals

- Generate recipes, meal plans, and troubleshooting advice using remembered
  servings, equipment, taste, dislikes, household members, and recipe feedback.
- Store real user data outside the repo by default.
- Keep the memory files human-readable and easy to inspect, edit, back up, or
  delete.
- Require explicit confirmation before durable preference writes.
- Keep one-off requests as session-only overrides.
- Preserve the existing safety-first merge priority.
- Provide a small script interface so the skill does not scatter YAML or JSONL
  writes through prompts.

## Non-Goals

- No vector database or semantic retrieval in v1.
- No cloud sync in v1.
- No automatic ingestion of all conversation history.
- No hidden writes into Claude Code, Codex, or other host-specific memory.
- No medical or nutrition personalization beyond respecting user-stated
  constraints and food-safety rules.

## Storage

The default memory root is:

```text
~/.rookie-cooking/
```

The user or test suite can override it with:

```bash
ROOKIE_COOKING_HOME=/custom/path
```

The v1 files are:

```text
~/.rookie-cooking/
  profile.yaml
  feedback.jsonl
  memory-candidates.jsonl
```

`profile.yaml` is the durable profile. It contains only user-confirmed defaults,
equipment, taste, dislikes, household members, and confirmed recipe-level
preferences.

`feedback.jsonl` is an append-only event log for cooking feedback. Entries start
as `pending-confirmation` unless the user explicitly states a durable rule.

`memory-candidates.jsonl` is an append-only queue of suggested durable memories.
Candidates may be proposed from feedback, repeated session overrides, or user
language that implies a preference but is not explicit enough to write directly.

The repo keeps examples and schema documentation only. It must not ship or
commit a real `~/.rookie-cooking/` profile.

## Data Model

The existing `references/user-profile.example.yaml` remains the profile shape.
Implementation may add `schema_version` fields, but the v1 logical fields are:

- `defaults`: serving count and preferred output strength.
- `taste`: salt, oil, spice, sweetness, and sourness levels.
- `equipment`: stove, pan, scale, thermometer, oven, and air fryer availability.
- `dislikes`: ingredients and aromatics to avoid when practical.
- `household_members`: named diners with taste, dislikes, and sensitive
  constraints.
- `recipe_preferences`: confirmed dish-specific adjustments.
- `feedback_history`: optional embedded history for small profiles; the primary
  write path is still `feedback.jsonl`.
- `memory_metadata`: source, confidence, and write policy.

Feedback entries follow the existing `references/feedback-log.example.yaml`
shape, adapted to one JSON object per line:

```json
{
  "entry_id": "2026-05-26-tomato-egg-too-salty",
  "recipe_id": "tomato-egg",
  "recipe_name": "番茄炒蛋",
  "created_at": "2026-05-26T12:00:00+08:00",
  "eaten_by": ["self"],
  "feedback": {
    "result": "edible",
    "issue": "too_salty",
    "observation": "用户反馈成品偏咸。"
  },
  "suggested_adjustment": {
    "salt_multiplier": 0.85,
    "note": "下次先减少盐，出锅前再补味。"
  },
  "memory_candidate": {
    "scope": "recipe-specific",
    "key": "recipe_preferences.tomato-egg.salt_multiplier",
    "value": 0.85,
    "confidence": 0.6,
    "source": "observed-feedback",
    "requires_confirmation": true
  },
  "status": "pending-confirmation"
}
```

## Script Interface

Add one standard-library Python script:

```bash
python scripts/cooking_memory.py <command> [options]
```

The script owns all file reads, writes, validation, and merge output. The skill
uses the script instead of editing memory files directly.

Required commands:

```bash
python scripts/cooking_memory.py read --dish tomato-egg --diners self
python scripts/cooking_memory.py init-profile
python scripts/cooking_memory.py view
python scripts/cooking_memory.py update-profile --set defaults.servings=4
python scripts/cooking_memory.py add-feedback --recipe tomato-egg --issue too_salty
python scripts/cooking_memory.py list-candidates
python scripts/cooking_memory.py confirm-candidate <candidate_id>
python scripts/cooking_memory.py reject-candidate <candidate_id>
python scripts/cooking_memory.py delete <path-or-id>
python scripts/cooking_memory.py ignore-once --dish tomato-egg
```

The `read` command returns a compact JSON object designed for direct prompt use.
It includes only relevant fields for the requested dish, diners, equipment, and
historical feedback.

Example:

```json
{
  "memory_found": true,
  "applied": {
    "servings": {"value": 2, "source": "profile.defaults"},
    "equipment": {
      "has_scale": {"value": true, "source": "profile.equipment"},
      "has_thermometer": {"value": false, "source": "profile.equipment"}
    },
    "taste": {
      "salt_level": {"value": "normal", "source": "profile.taste"},
      "spice_level": {"value": "mild", "source": "profile.taste"}
    },
    "recipe_feedback": [
      {
        "recipe_id": "tomato-egg",
        "adjustment": "salt_multiplier=0.85",
        "source": "feedback.jsonl",
        "status": "pending-confirmation",
        "confidence": 0.6,
        "label": "suggestion"
      }
    ]
  },
  "notices": [
    "Recipe feedback is pending confirmation, so label it as a suggestion."
  ]
}
```

If no profile exists, `read` returns `memory_found: false` and the skill proceeds
with existing defaults.

## Read Flow

For recipe generation, troubleshooting, meal planning, and recipe import:

1. Identify flow, dish, serving override, output strength, and named diners.
2. Run `cooking_memory.py read` when the script exists.
3. If memory is unavailable, continue with skill defaults.
4. Apply defaults first, then durable profile preferences, then relevant
   dish-level feedback, then the user's explicit current-turn overrides.
5. Treat pending or low-confidence feedback as suggestions, not defaults.
6. State the applied preferences or assumptions in the output.

The skill should not block normal recipe generation just because memory is
missing, unreadable, or uninitialized.

## Write Flow

The skill enters memory writing only when the user explicitly asks to initialize
or update durable preferences, or when the user confirms a memory candidate.

Examples that can write directly:

- "初始化我的做菜偏好。"
- "以后默认 4 人份。"
- "以后我都少辣。"
- "以后番茄炒蛋都少放盐。"

Examples that must stay session-only:

- "今天 4 人份。"
- "这次做给 3 个人。"
- "今晚不要放香菜。"

Examples that create pending feedback or a candidate:

- "这次番茄炒蛋太咸了。"
- "上次红烧肉肉柴。"
- "我好像不太喜欢太甜。"

Sensitive constraints require explicit confirmation before durable write:

- allergies
- health conditions
- pregnancy
- child-specific food rules
- religion or ethical diet restrictions
- long-term dietary restrictions

## Merge Rules

The merge priority remains:

```text
food safety and sensitive constraints
> explicit current request
> named household members
> recipe-specific confirmed preferences and feedback suggestions
> global profile preferences
> skill defaults
```

For multiple diners:

- Dislikes and safety constraints are combined.
- Salt, oil, and spice levels choose the conservative shared setting.
- The recipe may suggest split finishing, such as adding chili oil or salt at
  the table for diners who want more.

Safety overrides taste. When a safety requirement worsens texture or flavor,
the output explains the tradeoff briefly.

## Output Requirements

Any recipe, meal plan, or troubleshooting answer that used memory must include a
short applied-memory section:

```text
本次使用的偏好 / 假设：
- 人数：长期默认 2 人份，本次未覆盖
- 设备：有电子秤、无温度计
- 口味：少辣、正常盐
- 历史反馈：番茄炒蛋上次偏咸，本次盐减少 15%（建议，待确认）
```

If no memory exists, the output says it used defaults and may briefly mention
that the user can initialize cooking preferences.

When memory is used, the user must have an obvious way to view, change, delete,
or temporarily ignore remembered preferences.

## Error Handling

Missing memory files are not errors.

Malformed `profile.yaml` should produce a clear script error and the skill should
fall back to defaults for the current response. The final output should mention
that cooking memory was skipped due to invalid local memory data.

Malformed JSONL lines should be skipped with warnings in script output. Valid
lines before and after the malformed entry should still be usable.

Write commands should create parent directories as needed. They should fail
explicitly when the target path is not writable.

The script should use atomic writes for `profile.yaml`: write a temporary file in
the same directory, then replace the original.

Append-only files should write one complete line per event.

## Privacy

The v1 design is local-only. No network sync is part of the implementation.

The memory root is outside the repo to avoid accidental commits. If a future
implementation adds a sample `memory/` directory for tests, it must be fixture
data only.

The script should avoid printing sensitive values unless the user asks to view
memory. Even then, it should preserve human readability rather than hide data
behind opaque hashes, because user auditability is a core requirement.

## Documentation Changes

Update these files during implementation:

- `SKILL.md`: clarify that the script is the preferred memory read/write path.
- `references/cooking-memory-layer.md`: document storage, commands, and
  confirmation gates.
- `references/user-profile.example.yaml`: keep as canonical profile example.
- `references/feedback-log.example.yaml`: keep as canonical feedback example.
- `references/memory-merge-rules.md`: align wording with script output labels.
- `README.md`: add user-facing setup and usage examples.

## Tests

Add focused `unittest` coverage for:

- resolving `ROOKIE_COOKING_HOME`
- returning defaults when no memory exists
- reading a valid profile
- filtering recipe feedback by dish
- filtering household members by requested diners
- producing pending candidate records from feedback
- confirming candidates into `profile.yaml`
- rejecting candidates without mutating profile
- refusing sensitive durable writes without confirmation
- handling malformed profile data with explicit errors
- skipping malformed JSONL feedback lines while preserving valid entries
- atomic profile updates through temp-file replacement

Existing repository checks should continue to pass:

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## Implementation Scope

This is a single implementation unit:

1. Add the memory script and tests.
2. Update skill instructions and references to use the script.
3. Update README examples.
4. Run the test suite and completeness check.

Do not add cloud sync, MCP integration, vector retrieval, or host-specific memory
integration in this implementation.
