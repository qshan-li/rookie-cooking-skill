# baoyu-skills 对标优化计划

状态：已实施
依据：`JimLiu/baoyu-skills` 仓库结构对比分析
更新日期：2026-05-27

## 1. 任务目标

对标 `JimLiu/baoyu-skills`（19.6k stars）的成熟 Skill 结构规范，优化 `rookie-cooking` 的 SKILL.md 可读性、元数据完整度和用户体验，同时保留本项目在 Flow Matrix、Safety Triage、Quality Gates 等方面的既有优势。

不做的事：

- 不引入 TypeScript/Bun 运行时，本项目保持 Python stdlib。
- 不改变现有的记忆层架构（`~/.rookie-cooking/` + `scripts/cooding_memory.py`）。
- 不引入 EXTEND.md 机制，当前 `profile.yaml` 已满足需求。
- 不做大规模内容重写，只改结构和元数据。

## 2. 优化项清单

| ID | 优化项 | 优先级 | 涉及文件 | 预估改动量 |
|---|---|---|---|---|
| O1 | 补充 SKILL.md frontmatter 元数据 | 高 | `SKILL.md` | 3 行 |
| O2 | Resource Navigation 段落改表格 | 高 | `SKILL.md` | ~40 行重排 |
| O3 | 提取 User Input Tools 声明 | 中 | `SKILL.md` | ~15 行新增 |
| O4 | 补充 Completion Report 模板 | 中 | `SKILL.md` | ~20 行新增 |
| O5 | 提取 Confirmation Policy 声明 | 中 | `SKILL.md` | ~10 行新增 |

## 3. 实施步骤

### Step 1：补充 frontmatter 元数据（O1）

**文件**：`SKILL.md`

**当前状态**：

```yaml
---
name: rookie-cooking
description: Use when generating...
---
```

**目标状态**：

```yaml
---
name: rookie-cooking
description: >-
  Use when generating, adapting, reviewing, or troubleshooting beginner-friendly cooking recipes
  with exact measurements, kitchen execution steps, failure diagnosis, cooking principles,
  substitutions, food-safety checks, equipment adaptation, taste preferences, full recipe output,
  or printable kitchen versions.
version: 1.0.0
homepage: https://github.com/user/rookie-cooking-skill
---
```

**验证**：YAML frontmatter 可被 `scripts/check_skill_completeness.py` 解析，`name` 和 `description` 不变。

### Step 2：Resource Navigation 改表格（O2）

**文件**：`SKILL.md` 的 `## Resource Navigation` section

**当前状态**：30+ 行的无序列表，每行是 `- 文件路径: 用途描述`。

**目标状态**：按功能分组的 Markdown 表格。

```markdown
## Resource Navigation

Read only the files needed for the user request:

### Templates

| 文件 | 用途 |
|---|---|
| `templates/recipe-full.md` | 完整解释版输出 |
| `templates/recipe-kitchen.md` | 厨房执行版输出 |
| `templates/principle-card.md` | 原理卡输出 |
| `templates/failure-diagnosis.md` | 失败诊断输出 |
| `templates/recipe-review-checklist.md` | 菜谱质量审查 |
| `templates/meal-plan.md` | 一餐规划输出 |
| `templates/recipe-changelog.md` | 菜谱变更日志 |
| `templates/imported-recipe-review.md` | 导入菜谱审查 |

### References

| 文件 | 用途 |
|---|---|
| `references/defaults.md` | 默认假设和参数 |
| `references/heat-levels.md` | 火力用语和设备映射 |
| `references/equipment-profiles.md` | 设备特征 |
| `references/unit-conversion.md` | 单位换算和无秤替代 |
| `references/scaling-rules.md` | 份量缩放规则 |
| `references/food-safety-rules.md` | 食品安全规则 |
| `references/cooking-memory-layer.md` | 记忆层边界 |
| `references/user-profile.example.yaml` | 用户偏好结构 |
| `references/feedback-log.example.yaml` | 反馈日志结构 |
| `references/memory-merge-rules.md` | 记忆合并规则 |
| `references/meal-planning-rules.md` | 一餐规划规则 |
| `references/recipe-import-rules.md` | 菜谱导入规则 |
| `references/recipe-versioning.md` | 菜谱版本规则 |
| `references/source-notes.md` | 来源和许可记录 |
| `references/kitchen-validation.md` | 厨房实测规则 |

### Scripts

| 文件 | 用途 |
|---|---|
| `scripts/cooking_memory.py` | 记忆读写 CLI |
| `scripts/render_recipe_pdf.py` | PDF 渲染 |
| `scripts/check_skill_completeness.py` | 结构校验 |
| `scripts/apply_kitchen_validation.py` | 应用厨房实测记录 |
| `scripts/new_kitchen_validation_record.py` | 创建实测记录 |
| `scripts/prepare_benchmark_validation.py` | 准备标杆实测包 |
```

**验证**：表格行数与当前列表项数一致，无遗漏。

### Step 3：提取 User Input Tools 声明（O3）

**文件**：`SKILL.md`，在 `## Default Assumptions` 之后新增 section。

**新增内容**：

```markdown
## User Input Tools

When this skill prompts the user for a choice, follow this tool-selection rule:

1. **Prefer built-in user-input tools** exposed by the current agent runtime — e.g., `AskUserQuestion`, `request_user_input`, `clarify`, `ask_user`, or any equivalent.
2. **Fallback**: if no such tool exists, emit a numbered plain-text message and ask the user to reply with the chosen number/answer for each question.
3. **Batching**: if the tool supports multiple questions per call, combine all applicable questions into a single call; if only single-question, ask them one at a time in priority order.

Do not use a plain-text question in Claude Code or any other runtime that supports structured choices.
```

**验证**：新增 section 不与现有 Interactive QA Mode 内容冲突，后者保留为流程细节。

### Step 4：补充 Completion Report 模板（O4）

**文件**：`SKILL.md`，在 `## Generation Workflow` 的步骤 10 之后新增步骤或在末尾补充。

**新增内容**：

```markdown
## Completion Report

After Recipe Generation finishes, display a structured summary before entering the Post-Generation Delivery Flow:

```text
菜谱生成完成!
菜品: [dish name]
模式: [Default output / Kitchen execution output]
人数: [servings] 人份
设备: [equipment summary]
耗时: [total time]
难度: [difficulty]
相关原理: [principle card names]

偏好/假设: [list of applied preferences or defaults]
记忆状态: [profile exists / using defaults / one-time adaptation]
```

For Meal Planning, the report includes menu, timeline, and equipment conflicts.
For Troubleshooting, the report includes issue label, safety triage result, and memory action taken.
```

**验证**：Completion Report 在 Recipe Generation、Meal Planning、Troubleshooting 三种流程中均有对应模板。

### Step 5：提取 Confirmation Policy 声明（O5）

**文件**：`SKILL.md`，在 `## User Input Tools` 之后新增 section。

**新增内容**：

```markdown
## Confirmation Policy

Default behavior: **confirm before durable writes**.

- Recipe Generation: no confirmation needed for output itself; confirm only before PDF/print delivery.
- Memory Init / Update: show Write preview, then require explicit confirmation before any durable write.
- Recipe Import: confirm persistence target (chat-only / save as draft / review existing).
- Troubleshooting: feedback is recorded as pending candidate unless user confirms durable preference.
- Sensitive data (allergies, pregnancy, child-specific rules, disease, religion, long-term dietary restrictions): require separate explicit confirmation before durable memory.

Skip confirmation only when the user explicitly says to do so, for example: "直接保存", "不用确认", "跳过确认".
```

**验证**：与现有 Memory Init / Update Workflow 和 Troubleshooting Workflow 中的确认逻辑一致。

## 4. 验收标准

### 4.1 结构验收

- [ ] `SKILL.md` 的 YAML frontmatter 包含 `name`、`description`、`version`、`homepage` 四个字段。
- [ ] `SKILL.md` 包含 `## User Input Tools` section。
- [ ] `SKILL.md` 包含 `## Confirmation Policy` section。
- [ ] `SKILL.md` 包含 `## Completion Report` section。
- [ ] `## Resource Navigation` 使用分组表格，行数与改动前列表项数一致。

### 4.2 功能验收

- [ ] `python scripts/check_skill_completeness.py` 通过。
- [ ] `python -m unittest discover -s tests` 全部通过。
- [ ] `SKILL.md` 中所有文件路径引用在仓库中实际存在（可用 `scripts/check_skill_completeness.py` 验证）。

### 4.3 内容验收

- [ ] 新增 section 不与现有 Workflow 描述冲突或重复。
- [ ] 现有的 Interactive QA Mode、First-Run Adaptation、Post-Generation Delivery 等流程逻辑不变。
- [ ] 不引入对仓库外文件的硬编码引用。

## 5. 回滚方案

每个 Step 是独立的 commit。如果某个改动引入问题，`git revert` 对应 commit 即可。各 Step 之间无硬依赖，可单独回滚。
