# rookie-cooking

**让烹饪从“随缘”走向“可执行”：一套面向 AI Agent 的工程化烹饪执行系统。**

`rookie-cooking` 致力于消除中餐菜谱中诸如“适量”、“大火”、“炒熟”等模糊表述。它不仅是一个菜谱库，更是一个深度结构化的 **Agent Skill**。通过将传统烹饪中的隐性经验拆解为精确的克数/毫升、时间区间、火力等级、目标状态判定、失败信号预警以及底层的烹饪原理，它赋予了 AI Agent 辅助新手在厨房完成“精准执行、故障诊断、原理迁移”的全链路能力。

## Core Values

- **执行导向：** 拒绝模糊，将每一步操作转化为包含“操作、时间、火力、状态、原因”的标准化指令，默认输出可直接上台执行的厨房文档。
- **故障闭环：** 将“做坏了”视为可观测的信号，提供从现象到原因再到下次改进的闭环诊断方案。
- **知识解耦：** 通过原理卡（Principles）将具体的菜肴操作与普适的烹饪科学（如美拉德反应、淀粉糊化）解耦，让新手学会举一反三。
- **安全优先：** 强制集成食品安全边界（中心温度、解冻规则、生熟分开），安全优先级始终高于口感建议。

该项目适合那些追求理性、愿意量化、渴望在厨房获得确定性结果的“硬核新手”。

## What It Does

`rookie-cooking` 让支持 Skill 的 AI agent 生成、改写、检查、诊断和排程家常菜谱。它的默认输出不是一句“炒熟即可”，而是一份能放到厨房台面上执行的文档。

核心能力：

- 完整解释版：适合做饭前阅读，解释每一步为什么这样做。
- 厨房执行版：适合打印或放在手机上边做边看，采用一页打印卡，保留备料、火力/时间、目标状态和出错补救。
- 失败诊断：把“太咸”“出水”“肉柴”“蛋羹蜂窝”等结果映射到可能原因和下次调整。
- 原理链接：把单道菜的操作连接到可复用的烹饪原理卡。
- 一餐规划：合并多道菜的购物清单、厨房排程、设备冲突和检查节点。
- 菜谱导入：把用户粘贴、外部链接或自创菜谱改写成本项目结构，初始状态为 `draft`。
- 记忆适配：按用户设备、人数、口味、忌口和历史反馈调整输出，但不把一次性请求静默写成长期偏好。
- 安全提示：肉、蛋、海鲜、剩菜、解冻、复热和生熟分开优先于口感建议。

交互原则：

- 先判断流程，再决定是否需要提问。
- 只有安全、持久化、输出形态、购物清单细节、交付方式或长期记忆会被改变时才 elicitation。
- 能用默认值交付有用结果时，不把用户挡在问卷前面。
- Learning 默认先给短答；Meal Planning 先推断规划模式；Recipe Import 先区分持久化目标和输出形态。
- Troubleshooting 先做安全分诊，再给口感或参数调整，并把反馈写入候选记忆前要求确认。

默认假设见 [`references/defaults.md`](references/defaults.md)：2 人份、普通炒锅或煎锅、燃气灶或电磁炉、有手机计时器、有厨房秤，同时提供无秤判断。

## Use Scenarios

### Recipe Generation

用户问“番茄炒蛋怎么做”“给我 4 人份红烧肉”“只要厨房版”。Skill 会生成一道菜的执行文档。

输出模式：

- 默认：完整解释版；生成完成后询问是否需要 PDF 或直接打印。
- 厨房执行版：一页打印卡；生成完成后询问是否需要 PDF 或直接打印。

两个模式后续都可以生成 PDF 或直接打印；PDF / 纸质内容使用厨房执行版。如果运行在 Codex、Claude Code、OpenClaw、Hermes Agent 等支持交互选择的 agent 终端中，且用户没有指定输出模式，Skill 会进入 QA 模式，让用户先选择默认或厨房执行版。若当前 agent 没有选项选择工具，则不阻塞生成，直接使用默认输出模式并简要说明假设。

如果首次生成菜谱时还没有用户 profile，且 agent 支持交互选择，Skill 会在生成前提供一次轻量适配选择：继续使用默认值、仅适配本次、初始化长期偏好。默认选项是继续使用默认值；本次适配不会写入长期记忆。

生成完成后的交付流程也必须使用交互选择工具：生成 PDF、直接打印、暂不需要。选择直接打印时，先列出打印设备并让用户选择；如果当前环境没有打印服务或设备，则提供生成 PDF 或输出厨房执行版文本两个降级选项。一次性生成的 PDF / 打印材料使用 `~/.rookie-cooking/tmp/print-jobs/` 里的临时厨房执行版，不要写入 `recipes/`；渲染成功后临时 Markdown 会被删除。

### Troubleshooting

用户反馈“肉柴了”“蒸蛋有蜂窝”“青菜出水”。Skill 会先做安全分诊，再给出可能原因、风险判断和下次调整方案。诊断后可选择只记录本次反馈、保存长期偏好或不记录。

### Learning

用户问“为什么要上浆”“为什么要热锅冷油”“盐为什么会让黄瓜出水”。Skill 默认先短答，并链接到能练习这个原理的菜；用户可以继续要求完整原理卡、结合一道菜解释或转入失败诊断。

### Meal Planning

用户问“一顿饭怎么安排”“两菜一汤给 3 个人”。Skill 会先推断是按指定菜、按现有食材还是从菜谱推荐，再输出菜单、厨房时间线、设备冲突和长等待步骤的闹钟建议。完整购物清单仍需先选择清单模式。

### Recipe Import

用户粘贴菜谱、外部链接摘要或自创做法。Skill 会先区分持久化目标：只在本次对话改写、保存为 `draft`、或 review existing draft；再按完整解释版、厨房执行版或 PDF / 打印处理输出形态。导入菜谱默认是 `draft`，通过 review 后才可标记为 `passed`。

### Memory Init / Update

用户明确说“初始化我的做菜偏好”或“以后默认少辣”。Skill 才会进入偏好初始化或更新流程，记录会改变菜谱参数的信息，例如默认人数、灶具、锅具、是否有秤、是否有温度计、咸淡油辣偏好、忌口和家庭成员。长期写入前会展示写入预览，并让用户确认写入、编辑或取消。

## Memory Behavior

真实用户记忆默认保存在仓库外的 `~/.rookie-cooking/`，也可以用 `ROOKIE_COOKING_HOME` 指向其他目录：

```text
~/.rookie-cooking/
  profile.yaml
  feedback.jsonl
  memory-candidates.jsonl
```

Skill 通过 `scripts/cooking_memory.py` 读写这些文件，不把真实用户偏好提交进本仓库。常用命令：

```bash
python scripts/cooking_memory.py init-profile
python scripts/cooking_memory.py read --dish tomato-egg --diners self
python scripts/cooking_memory.py update-profile --set defaults.servings=4
python scripts/cooking_memory.py add-feedback --recipe tomato-egg --issue too_salty
python scripts/cooking_memory.py list-candidates
python scripts/cooking_memory.py confirm-candidate <candidate_id>
python scripts/cooking_memory.py view
```

每次执行时，Skill 会先检查是否有用户 profile 或 memory：

- 有 profile：只读取与当前请求相关的设备、人数、口味、忌口、家庭成员和历史反馈。
- 没有 profile：不阻塞主任务，直接按默认值输出，并在末尾轻提示可以初始化偏好。
- 本次覆盖不等于长期偏好，例如“今天 4 人份”只影响当前请求。
- 长期偏好必须由用户明确表达，例如“以后默认 4 人份”。
- 单次反馈先进入 `feedback.jsonl` 或 `memory-candidates.jsonl`，在用户确认前只作为“建议”，不能静默变成默认。
- 健康、过敏、宗教、孕期、儿童、疾病和长期忌口等敏感信息，写入长期记忆前必须明确确认。

## Installation

把本仓库作为一个本地 Skill 目录提供给你的 agent。Skill 入口是 [`SKILL.md`](SKILL.md)，展示配置在 [`agents/openai.yaml`](agents/openai.yaml)。

```bash
git clone <this-repository-url> rookie-cooking
cd rookie-cooking
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
python scripts/sync_skill_install.py
```

通用安装要求：

- 让 agent 能发现本目录。
- 让 agent 在触发 `$rookie-cooking` 时读取根目录的 [`SKILL.md`](SKILL.md)。
- 如果 agent 支持展示元数据，可读取 [`agents/openai.yaml`](agents/openai.yaml)。
- 如果需要本地 personal skill，可把本仓库复制或软链接到对应 agent 的 skills 目录。

调用示例：

```text
Use $rookie-cooking 生成 2 人份番茄炒蛋，厨房只有电磁炉和不粘锅。
```

```text
Use $rookie-cooking 诊断：我做的蒸蛋有很多蜂窝，表面还出水。
```

```text
Use $rookie-cooking 把红烧肉改成 4 人份，并给我可打印厨房版。
```

```text
Use $rookie-cooking 初始化我的做菜偏好。
```

PDF 渲染是可选能力，需要本机有 Chrome 或 Chromium，并能导入 Python `markdown` 包：

```bash
python scripts/render_recipe_pdf.py recipes/vegetable/fan-qie-chao-dan.md
python scripts/render_recipe_pdf.py --kitchen-markdown ~/.rookie-cooking/tmp/print-jobs/print-job.md --title 糖醋排骨 --output-stem tang-cu-pai-gu
```

默认 PDF 输出目录是 `~/.rookie-cooking/output/pdf/`，中间 HTML 文件写入 `~/.rookie-cooking/tmp/pdfs/`。已有菜谱文件会沿用 `.md` 文件名，例如 `fan-qie-chao-dan.md` 输出 `fan-qie-chao-dan-kitchen.pdf`；一次性生成的临时厨房稿应显式传入 `--output-stem <pinyin-slug>`，保持同样的汉语拼音文件名风格。

直接打印会先生成厨房执行版 PDF，再调用系统 `lp` 或 `lpr`：

```bash
python scripts/render_recipe_pdf.py --list-printers
python scripts/render_recipe_pdf.py recipes/vegetable/fan-qie-chao-dan.md --print
python scripts/render_recipe_pdf.py recipes/vegetable/fan-qie-chao-dan.md --print --printer KitchenPrinter
```

当用户选择打印时，先用 `--list-printers` 或系统打印工具列出设备，让用户选择打印设备，再执行 `--print --printer <设备名>`。

## Repository Layout

```text
.
├── SKILL.md                         # Skill 入口：触发条件、默认假设、工作流和资源导航
├── agents/openai.yaml               # Agent 展示名、短描述和默认调用提示
├── templates/                       # 菜谱、厨房版、原理卡、失败诊断和 review 模板
├── recipes/                         # 已整理菜谱，按类别分组
├── principles/                      # 可复用烹饪原理卡
├── references/                      # 火力、换算、设备、缩放、安全、记忆层和来源规则
├── scripts/                         # 校验、记忆、PDF 渲染和厨房实测记录工具
├── tests/                           # Python unittest 测试
├── assets/print.css                 # 厨房执行版打印样式
└── docs/                            # 需求、计划和项目背景文档
```

当前内容基线：

- 385 个 recipe markdown 文件，按 `recipes/` 下的类别组织。
- 10 张核心烹饪原理卡。
- 结构完整性、菜谱质量、来源记录和厨房实测状态校验脚本。

## Quality Gates

新增或改写菜谱必须满足这些底线：

- 有完整解释版和厨房执行版。
- 每个完整步骤包含操作、时间、火力、目标状态、失败信号和原因。
- 原料有克数或毫升，并给出实用的无秤替代判断。
- 禁止无约束使用“适量”“少许”“一会儿”“炒熟”“收汁即可”等模糊词。
- 涉及肉、蛋、海鲜、剩菜、解冻、复热和生食时必须有食品安全提示。
- 至少引用一个已存在的原理卡。
- 参考或改写外部菜谱时，必须更新 [`references/source-notes.md`](references/source-notes.md)。

提交前运行：

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

跨 agent 检查全功能 QA harness：

```bash
python scripts/run_agent_skill_qa.py plan
python scripts/run_agent_skill_qa.py check-install
python scripts/run_agent_skill_qa.py acp-check
```

真实调用 agent 时可先跑单场景，再跑全矩阵：

```bash
python scripts/run_agent_skill_qa.py run-acp --agent gemini --case A
python scripts/run_agent_skill_qa.py run-headless --agent codex --case A
python scripts/run_agent_skill_qa.py run-acp --agent gemini
python scripts/run_agent_skill_qa.py run-headless --agent codex
```

`run-acp` 使用 `acpx <agent> exec` 的一次性会话，不依赖已有 `acpx` session，避免多次测试之间串上下文。
它会为本地受信任 QA prompt 传入 `--approve-all`，确保 agent 能加载 skill；报告会记录 ACP 原始 `returncode`，但 `run-acp` 的退出状态按内容判定结果计算。

要求一定数量的标杆菜完成厨房实测：

```bash
python scripts/check_skill_completeness.py --require-benchmark-validations 3
```

## Common Workflows

新增或改写菜谱：

1. 从 [`templates/recipe-full.md`](templates/recipe-full.md) 和 [`templates/recipe-kitchen.md`](templates/recipe-kitchen.md) 开始。
2. 读取相关规则文件，例如火力用 [`references/heat-levels.md`](references/heat-levels.md)，食品安全用 [`references/food-safety-rules.md`](references/food-safety-rules.md)。
3. 引用相关原理卡，必要时先补充 `principles/`。
4. 在 [`references/source-notes.md`](references/source-notes.md) 记录来源、许可证依据、改写程度和可信度。
5. 运行测试和结构校验。

创建并应用厨房实测记录：

```bash
python scripts/new_kitchen_validation_record.py \
  recipes/vegetable/fan-qie-chao-dan.md \
  output/validation/tomato-egg-validation.json

python scripts/apply_kitchen_validation.py \
  recipes/vegetable/fan-qie-chao-dan.md \
  output/validation/tomato-egg-validation.json \
  --mark-validated
```

准备标杆菜实测包：

```bash
python scripts/prepare_benchmark_validation.py
```

## Design Principles

- 精确，但不伪精确：给默认值、范围、状态判断和调整规则，不把不稳定变量写成唯一答案。
- 操作优先：原理只服务执行、判断、纠错和迁移。
- 安全优先：安全建议和口感建议冲突时，保留安全底线并说明口感取舍。
- 厨房友好：厨房执行版要能在手上有水或油时快速扫读，优先保持一页打印卡结构。
- 可复盘：失败不是“没天赋”，而是可观察信号、原因假设和下次修正。

## Sources, License, And Thanks

本仓库的标准菜谱基础参数主要参考 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)（《程序员做饭指南》）。HowToCook 使用 [Unlicense](https://github.com/Anduin2017/HowToCook/blob/master/LICENSE) 许可证，将内容释放到 public domain，可自由复制、修改、发布、使用和分发。

本项目在此基础上做了结构化改写，而不是直接复制长段原文：

- 将原菜谱的基础食材、用量和操作顺序作为参考。
- 按本 Skill 模板补充克数 / ml、时间区间、火力描述、目标状态、出错补救、替代方案、食品安全提示和相关原理。
- 为每道参考菜谱记录上游 URL、检查日期、许可证依据、改写程度和可信度，详见 [`references/source-notes.md`](references/source-notes.md)。

感谢 HowToCook 作者和社区维护者整理了大量清晰、开放的中文家常菜资料。本仓库的目标是在尊重其开源协议的基础上，把这些菜谱进一步改写成适合 AI agent 生成、适配、打印和复盘的厨房执行文档。

## Contributing

保持修改小而可验证：

- 只改当前任务相关文件。
- Markdown 文件使用 kebab-case 命名。
- 新菜谱对齐现有模板，并补齐来源记录。
- 改 validation 脚本或质量规则时，同步补充 `tests/`。
- 提交前运行：

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## License

当前仓库尚未声明许可证。对外发布或接受外部贡献前，应先补充明确的 `LICENSE` 文件。
