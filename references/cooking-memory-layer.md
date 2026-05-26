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
```

## 记忆类型

| 类型 | 含义 | 示例 | 写入规则 |
| --- | --- | --- | --- |
| Session Memory | 只对本次对话有效 | 今天 4 人份 | 不写入长期偏好。 |
| User Preference | 长期偏好 | 以后默认 4 人份、少辣 | 明确表达长期意图后写入。 |
| Recipe-Specific Memory | 单菜反馈 | 青椒肉丝上次肉柴 | 下次生成该菜时优先读取。 |
| Learning Log | 学习记录 | 已解释过美拉德反应 | 只用于减少重复解释。 |

## 敏感边界

健康、过敏、宗教、孕期、疾病、儿童饮食、长期忌口等信息必须确认后才能作为长期记忆。确认前只能作为当前请求约束。

## 输出规则

- 生成菜谱前读取与菜名、设备、份量、口味、历史失败相关的记忆。
- 输出末尾说明本次使用了哪些偏好或默认值。
- 区分“本次覆盖”和“以后默认”。
- 提供查看、修改、删除、临时禁用偏好的入口。
