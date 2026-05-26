# Cooking Memory Layer

记忆层的目标是减少重复适配，不是替用户保存敏感信息。低置信度记忆只能作为建议。

## MVP Profile 字段

```yaml
defaults:
  servings: 2
  preferred_output: full-plus-kitchen
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

## 初始化规则

缺少用户 profile 时，不应阻塞当前做菜、诊断、原理解释、一餐规划或菜谱导入任务。

- 默认按 `references/defaults.md` 执行当前请求。
- 输出末尾说明本次使用默认值，而不是已记忆偏好。
- 可以轻提示用户说“初始化我的做菜偏好”来记录设备、口味、忌口和家庭成员。
- 只有用户明确要求初始化或更新偏好时，才进入 Memory Init / Update 流程。
- 初始化流程应优先记录会改变菜谱参数的信息：默认人数、灶具、锅具、是否有秤、是否有温度计、咸淡油辣偏好、忌口和家庭成员。
- 健康、过敏、宗教、孕期、儿童、疾病和长期忌口等敏感信息，必须在写入长期记忆前得到明确确认。

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

- 用户反馈先写入 `feedback_history` 或 `references/feedback-log.example.yaml` 所示结构。
- 单次反馈默认置信度低，只能作为下次同菜谱的建议。
- 用户明确确认“以后都这样调整”后，才写入长期 `recipe_preferences`。
- 健康、过敏、孕期、儿童、长期忌口等敏感信息必须确认后写入。

合并细则见 `references/memory-merge-rules.md`。

## 敏感边界

健康、过敏、宗教、孕期、疾病、儿童饮食、长期忌口等信息必须确认后才能作为长期记忆。确认前只能作为当前请求约束。

## 输出规则

- 生成菜谱前检查是否存在 profile；存在时读取与菜名、设备、份量、口味、历史失败相关的记忆。
- profile 不存在时继续使用默认值，不先进入问卷。
- 如果用户指定家庭成员，只读取这些成员和当前菜谱相关的记忆。
- 输出末尾说明本次使用了哪些偏好或默认值。
- 区分“本次覆盖”和“以后默认”。
- 提供查看、修改、删除、临时禁用偏好的入口。
