# Rookie Cooking Skill

把含糊的菜谱话术改写成新手能执行的厨房步骤：明确克数/毫升、时间、火力、目标状态、失败信号、补救办法和必要的食品安全提示。

适合让 AI Agent 生成菜谱、诊断做菜失败、解释烹饪原理、规划一餐，或把外部菜谱改写成更适合新手执行的格式。

## 功能特点

| 特性 | 说明 |
| --- | --- |
| 执行导向 | 拒绝模糊，每一步操作标准化为「操作、时间、火力、状态、原因」 |
| 故障闭环 | 把“太咸”“出水”“肉柴”“蛋羹蜂窝”映射到原因假设和下次修正 |
| 知识解耦 | 原理卡（Principles）与具体菜肴操作解耦，学会举一反三 |
| 安全优先 | 食品安全边界（中心温度、解冻、生熟分开）优先于口感建议 |
| 记忆适配 | 按用户设备、人数、口味、忌口和历史反馈调整输出 |
| 可打印输出 | 厨房执行版一页打印卡，支持 PDF 渲染和直接打印 |

## 快速开始

推荐用 skill 安装器：

```bash
npx skills add qshan-li/rookie-cooking-skill
```

也可以把这段话发给有 shell 权限的 AI Agent：

```text
帮我安装 rookie-cooking skill。请把 https://github.com/qshan-li/rookie-cooking-skill 克隆到 ~/.local/share/skills/rookie-cooking，然后按我当前使用的 Agent 建立 skill 链接。安装后检查 SKILL.md、templates/、references/、principles/ 是否存在。
```

常见 Agent 的 skill 目录包括：

| Agent | 常见目录 |
| --- | --- |
| Claude Code | `~/.claude/skills/rookie-cooking` |
| Codex | `~/.codex/skills/rookie-cooking` |
| Gemini CLI | `~/.gemini/skills/rookie-cooking` |
| Hermes | `~/.hermes/skills/rookie-cooking` |

更新已安装版本：

```bash
cd ~/.local/share/skills/rookie-cooking
git pull
```

## 使用方式

安装后对 Agent 说：

```text
Use $rookie-cooking 生成 2 人份番茄炒蛋，厨房只有电磁炉和不粘锅。
Use $rookie-cooking 诊断：我做的蒸蛋有很多蜂窝，表面还出水。
Use $rookie-cooking 把红烧肉改成 4 人份，并给我可打印厨房版。
Use $rookie-cooking 为什么炒青菜会出水？
```

支持的主要任务：

| 任务 | 输出 |
| --- | --- |
| 菜谱生成 | 用量、步骤、火力、时间、目标状态、失败信号、替代方案 |
| 失败诊断 | 安全分诊、可能原因、当下补救、下次调整 |
| 原理解释 | 先短答，再按需展开到原理卡 |
| 一餐规划 | 菜单、排程、设备冲突、购物清单选项 |
| 菜谱导入 | 把外部菜谱改写为本项目结构，初始状态为 `draft` |
| 偏好记忆 | 在确认后记录人数、设备、口味、忌口和历史反馈 |

## 输出模式

| 模式 | 说明 |
| --- | --- |
| 完整解释版 | 适合做饭前阅读，解释每一步为什么这样做 |
| 厨房执行版 | 一页打印卡，保留备料、火力/时间、目标状态和出错补救 |
| PDF / 打印 | 将厨房执行版渲染为 PDF 或发送到打印机 |

默认：完整解释版。生成后可选择 PDF 或直接打印。厨房执行版：一页打印卡，适合打印或放在手机上边做边看。

不同 Agent 对交互选择工具的支持不同。Claude Code、Codex、Gemini CLI、Hermes 等环境只要能读取 skill 文件，就可以使用核心提示词；如果当前 Agent 没有交互选择工具，Skill 会按默认输出继续，不会因为缺少选择界面而中断。

## 可选功能

### 运行环境检查

菜谱生成本身不依赖 Python。只有在使用本地记忆、PDF、直接打印或开发校验时，才需要可用的 Python 环境。

如果当前 Agent 有 shell 权限，它可以自行检查运行环境，并把结果记录到 `~/.rookie-cooking/runtime.json`，后续复用已确认的 Python 命令。普通菜谱生成不需要用户手动做环境检查。

如果只是生成菜谱，Python 不可用也可以继续使用默认输出。PDF 或直接打印依赖 Python、相关依赖以及本机 Chrome / Chromium，使用这些功能前由 Agent 检查并提示缺失项即可。

### 本地记忆

用户偏好默认存放在仓库外的 `~/.rookie-cooking/`，也可以用 `ROOKIE_COOKING_HOME` 指向其他目录。

```text
~/.rookie-cooking/
  profile.yaml
  feedback.jsonl
  memory-candidates.jsonl
```

长期偏好、过敏、宗教饮食、疾病相关限制等信息写入前需要用户确认。

### PDF 和打印

PDF 和打印用于把厨房执行版输出成文件或发送到打印机。需要本机 Python 依赖、Chrome / Chromium，以及可用打印机配置。

这些步骤通常由有 shell 权限的 Agent 执行；用户只需要说明要 PDF 还是直接打印，并提供目标菜谱和打印机偏好。

## 仓库内容

```text
rookie-cooking-skill/
├── SKILL.md            # Skill 入口和工作流规则
├── templates/          # 菜谱、厨房版、诊断、原理卡等模板
├── recipes/            # 维护中的结构化菜谱
├── principles/         # 可复用烹饪原理卡
├── references/         # 火力、换算、设备、安全、记忆和来源规则
├── scripts/            # 校验、记忆、PDF 渲染和厨房实测工具
├── tests/              # Python unittest 测试
└── assets/print.css    # 厨房执行版打印样式
```

开发或改内容前，先看 `SKILL.md`、`templates/` 和相关 `references/`。提交前运行：

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## 来源

本仓库的基础菜谱参数主要参考 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)（《程序员做饭指南》，Unlicense），并在此基础上做结构化改写：补充克数/ml、时间区间、火力描述、目标状态、出错补救、替代方案、食品安全提示和相关原理。详见 [`references/source-notes.md`](references/source-notes.md)。

## License

[MIT License](LICENSE)。
