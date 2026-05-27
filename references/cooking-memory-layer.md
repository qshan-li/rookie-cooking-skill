# Cooking Memory Layer

记忆层的目标是减少重复适配，不是替用户保存敏感信息。低置信度记忆只能作为建议。

## 本地存储

真实用户数据默认放在 skill 仓库外：

```text
~/.rookie-cooking/
  profile.yaml
  feedback.jsonl
  memory-candidates.jsonl
```

可以用 `ROOKIE_COOKING_HOME` 覆盖根目录，便于测试、备份或迁移。仓库内只保留 schema、示例和规则，不提交真实用户偏好。

所有持久化读写都应通过标准库脚本完成：

```bash
python scripts/cooking_memory.py read --dish tomato-egg --diners self
python scripts/cooking_memory.py init-profile
python scripts/cooking_memory.py update-profile --set defaults.servings=4
python scripts/cooking_memory.py add-feedback --recipe tomato-egg --issue too_salty
python scripts/cooking_memory.py list-candidates
python scripts/cooking_memory.py confirm-candidate <candidate_id>
python scripts/cooking_memory.py reject-candidate <candidate_id>
python scripts/cooking_memory.py view
python scripts/cooking_memory.py delete <path-or-id>
python scripts/cooking_memory.py ignore-once --dish tomato-egg
```

Skill 不应在 prompt 中直接散写 YAML 或 JSONL 文件。

## MVP Profile 字段

```yaml
defaults:
  servings: 2
taste:
  salt_level: normal
  sweetness: normal
  spice_level: mild
equipment:
  stove: unknown
  pan: ordinary-wok
  has_scale: true
  has_thermometer: false
dislikes: []
household_members: []
recipe_preferences: {}
feedback_history: []
```

完整示例见 `references/user-profile.example.yaml`。

## 记忆类型

| 类型 | 含义 | 示例 | 写入规则 |
| --- | --- | --- | --- |
| Session Memory | 只对本次对话有效 | 今天 4 人份 | 不写入长期偏好。 |
| User Preference | 长期偏好 | 以后默认 4 人份、少辣 | 明确表达长期意图后写入。 |
| Recipe-Specific Memory | 单菜反馈 | 青椒肉丝上次肉柴 | 下次生成该菜时优先读取。 |
| Learning Log | 学习记录 | 已解释过美拉德反应 | 只用于减少重复解释。 |

输出模式不是长期记忆字段。不要保存“默认完整版”“默认厨房执行版”“默认生成 PDF”“默认打印”等输出形态或交付方式；Recipe Generation 每次缺少输出模式时，只要运行时支持交互选择工具，都必须重新提供默认 / 厨房执行版选择。长期记忆只能影响人数、设备、口味、忌口、家庭成员和已确认的单菜参数调整。

## 初始化规则

缺少用户 profile 时，不应阻塞当前做菜、诊断、原理解释、一餐规划或菜谱导入任务。

- 默认按 `references/defaults.md` 执行当前请求。
- Recipe Generation 中 profile 不存在且交互选择工具可用时，生成前必须提供一次可选的本次适配入口，但默认选项必须是继续使用默认值。
- 本次适配只收集当前菜谱需要的人数、设备、口味和忌口；除非用户选择初始化长期偏好，否则不写入长期记忆。
- 输出末尾说明本次使用默认值，而不是已记忆偏好。
- 可以轻提示用户说“初始化我的做菜偏好”来记录设备、口味、忌口和家庭成员。
- 只有用户明确要求初始化或更新偏好时，才进入 Memory Init / Update 流程。
- 初始化流程应优先记录会改变菜谱参数的信息：默认人数、灶具、锅具、是否有秤、是否有温度计、咸淡油辣偏好、忌口和家庭成员。
- 健康、过敏、宗教、孕期、儿童、疾病和长期忌口等敏感信息，必须在写入长期记忆前得到明确确认。

## 写入预览

Memory Init / Update 必须在任何长期写入前展示写入预览，而不是直接调用写命令。

```text
Will write:
- defaults.servings = 4
- equipment.stove_type = induction

Will not write:
- tonight_no_cilantro, session-only
```

用户必须选择：

- Confirm write
- Edit values
- Cancel

当前 CLI 可以执行写入，但不一定提供专门的 dry-run 模式。第一版可以由 skill 根据解析出的用户意图生成预览；如果跨 agent 测试显示预览不稳定，再给 `scripts/cooking_memory.py` 增加 dry-run 或 preview 命令。

## 家庭成员

家庭成员用于“给谁吃”的适配，不用于建立复杂身份系统。

每个成员至少包含：

- `member_id`
- `display_name`
- 口味偏好：咸淡、油量、辣度
- 忌口和不喜欢的食材
- 需要确认后才能长期记录的敏感约束：过敏、孕期、儿童、疾病、宗教或伦理饮食限制

多人共同进餐时，忌口取并集，口味取保守交集。安全和敏感约束优先于口感。

## 历史反馈与自动学习

自动学习只能产生建议，不能静默修改长期记忆。

- 用户反馈先写入 `feedback.jsonl`，结构与 `references/feedback-log.example.yaml` 一致。
- 单次反馈默认置信度低，只能作为下次同菜谱的建议。
- Troubleshooting 可以读取相关记忆来排序原因和调整下次参数，但不能把一次失败静默写成长期偏好。
- 自动学习产生的长期记忆建议写入 `memory-candidates.jsonl`，状态为 `pending`。
- 用户明确确认“以后都这样调整”或确认某个 candidate 后，才写入长期 `recipe_preferences`。
- 健康、过敏、孕期、儿童、长期忌口等敏感信息必须确认后写入。
- Troubleshooting 结束后只能提供三类记忆动作：Record feedback only、Save durable preference、Do not record。没有确认时只能写 pending feedback 或 candidate。

合并细则见 `references/memory-merge-rules.md`。

## 敏感边界

健康、过敏、宗教、孕期、疾病、儿童饮食、长期忌口等信息必须确认后才能作为长期记忆。确认前只能作为当前请求约束。

## 输出规则

- 生成菜谱前用 `scripts/cooking_memory.py read` 检查是否存在 profile；存在时读取与菜名、设备、份量、口味、历史失败相关的记忆。
- profile 不存在时不强制进入问卷；如果运行时支持交互选择，生成前必须提供可选本次适配入口，默认继续使用默认值。
- 如果用户指定家庭成员，只读取这些成员和当前菜谱相关的记忆。
- 输出末尾说明本次使用了哪些偏好或默认值。
- 使用 `pending-confirmation` 或低置信度反馈时，必须标注为“建议”，不能标注为“默认”。
- 区分“本次覆盖”和“以后默认”。
- 提供查看、修改、删除、临时禁用偏好的入口。
