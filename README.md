# Rookie Cooking Skill

**面向 AI Agent 的工程化烹饪执行系统 —— 把"适量""大火""炒熟"变成可执行的厨房文档。**

一个结构化的 Agent Skill，通过精确克数/毫升、时间区间、火力等级、目标状态判定、失败信号预警和烹饪原理卡，让 AI Agent 赋能新手在厨房完成「精准执行 → 故障诊断 → 原理迁移」的全链路闭环。

## Features

- **执行导向** — 拒绝模糊，每一步操作标准化为「操作、时间、火力、状态、原因」
- **故障闭环** — 把"太咸""出水""肉柴""蛋羹蜂窝"映射到原因假设和下次修正
- **知识解耦** — 原理卡（Principles）与具体菜肴操作解耦，学会举一反三
- **安全优先** — 食品安全边界（中心温度、解冻、生熟分开）优先于口感建议
- **记忆适配** — 按用户设备、人数、口味、忌口和历史反馈调整输出
- **可打印输出** — 厨房执行版一页打印卡，支持 PDF 渲染和直接打印

## 30 秒开始

**一行命令安装（推荐）：**

```bash
npx skills add qshan-li/rookie-cooking-skill
```

**也可以直接把这段话发给有 shell 权限的 AI Agent：**

```
帮我安装 rookie-cooking skill。请把 https://github.com/qshan-li/rookie-cooking-skill 克隆到 ~/.local/share/skills/rookie-cooking，然后为已安装的 agent 创建符号链接：Claude Code 链接到 ~/.claude/skills/rookie-cooking，Codex 链接到 ~/.codex/skills/rookie-cooking，Gemini 链接到 ~/.gemini/skills/rookie-cooking，Hermes 链接到 ~/.hermes/skills/rookie-cooking。安装完成后检查 SKILL.md、templates/、references/、principles/ 是否存在。
```

**已经安装过的话，用这段话更新：**

```
帮我更新 rookie-cooking skill。请进入 ~/.local/share/skills/rookie-cooking 执行 git pull，然后告诉我当前最新 commit。
```

**安装后直接对 Agent 说：**

```
Use $rookie-cooking 生成 2 人份番茄炒蛋，厨房只有电磁炉和不粘锅。
Use $rookie-cooking 诊断：我做的蒸蛋有很多蜂窝，表面还出水。
Use $rookie-cooking 把红烧肉改成 4 人份，并给我可打印厨房版。
```

## Output Modes

| 模式 | 说明 |
|------|------|
| 完整解释版 | 适合做饭前阅读，解释每一步为什么这样做 |
| 厨房执行版 | 一页打印卡，保留备料、火力/时间、目标状态和出错补救 |
| PDF / 打印 | 厨房执行版渲染为 PDF 或调用系统打印机 |

默认：完整解释版；生成完成后询问是否需要 PDF 或直接打印。厨房执行版：一页打印卡，适合打印或放在手机上边做边看。在支持交互选择的 agent 终端（Claude Code、Codex、OpenClaw、Hermes Agent）中，如果用户没有指定输出模式，Skill 会进入 QA 模式让用户先选择。若当前 agent 没有选项选择工具，则不阻塞生成，直接使用默认输出模式并简要说明假设。

## Use Scenarios

| 场景 | 说明 |
|------|------|
| **菜谱生成** | 输入菜名，生成包含用量、步骤、状态判断的执行文档 |
| **失败诊断** | 反馈"肉柴了""蒸蛋蜂窝"，先安全分诊，再给原因和修正方案 |
| **原理学习** | 问"为什么要上浆""热锅冷油为什么"，短答 + 链接到练习菜 |
| **一餐规划** | 多道菜的购物清单、厨房排程、设备冲突和长等待闹钟建议 |
| **菜谱导入** | 粘贴外部菜谱或自创做法，改写为本项目结构，初始状态 `draft` |
| **偏好初始化** | 记录默认人数、灶具、锅具、咸淡油辣偏好、忌口等长期偏好 |

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Claude Code | Supported | 原生 skill workflow |
| Codex | Supported | 完整 QA 支持 |
| OpenClaw / Hermes Agent | Supported | 交互选择 + skill 加载 |
| Cursor / 其他本地 Agent | Usable | 需要文件读写和 shell 执行 |

## Memory Behavior

用户记忆存储在仓库外 `~/.rookie-cooking/`（可通过 `ROOKIE_COOKING_HOME` 自定义）：

```text
~/.rookie-cooking/
  profile.yaml              # 长期偏好：人数、设备、口味、忌口
  feedback.jsonl            # 单次反馈记录
  memory-candidates.jsonl   # 待确认的记忆候选
```

常用命令：

```bash
python scripts/cooking_memory.py init-profile
python scripts/cooking_memory.py view
python scripts/cooking_memory.py update-profile --set defaults.servings=4
python scripts/cooking_memory.py add-feedback --recipe tomato-egg --issue too_salty
python scripts/cooking_memory.py list-candidates
python scripts/cooking_memory.py confirm-candidate <candidate_id>
```

关键规则：

- 没有 profile 时不阻塞主任务，按默认值输出
- 单次反馈先进入候选，用户确认前不变成默认
- 健康、过敏、宗教等敏感信息写入前必须明确确认

## Installation

### 依赖

- Python 3.10+
- `pip install pyyaml markdown`（烹饪记忆和 PDF 渲染必需）
- `pip install zeroconf`（可选，用于自动发现网络打印机）
- Chrome/Chromium（可选，PDF 渲染需要）

### 方式一：一行命令安装（推荐）

```bash
npx skills add qshan-li/rookie-cooking-skill
```

自动检测你安装的 agent，创建对应的符号链接。支持 Claude Code、Codex、Gemini CLI、Hermes 等 50+ 个 agent。

### 方式二：把下面这段话直接发给 AI

```
帮我安装 rookie-cooking skill。请把 https://github.com/qshan-li/rookie-cooking-skill 克隆到 ~/.local/share/skills/rookie-cooking，然后为已安装的 agent 创建符号链接：Claude Code 链接到 ~/.claude/skills/rookie-cooking，Codex 链接到 ~/.codex/skills/rookie-cooking，Gemini 链接到 ~/.gemini/skills/rookie-cooking，Hermes 链接到 ~/.hermes/skills/rookie-cooking。安装完成后检查 SKILL.md、templates/、references/、principles/ 是否存在。
```

更新：

```
帮我更新 rookie-cooking skill。请进入 ~/.local/share/skills/rookie-cooking 执行 git pull，然后告诉我当前最新 commit。
```

### 方式三：手动安装

克隆仓库：

```bash
git clone https://github.com/qshan-li/rookie-cooking-skill.git ~/.local/share/skills/rookie-cooking
```

安装 Python 依赖：

```bash
pip install pyyaml markdown
```

按你使用的 agent 创建符号链接：

**Claude Code**

```bash
ln -s ~/.local/share/skills/rookie-cooking ~/.claude/skills/rookie-cooking
```

**Codex**

```bash
ln -s ~/.local/share/skills/rookie-cooking ~/.codex/skills/rookie-cooking
```

**Gemini CLI**

```bash
ln -s ~/.local/share/skills/rookie-cooking ~/.gemini/skills/rookie-cooking
```

**Hermes Agent**

```bash
ln -s ~/.local/share/skills/rookie-cooking ~/.hermes/skills/rookie-cooking
```

### 验证安装

检查符号链接和关键文件是否存在：

```bash
# Claude Code
ls ~/.claude/skills/rookie-cooking/SKILL.md

# Codex
ls ~/.codex/skills/rookie-cooking/SKILL.md

# Gemini CLI
ls ~/.gemini/skills/rookie-cooking/SKILL.md

# Hermes Agent
ls ~/.hermes/skills/rookie-cooking/SKILL.md
```

或使用内置检查：

```bash
python scripts/run_agent_skill_qa.py install-check
```

### PDF 渲染（可选）

```bash
python scripts/render_recipe_pdf.py recipes/vegetable/fan-qie-chao-dan.md
python scripts/render_recipe_pdf.py --list-printers
python scripts/render_recipe_pdf.py recipes/vegetable/fan-qie-chao-dan.md --print
```

选择打印设备时，先用 `--list-printers` 列出设备，让用户选择打印设备，再执行 `--print --printer <设备名>`。一次性生成的 PDF / 打印材料使用 `~/.rookie-cooking/tmp/print-jobs/` 里的临时厨房执行版，不要写入 `recipes/`。

## Directory Structure

```text
rookie-cooking-skill/
├── SKILL.md                    # Skill 入口：触发条件、默认假设、工作流和资源导航
├── agents/openai.yaml          # Agent 展示名、短描述和默认调用提示
├── templates/                  # 菜谱、厨房版、原理卡、失败诊断和 review 模板
├── recipes/                    # 已整理菜谱（385 道），按类别分组
├── principles/                 # 可复用烹饪原理卡（22 张）
├── references/                 # 火力、换算、设备、缩放、安全、记忆层和来源规则
├── scripts/                    # 校验、记忆、PDF 渲染和厨房实测记录工具
├── tests/                      # Python unittest 测试
├── assets/print.css            # 厨房执行版打印样式
└── docs/                       # 需求、计划和项目背景文档
```

## Quality Gates

新增或改写菜谱必须满足：

- 有完整解释版和厨房执行版
- 每个步骤包含操作、时间、火力、目标状态、失败信号和原因
- 原料有克数/毫升，并给出无秤替代判断
- 禁止无约束的"适量""少许""炒熟""收汁即可"等模糊词
- 肉、蛋、海鲜、剩菜、解冻、复热必须有食品安全提示
- 至少引用一个原理卡
- 参考外部菜谱时更新 [`references/source-notes.md`](references/source-notes.md)

提交前运行：

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## Design Principles

1. **精确，但不伪精确** — 给默认值、范围、状态判断和调整规则，不把不稳定变量写成唯一答案
2. **操作优先** — 原理只服务执行、判断、纠错和迁移
3. **安全优先** — 安全建议和口感建议冲突时，保留安全底线并说明口感取舍
4. **厨房友好** — 执行版能在手上有水或油时快速扫读，保持一页打印卡结构
5. **可复盘** — 失败不是"没天赋"，而是可观察信号、原因假设和下次修正

## Common Workflows

**新增或改写菜谱：**

1. 从 [`templates/recipe-full.md`](templates/recipe-full.md) 和 [`templates/recipe-kitchen.md`](templates/recipe-kitchen.md) 开始
2. 读取规则文件：[`references/heat-levels.md`](references/heat-levels.md)、[`references/food-safety-rules.md`](references/food-safety-rules.md)
3. 引用相关原理卡，必要时先补充 `principles/`
4. 在 [`references/source-notes.md`](references/source-notes.md) 记录来源
5. 运行测试和结构校验

**厨房实测：**

```bash
python scripts/new_kitchen_validation_record.py \
  recipes/vegetable/fan-qie-chao-dan.md \
  output/validation/tomato-egg-validation.json

python scripts/apply_kitchen_validation.py \
  recipes/vegetable/fan-qie-chao-dan.md \
  output/validation/tomato-egg-validation.json \
  --mark-validated
```

## FAQ

**为什么要用这个而不是直接搜菜谱？** — 传统菜谱的"适量""大火""炒熟"对新手是黑箱。本项目把隐性经验拆解为可执行的参数和状态判断，让新手第一次做也能出可预期的结果。

**没有厨房秤怎么办？** — 每道菜谱都提供无秤替代判断（如"大约一个鸡蛋大小""铺满锅底薄薄一层"），但有秤更精确。

**可以导入自己的菜谱吗？** — 可以。把菜谱文本粘贴给 Skill，或描述你的自创做法，Skill 会改写为本项目结构，初始状态为 `draft`，通过 review 后标记为 `passed`。

**怎么更新？** — `git pull` 拉取最新内容即可。

## Sources

本仓库的基础参数主要参考 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)（《程序员做饭指南》，[Unlicense](https://github.com/Anduin2017/HowToCook/blob/master/LICENSE)）。在此基础上做了结构化改写：补充克数/ml、时间区间、火力描述、目标状态、出错补救、替代方案、食品安全提示和相关原理。详见 [`references/source-notes.md`](references/source-notes.md)。

## Contributing

- 只改当前任务相关文件
- Markdown 文件使用 kebab-case 命名
- 新菜谱对齐现有模板，补齐来源记录
- 改 validation 脚本或质量规则时，同步补充 `tests/`
- 提交前运行 `python -m unittest discover -s tests` 和 `python scripts/check_skill_completeness.py`

## License

[MIT License](LICENSE)。
