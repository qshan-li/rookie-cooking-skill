# rookie-cooking-skill

**让烹饪从“随缘”走向“可执行”：一套面向 AI Agent 的工程化烹饪执行系统。**

`rookie-cooking-skill` 致力于消除中餐菜谱中诸如“适量”、“大火”、“炒熟”等模糊表述。它不仅是一个菜谱库，更是一个深度结构化的 **Agent Skill**。通过将传统烹饪中的隐性经验拆解为精确的克数/毫升、时间区间、火力等级、目标状态判定、失败信号预警以及底层的烹饪原理，它赋予了 AI Agent 辅助新手在厨房完成“精准执行、故障诊断、原理迁移”的全链路能力。

## Core Values

- **执行导向：** 拒绝模糊，将每一步操作转化为包含“操作、时间、火力、状态、原因”的标准化指令，默认输出可直接上台执行的厨房文档。
- **故障闭环：** 将“做坏了”视为可观测的信号，提供从现象到原因再到下次改进的闭环诊断方案。
- **知识解耦：** 通过原理卡（Principles）将具体的菜肴操作与普适的烹饪科学（如美拉德反应、淀粉糊化）解耦，让新手学会举一反三。
- **安全优先：** 强制集成食品安全边界（中心温度、解冻规则、生熟分开），安全优先级始终高于口感建议。

该项目适合那些追求理性、愿意量化、渴望在厨房获得确定性结果的“硬核新手”。

## What It Does

`rookie-cooking-skill` 让支持 Skill 的 AI agent 生成、改写、检查、诊断和排程家常菜谱。它的默认输出不是一句“炒熟即可”，而是一份能放到厨房台面上执行的文档。

核心能力：

- 完整解释版：适合做饭前阅读，解释每一步为什么这样做。
- 厨房执行版：适合打印或放在手机上边做边看，保留关键步骤、时间、火力和状态判断。
- 失败诊断：把“太咸”“出水”“肉柴”“蛋羹蜂窝”等结果映射到可能原因和下次调整。
- 原理链接：把单道菜的操作连接到可复用的烹饪原理卡。
- 一餐规划：合并多道菜的购物清单、厨房排程、设备冲突和检查节点。
- 菜谱导入：把用户粘贴、外部链接或自创菜谱改写成本项目结构，初始状态为 `draft`。
- 记忆适配：按用户设备、人数、口味、忌口和历史反馈调整输出，但不把一次性请求静默写成长期偏好。
- 安全提示：肉、蛋、海鲜、剩菜、解冻、复热和生熟分开优先于口感建议。

默认假设见 [`references/defaults.md`](references/defaults.md)：2 人份、普通炒锅或煎锅、燃气灶或电磁炉、有手机计时器、有厨房秤，同时提供无秤判断。

## Use Scenarios

### Recipe Generation

用户问“番茄炒蛋怎么做”“给我 4 人份红烧肉”“只要厨房版”。Skill 会生成一道菜的执行文档。

输出强度：

- 默认：完整解释版 + 厨房执行版。
- 快速：压缩解释，但保留克数、时间、状态判断、安全提示和失败信号。
- 精准：增强克数、温度、缩放、设备适配和控制范围。
- 厨房版-only：只给可扫读步骤，但不删除关键安全提示。

### Troubleshooting

用户反馈“肉柴了”“蒸蛋有蜂窝”“青菜出水”。Skill 会给出可能原因、风险判断和下次调整方案。

### Learning

用户问“为什么要上浆”“为什么要热锅冷油”“盐为什么会让黄瓜出水”。Skill 会输出原理卡，并链接到能练习这个原理的菜。

### Meal Planning

用户问“一顿饭怎么安排”“两菜一汤给 3 个人”。Skill 会输出菜单、合并购物清单、厨房时间线、设备冲突和长等待步骤的闹钟建议。

### Recipe Import

用户粘贴菜谱、外部链接摘要或自创做法。Skill 会识别模糊词和缺失参数，按模板改写成完整解释版和厨房执行版；导入菜谱默认是 `draft`，通过 review 后才可标记为 `passed`。

### Memory Init / Update

用户明确说“初始化我的做菜偏好”或“以后默认少辣”。Skill 才会进入偏好初始化或更新流程，记录会改变菜谱参数的信息，例如默认人数、灶具、锅具、是否有秤、是否有温度计、咸淡油辣偏好、忌口和家庭成员。

## Memory Behavior

每次执行时，Skill 会先检查是否有用户 profile 或 memory：

- 有 profile：只读取与当前请求相关的设备、人数、口味、忌口、家庭成员和历史反馈。
- 没有 profile：不阻塞主任务，直接按默认值输出，并在末尾轻提示可以初始化偏好。
- 本次覆盖不等于长期偏好，例如“今天 4 人份”只影响当前请求。
- 长期偏好必须由用户明确表达，例如“以后默认 4 人份”。
- 健康、过敏、宗教、孕期、儿童、疾病和长期忌口等敏感信息，写入长期记忆前必须明确确认。

## Installation

把本仓库作为一个本地 Skill 目录提供给你的 agent。Skill 入口是 [`SKILL.md`](SKILL.md)，展示配置在 [`agents/openai.yaml`](agents/openai.yaml)。

```bash
git clone <this-repository-url> rookie-cooking-skill
cd rookie-cooking-skill
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

通用安装要求：

- 让 agent 能发现本目录。
- 让 agent 在触发 `$rookie-cooking-skill` 时读取根目录的 [`SKILL.md`](SKILL.md)。
- 如果 agent 支持展示元数据，可读取 [`agents/openai.yaml`](agents/openai.yaml)。
- 如果需要本地 personal skill，可把本仓库复制或软链接到对应 agent 的 skills 目录。

调用示例：

```text
Use $rookie-cooking-skill 生成 2 人份番茄炒蛋，厨房只有电磁炉和不粘锅。
```

```text
Use $rookie-cooking-skill 诊断：我做的蒸蛋有很多蜂窝，表面还出水。
```

```text
Use $rookie-cooking-skill 把红烧肉改成 4 人份，并给我可打印厨房版。
```

```text
Use $rookie-cooking-skill 初始化我的做菜偏好。
```

PDF 渲染是可选能力，需要本机有 Chrome 或 Chromium，并能导入 Python `markdown` 包：

```bash
python scripts/render_recipe_pdf.py recipes/vegetable/tomato-egg.md
```

## Repository Layout

```text
.
├── SKILL.md                         # Skill 入口：触发条件、默认假设、工作流和资源导航
├── agents/openai.yaml               # Agent 展示名、短描述和默认调用提示
├── templates/                       # 菜谱、厨房版、原理卡、失败诊断和 review 模板
├── recipes/                         # 已整理菜谱，按类别分组
├── principles/                      # 可复用烹饪原理卡
├── references/                      # 火力、换算、设备、缩放、安全、记忆层和来源规则
├── scripts/                         # 校验、PDF 渲染和厨房实测记录工具
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
  recipes/vegetable/tomato-egg.md \
  output/validation/tomato-egg-validation.json

python scripts/apply_kitchen_validation.py \
  recipes/vegetable/tomato-egg.md \
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
- 厨房友好：厨房执行版要能在手上有水或油时快速扫读。
- 可复盘：失败不是“没天赋”，而是可观察信号、原因假设和下次修正。

## Sources, License, And Thanks

本仓库的标准菜谱基础参数主要参考 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)（《程序员做饭指南》）。HowToCook 使用 [Unlicense](https://github.com/Anduin2017/HowToCook/blob/master/LICENSE) 许可证，将内容释放到 public domain，可自由复制、修改、发布、使用和分发。

本项目在此基础上做了结构化改写，而不是直接复制长段原文：

- 将原菜谱的基础食材、用量和操作顺序作为参考。
- 按本 Skill 模板补充克数 / ml、时间区间、火力描述、目标状态、失败信号、替代方案、食品安全提示和相关原理。
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
