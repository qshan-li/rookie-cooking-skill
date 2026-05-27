# 做菜 Skill 执行文档

状态：执行计划版
依据：`docs/cooking-skill-requirements.md`、OpenAI 官方 `openai/skills` 仓库成熟 Skill 目录模式
更新日期：2026-05-26

## 1. 任务目标

本任务的目标是把当前需求文档落成一个可安装、可维护、可扩展的 `rookie-cooking`。

交付结果必须满足三件事：

- 形成符合 Agent Skill 惯例的目录结构：`SKILL.md` 为入口，长内容拆到 `references/`、`templates/`、`principles/`、`recipes/` 等目录。
- 先完成 P0 能力：默认生成完整解释版菜谱、厨房执行版、精确参数、状态判断、失败诊断、替代方案、食品安全提示。
- 给后续 P1 记忆层、个性化调参、一餐规划和 PDF 输出留下清晰边界，但不在第一轮过度实现。

## 2. 结构原则

成熟 Skill 的共性是入口短、资源分层、按需加载：

- `SKILL.md` 只放触发条件、核心工作流、默认假设、输出规则和资源导航。
- `agents/openai.yaml` 放 UI 展示信息和默认调用提示。
- `references/` 放需要按需读取的长规则、标准和领域说明。
- `scripts/` 只放需要确定性执行的工具，不为一次性手工流程写脚本。
- `assets/` 只放输出需要复用的静态资源。

本项目采用仓库根目录作为 Skill 根目录，避免再嵌套一层 `cooking-skill/`：

```text
rookie-cooking/
  SKILL.md
  agents/
    openai.yaml
  templates/
    recipe-full.md
    recipe-kitchen.md
    principle-card.md
    failure-diagnosis.md
    recipe-review-checklist.md
  principles/
    protein-denaturation.md
    maillard.md
    starch-gelatinization.md
    velveting.md
    salt-water-migration.md
    seasoning-balance.md
    blanching.md
    oil-temperature-smoke-point.md
    wok-heat.md
    food-safety-temperature.md
  recipes/
    vegetable/
      fan-qie-chao-dan.md
      qing-chao-xiao-qing-cai.md
    meat/
      qing-jiao-rou-si.md
      hong-shao-rou.md
    soup/
      zheng-dan-geng.md
  references/
    defaults.md
    heat-levels.md
    unit-conversion.md
    equipment-profiles.md
    scaling-rules.md
    food-safety-rules.md
    cooking-memory-layer.md
    source-notes.md
  scripts/
    render_recipe_pdf.py
  assets/
    print.css
  docs/
    cooking-skill-requirements.md
    cooking-skill-execution-plan.md
```

目录职责：

| 路径 | 职责 |
| --- | --- |
| `SKILL.md` | Agent 实际读取的主入口，保持短、可执行、可导航。 |
| `agents/openai.yaml` | Skill 展示名、短描述、默认调用提示。 |
| `templates/` | 菜谱、厨房版、原理卡、失败诊断和 review 清单模板。 |
| `principles/` | 可复用原理卡，支持 Learning 模式和菜谱反向链接。 |
| `recipes/` | 标杆菜和后续 V1 菜谱内容。 |
| `references/` | 默认假设、火力、换算、设备、缩放、安全、记忆层等长规则。 |
| `scripts/` | 可重复、确定性的辅助脚本。V1 只保留 PDF 渲染脚本。 |
| `assets/` | 打印样式等输出资产。 |
| `docs/` | 需求、计划和项目内执行资料，不作为 Skill 运行入口。 |

标准菜谱基准来源：

- 标准菜谱的基础参考来源标明为 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)。
- 只参考具体菜谱的原料、计算和基础操作，不直接 fork 整个仓库。
- 每道参考或改写的菜谱必须在 `references/source-notes.md` 记录上游 URL、检查日期、许可证依据、改写程度和本 Skill 补充的状态判断 / 失败诊断 / 原理说明。

## 3. 执行步骤

### Step 1：建立 Skill 入口和元数据

目标：让项目具备最小可安装 Skill 形态。

执行：

- 新建 `SKILL.md`。
- 新建 `agents/openai.yaml`。
- 在 `SKILL.md` frontmatter 中声明 `name` 和覆盖目标模式、Learning 模式、快速模式、精准模式的 `description`。
- 在 `SKILL.md` 正文写入默认假设、模式选择、输出顺序、资源导航和安全优先规则。
- 在 `agents/openai.yaml` 写入显示名、短描述和默认调用提示。

验收：

- `SKILL.md` 存在合法 YAML frontmatter，至少包含 `name` 和 `description`。
- `description` 能明确触发“生成新手友好菜谱、厨房执行版、失败诊断、做菜原理解释、设备/口味适配”。
- `SKILL.md` 不复制整份需求文档，只保留执行必须读的规则和引用路径。
- `agents/openai.yaml` 中的展示文案与 `SKILL.md` 能力一致。

### Step 2：沉淀模板层

目标：先固定输出格式，避免每道菜各写各的。

执行：

- 新建 `templates/recipe-full.md`，覆盖完整解释版菜谱字段。
- 新建 `templates/recipe-kitchen.md`，覆盖厨房执行版字段。
- 新建 `templates/principle-card.md`，覆盖 Learning 模式原理卡字段。
- 新建 `templates/failure-diagnosis.md`，覆盖通用失败诊断和单菜专属诊断字段。
- 新建 `templates/recipe-review-checklist.md`，覆盖执行完整性、参数可靠性、原理匹配、安全检查和厨房友好性。

验收：

- 完整解释版模板包含：菜名、难度、时间、份量、热量估算、设备、成品目标、原料工具、缩放表、预处理、操作步骤、关键判断点、失败诊断、替代方案、相关原理。
- 每个操作步骤强制包含：操作、时间、火力、目标状态、失败信号、为什么。
- 厨房执行版模板包含：菜名、单行元信息、备料、做法表、关键安全 / 补救提示。
- 厨房执行版模板保持一页打印卡结构，并默认省略长原理解释。
- review 清单可用于阻止不合格菜谱进入 `recipes/`。

### Step 3：建立 references 规则库

目标：把跨菜谱规则放到可复用参考文件，减少 `SKILL.md` 膨胀。

执行：

- 新建 `references/defaults.md`，记录默认 2 人份、默认设备、无温度计/有计时器等假设。
- 新建 `references/heat-levels.md`，记录燃气灶、电磁炉和状态判断三套火力描述。
- 新建 `references/unit-conversion.md`，记录 g、ml、个数约重、常见调料换算和无秤替代判断。
- 新建 `references/equipment-profiles.md`，记录燃气灶、电磁炉、铁锅、不粘锅、普通炒锅的参数影响。
- 新建 `references/scaling-rules.md`，记录人份缩放、分批规则和非线性参数。
- 新建 `references/food-safety-rules.md`，记录肉、蛋、海鲜、剩菜、解冻、复热、生熟分开的硬规则。
- 新建 `references/cooking-memory-layer.md`，记录记忆字段、写入规则、读取规则、隐私边界和管理入口。
- 新建 `references/source-notes.md`，记录标准菜谱基准来源 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)、其他外部菜谱来源、许可证检查日期、改写程度和可信度。

验收：

- `SKILL.md` 能明确说明何时读取每个 reference 文件。
- 火力规则覆盖“大火 / 中火 / 小火”的燃气灶、电磁炉、状态判断三列。
- 缩放规则明确区分主料、盐、生抽、糖、油、水、炒制时间、炖煮时间。
- 食品安全规则独立存在；当安全建议和口感建议冲突时，安全优先。
- 记忆层规则区分 Session Memory、User Preference、Recipe-Specific Memory、Learning Log。

### Step 4：编写 10 张核心原理卡

目标：支撑菜谱中的一句话解释和 Learning 模式展开。

执行：

- 按模板创建 10 张原理卡：
  - `principles/protein-denaturation.md`
  - `principles/maillard.md`
  - `principles/starch-gelatinization.md`
  - `principles/velveting.md`
  - `principles/salt-water-migration.md`
  - `principles/seasoning-balance.md`
  - `principles/blanching.md`
  - `principles/oil-temperature-smoke-point.md`
  - `principles/wok-heat.md`
  - `principles/food-safety-temperature.md`
- 每张卡包含 ID、名称、一句话解释、原理描述、关键变量、实际应用、常见误区、适用菜谱、来源。

验收：

- 每张原理卡都能被至少一个首批标杆菜引用。
- 每张原理卡的一句话解释能直接放入完整菜谱的“为什么”字段。
- 原理解释服务操作判断，不写成泛科普文章。
- 食品安全温度卡明确标注无温度计判断可靠性低于温度计。

### Step 5：制作首批 5 道标杆菜

目标：用真实菜谱验证模板和规则是否可用。

执行：

- 按完整解释版模板创建：
  - `recipes/vegetable/fan-qie-chao-dan.md`
  - `recipes/meat/qing-jiao-rou-si.md`
  - `recipes/soup/zheng-dan-geng.md`
  - `recipes/vegetable/qing-chao-xiao-qing-cai.md`
  - `recipes/meat/hong-shao-rou.md`
- 每道菜同时包含完整解释版和厨房执行版。
- 每道菜引用相关原理卡。
- 每道菜包含通用失败诊断和单菜专属失败诊断。
- 每道菜记录来源说明和改写依据；默认先检查 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook) 是否有对应菜谱，再按本 Skill 模板重写、review 和补全。

验收：

- 5 道菜都能在默认 2 人份、普通家庭灶具、无温度计场景下独立执行。
- 每道菜都没有单独出现“适量、少许、一会儿、差不多熟了”等未量化表达；如必须使用感官描述，必须配状态标准。
- 番茄炒蛋覆盖鸡蛋碎、番茄出水、太酸、味道寡淡等专属诊断。
- 青椒肉丝覆盖上浆、滑炒、出水、肉柴、锅温不足等专属诊断。
- 蒸蛋羹覆盖蛋水比例、过滤、气泡、蜂窝、蒸汽控制等专属诊断。
- 清炒小青菜覆盖锅温、盐加入时机、出水、颜色发暗等专属诊断。
- 红烧肉覆盖焯水、煸炒、糖色、炖煮软烂、食品安全和油脂处理等专属诊断。

### Step 6：建立菜谱 review 流程

目标：确保新增菜谱不是“能写出来”，而是“能通过质量门”。

执行：

- 使用 `templates/recipe-review-checklist.md` 对 5 道标杆菜逐项 review。
- 对不通过项直接修改菜谱或对应规则文件。
- 在每道菜末尾记录 review 状态、review 日期和未解决风险。

验收：

- 每道菜都通过执行完整性、参数可靠性、原理匹配、安全检查、厨房友好性五项检查。
- 不合格菜谱不能标记为标杆菜。
- review 发现的问题不沉默跳过，必须在菜谱或 reference 中有对应修正。

### Step 7：实现厨房执行版和打印样式

目标：把“实时陪做”需求转成可打印、可扫读的厨房文档。

执行：

- 新建 `assets/print.css`，定义 A4、14pt 以上正文、高对比度、宽行距、醒目步骤编号。
- 新建 `scripts/render_recipe_pdf.py`，把指定 Markdown 菜谱渲染为可打印 PDF。
- 先支持单道菜 PDF，不做自动打印机调用。
- 输出文件放入 `output/pdf/`，中间文件放入 `tmp/pdfs/`。

验收：

- 至少能从 1 道标杆菜生成 Markdown 厨房版和 PDF。
- PDF 单道菜控制在 1-2 页 A4。
- 厨房版顶部食材清单可作为简版购物清单使用。
- PDF 不出现文字裁切、表格溢出、低对比度或步骤拥挤。
- 不调用 `lp`、`lpr` 或系统打印机。

### Step 8：落地最小 Cooking Memory Layer

目标：先定义可用记忆协议，不急于做复杂存储系统。

执行：

- 在 `references/cooking-memory-layer.md` 中固化 MVP profile 字段。
- 在 `SKILL.md` 中写入生成菜谱前的记忆读取规则。
- 在 `SKILL.md` 中写入本次覆盖、长期偏好、敏感信息确认和删除入口规则。
- 在首批菜谱中示例说明“已按哪些偏好适配”。

验收：

- MVP 字段包含 defaults、taste、equipment、dislikes。
- 能区分“今天 4 人份”和“以后默认 4 人份”。
- 设备、口味、份量偏好可自动建议记忆；健康、过敏、宗教或长期忌口必须确认后记忆。
- 输出菜谱时必须说明使用了哪些偏好。
- 低置信度记忆只能作为建议，不强制应用。

### Step 9：扩展到 V1 菜谱集

目标：在模板稳定后扩展到 20-30 道菜，不提前堆内容。

执行：

- 先补齐中餐家常菜：鸡蛋类、肉丝类、蔬菜类、炖煮类、蒸菜类、凉拌类、简单汤类。
- 再补少量快手西餐：番茄肉酱意面、煎牛排、沙拉油醋汁。
- 每新增一道菜都复用模板、引用原理卡、通过 review 清单。

验收：

- V1 至少 20 道菜，每道菜都有完整解释版和厨房执行版。
- 每道菜至少引用 1 张原理卡。
- 涉及肉、蛋、海鲜、剩菜的菜谱必须触发食品安全规则。
- 菜谱来源、改写程度和许可证检查记录进入 `references/source-notes.md`。

### Step 10：实际厨房验证

目标：用真实做菜结果校正文档，不只做文本自洽。

执行：

- 至少实际做 3-5 道标杆菜。
- 记录实际克数、时间、火力、状态判断、失败点和修正建议。
- 根据验证结果修订菜谱参数、失败诊断和 reference 规则。

说明：本步骤作为后续厨房校准流程保留，不作为第一轮完成验收标准。

## 4. 总体验收标准

结构验收：

- 根目录存在 `SKILL.md`，并有 `agents/`、`templates/`、`principles/`、`recipes/`、`references/`。
- 长规则不堆在 `SKILL.md`，而是按主题拆分到 references。
- 菜谱、原理、模板、规则、脚本职责清楚，没有相互复制大段内容。

功能验收：

- 用户只输入菜名时，Skill 可按默认 2 人份生成完整解释版和厨房执行版。
- 用户追问原理时，Skill 可进入对应原理卡。
- 用户反馈失败时，Skill 可给出可能原因和下次调整方案。
- 用户提供人数、设备、锅具、电子秤、温度计时，Skill 可调整用量和步骤。

内容验收：

- 首批 5 道标杆菜完整可执行。
- 10 张核心原理卡可复用且互相不重复。
- 所有菜谱避免无量化的模糊表达。
- 所有步骤都有时间、火力、目标状态和失败信号。

安全验收：

- 食品安全规则独立维护。
- 涉及安全边界时，菜谱中必须出现明确提示。
- 无温度计的感官判断必须提示可靠性限制。
- 口感建议不得覆盖最低安全要求。

厨房友好性验收：

- 厨房执行版每步短、编号清楚、关键计时点明确。
- 单道菜厨房版可控制在 1-2 页 A4。
- 顶部食材清单可直接作为购物清单。
- 打印版不依赖实时对话、手机通知或内置计时器。

记忆层验收：

- 能表达长期偏好、本次覆盖、单菜反馈和学习日志的边界。
- 敏感长期记忆写入前需要确认。
- 输出时说明使用了哪些偏好。
- 用户可以查看、修改、删除或临时禁用偏好。

## 5. 暂不做事项

以下内容不进入第一轮实现：

- 独立实时陪做 App。
- 系统级计时器或跨平台通知。
- 自动检测或调用本地打印机。
- 多家庭成员复杂偏好模型。
- 医学诊断、治疗建议或营养处方。
- 大规模导入外部菜谱库。

## 6. 执行顺序建议

第一批 commit：

- `SKILL.md`
- `agents/openai.yaml`
- `templates/`
- `references/defaults.md`

第二批 commit：

- `references/heat-levels.md`
- `references/unit-conversion.md`
- `references/equipment-profiles.md`
- `references/scaling-rules.md`
- `references/food-safety-rules.md`

第三批 commit：

- `principles/` 10 张核心原理卡

第四批 commit：

- `recipes/` 5 道标杆菜（按菜品类型分目录）
- 菜谱 review 记录

第五批 commit：

- `assets/print.css`
- `scripts/render_recipe_pdf.py`
- 1 道菜 PDF 输出验证

第六批 commit：

- `references/cooking-memory-layer.md`
- `SKILL.md` 记忆层读取和写入规则

## 7. 参考来源

- [OpenAI `openai/skills`](https://github.com/openai/skills)：官方 Skills Catalog，说明 Skill 是由 instructions、scripts 和 resources 组成的可发现能力包。
- [OpenAI curated `playwright` Skill](https://github.com/openai/skills/tree/main/skills/.curated/playwright)：示例目录包含 `SKILL.md`、`agents/`、`assets/`、`references/`、`scripts/`。
- [OpenAI curated `pdf` Skill](https://github.com/openai/skills/tree/main/skills/.curated/pdf)：示例目录只保留任务需要的 `SKILL.md`、`agents/`、`assets/`，说明 optional 目录不必强行创建。
- [OpenAI `skill-creator` Skill](https://github.com/openai/skills/tree/main/skills/.system/skill-creator)：明确 `SKILL.md` 必需，`agents/openai.yaml` 推荐，`scripts/`、`references/`、`assets/` 按需使用，并要求通过渐进披露控制上下文体积。
- [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)：本 Skill 标准菜谱的基础参考来源，仅作为单菜谱原料、计算和基础步骤参考，不作为整库 fork 来源。
