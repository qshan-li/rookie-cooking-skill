# Recipe Import Rules

用户导入菜谱时，目标是把原始文本改写成本项目的可执行厨房文档，而不是保留原菜谱格式。

## 触发场景

- 用户粘贴菜谱文本。
- 用户提供外部菜谱链接或截图内容摘要。
- 用户要求“把这个菜谱整理成新手版”。
- 用户自创菜谱，需要进入本项目结构。

## 状态规则

- 用户导入或新建菜谱初始状态必须是 `draft`。
- `draft` 菜谱可以用于当前对话，但不能作为高可信标准菜谱。
- 通过 `templates/recipe-review-checklist.md` 后，才能改为 `passed`。
- 用户实际执行并认可且有实测记录后，才能改为 `validated`。

## 导入意图

Recipe Import 先区分持久化目标，再区分输出形态，不要把两者混成一个选择。

持久化目标：

- 本次对话改写：默认选项，不保存到 `recipes/`，导入状态仍标记为 `draft`。
- 保存为 draft 菜谱：需要来源说明和目标路径，不能标记为 `passed`。
- Review existing draft：只审查已有 draft，按 review checklist 输出问题和下一步。

输出形态：

- 完整解释版：默认输出。
- 厨房执行版：用户明确要求厨房版、PDF、打印或保存厨房执行材料时输出。
- PDF / direct print：只能基于厨房执行版生成，不能把完整解释版直接打印成厨房版。

## 改写流程

1. 识别原始菜名、份量、食材、步骤和来源。
2. 标出模糊词和缺失参数，例如“适量”“少许”“炒熟”“收汁”。
3. 用 `references/defaults.md`、`references/heat-levels.md`、`references/unit-conversion.md` 和 `references/scaling-rules.md` 补默认值和区间。
4. 用 `templates/recipe-full.md` 和 `templates/recipe-kitchen.md` 重写。
5. 用 `templates/imported-recipe-review.md` 记录导入依据和风险。
6. 写 `## 来源说明`，标明用户提供、外部链接、原创整理或其他来源。

## 不允许

- 不允许把用户导入菜谱直接标记为 `passed`。
- 不允许保留未经解释的模糊量词。
- 不允许复制长段外部菜谱正文作为最终菜谱。
- 不允许为了补参数伪造精确值；必须写成默认值、区间和状态判断。
- 不允许忽略食品安全风险。
