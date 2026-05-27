# Recipe Import Rules

用户导入菜谱时，目标是把原始文本改写成本项目的可执行厨房文档，而不是保留原菜谱格式。

## 触发场景

- 用户粘贴菜谱文本。
- 用户提供外部菜谱链接或截图内容摘要。
- 用户要求"把这个菜谱整理成新手版"。
- 用户自创菜谱，需要进入本项目结构。

## 状态规则

用户导入菜谱有三个状态，含义如下：

- `draft`：刚导入，尚未完成 review。可用于当前对话，但不能作为标准菜谱。
- `passed`：review 通过，可作为用户的个人标准菜谱使用。
- `validated`：用户实际照做并认可结果。

状态转换触发条件：

- `draft → passed`：agent 自动跑 review checklist（见下方"Review 通过标准"），用户确认后改写。
- `passed → validated`：用户主动反馈"我做了，没问题"或明确要求标记为已验证。不需要完整实测记录，用户一句话确认即可。
- 不允许跳过 `draft` 直接标记为 `passed`。

## 存储路径

用户导入的菜谱存储在 `~/.rookie-cooking/` 下，不进入 skill 的 `recipes/` 目录：

```text
~/.rookie-cooking/
  drafts/          # draft 状态的用户菜谱
  recipes/         # passed / validated 状态的用户菜谱
```

文件命名规则：和 `recipes/` 一致，使用拼音 kebab-case，例如 `ma-po-dou-fu.md`。

agent 发现用户菜谱的方式：直接扫描目录，不维护索引文件。

## Frontmatter 要求

用户导入的菜谱必须包含以下 frontmatter 字段：

```yaml
---
name: ma-po-dou-fu
status: draft          # draft / passed / validated
source: user-import    # user-import / howtocook / original
source_description: "用户粘贴的家传做法"
import_date: 2026-05-27
---
```

- `status`：必须，agent 按这个判断菜谱状态。
- `source`：必须，区分来源类型。
- `source_description`：必须，记录具体来源。
- `import_date`：可选但建议保留。

## 导入意图

Recipe Import 先区分持久化目标，再区分输出形态，不要把两者混成一个选择。

持久化目标：

- 本次对话改写：默认选项，不保存到 `~/.rookie-cooking/drafts/`，状态仍标记为 `draft`。
- 保存为 draft 菜谱：保存到 `~/.rookie-cooking/drafts/`，需要来源说明，状态为 `draft`。
- Review existing draft：扫描 `~/.rookie-cooking/drafts/`，列出已有 draft，按 review checklist 审查。

输出形态：

- 完整解释版：默认输出。
- 厨房执行版：用户明确要求厨房版、PDF、打印或保存厨房执行材料时输出。
- PDF / direct print：只能基于厨房执行版生成，不能把完整解释版直接打印成厨房版。

## 改写流程

1. 识别原始菜名、份量、食材、步骤和来源。
2. 标出模糊词和缺失参数，例如"适量""少许""炒熟""收汁"。
3. 用 `references/defaults.md`、`references/heat-levels.md`、`references/unit-conversion.md` 和 `references/scaling-rules.md` 补默认值和区间。
4. 用 `templates/recipe-full.md` 和 `templates/recipe-kitchen.md` 重写。
5. 写 `## 来源说明`，标明用户提供、外部链接、原创整理或其他来源。
6. 填写 frontmatter（`status`、`source`、`source_description`、`import_date`）。

## Review 通过标准

agent 生成菜谱后自动跑一遍 `templates/recipe-review-checklist.md`。

必须全部满足：

- 安全检查 4 项全通过。
- 参数可靠性：主料、盐、酱油、糖、油有精确量或明确区间。
- 每个步骤有操作、时间、火力、目标状态。

允许 1-2 项未通过（标注 TODO）：

- 厨房友好性中的"可离线执行"。
- 原理引用（可以暂时缺，但必须标注 TODO）。

review 完成后：

- 未通过项列出，让用户决定是否接受 draft 状态或当场补全。
- 用户确认后，agent 改写 frontmatter `status: passed`。

## Draft 提升为 Passed

用户说"这个菜谱可以了，帮我保存"时，agent 自动执行：

1. 改 frontmatter `status: draft → passed`。
2. 移动文件：`~/.rookie-cooking/drafts/<name>.md → ~/.rookie-cooking/recipes/<name>.md`。
3. 确认："已保存到 ~/.rookie-cooking/recipes/，状态改为 passed"。

## 重名处理

导入时：agent 扫描 skill 的 `recipes/` 和 `~/.rookie-cooking/recipes/`，发现重名则提示用户"已有同名菜谱，是否仍要导入？"。

使用时：如果用户有自己的版本，优先用用户的。两个版本不合并，各自独立。

## 来源记录

用户导入的菜谱保存为 draft 后，在 `references/source-notes.md` 加一行来源记录，和 HowToCook 菜谱同表：

| 菜名 | 来源 | 检查日期 | 改写程度 | 可信度 |
| --- | --- | --- | --- | --- |
| 麻婆豆腐 | 用户导入：家传做法 | 2026-05-27 | 改写 | 中 |

## 不允许

- 不允许把用户导入菜谱直接标记为 `passed`。
- 不允许保留未经解释的模糊量词。
- 不允许复制长段外部菜谱正文作为最终菜谱。
- 不允许为了补参数伪造精确值；必须写成默认值、区间和状态判断。
- 不允许忽略食品安全风险。
- 不允许将用户导入的菜谱放入 skill 的 `recipes/` 目录。
