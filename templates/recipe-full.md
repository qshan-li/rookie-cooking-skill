# {{dish_name}} 完整解释版

## 基本信息

- 份量：{{servings}}
- 总时间：{{total_time}}
- 主动操作时间：{{active_time}}
- 难度：{{difficulty}}
- 热量估算：{{calories_estimate}}
- 设备：{{equipment}}
- 成品目标：{{target_result}}
- 已使用偏好 / 假设：
  - 人数：{{servings_or_profile_servings}}
  - 设备：{{applied_equipment}}
  - 口味：{{applied_taste}}
  - 家庭成员：{{applied_household_members_or_none}}
  - 历史反馈：{{applied_feedback_or_none}}

## 原料和工具

| 项目 | 精确量 | 无秤判断 | 作用 | 可替代 |
| --- | ---: | --- | --- | --- |
| {{ingredient}} | {{amount}} | {{no_scale_check}} | {{purpose}} | {{substitution}} |

## 份量缩放

| 份量 | 主料 | 盐 | 生抽/酱油 | 糖 | 油 | 水/汤 | 时间调整 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 人 | {{one_serving}} | {{salt_1}} | {{soy_1}} | {{sugar_1}} | {{oil_1}} | {{water_1}} | {{time_1}} |
| 2 人 | {{two_servings}} | {{salt_2}} | {{soy_2}} | {{sugar_2}} | {{oil_2}} | {{water_2}} | {{time_2}} |
| 4 人 | {{four_servings}} | {{salt_4}} | {{soy_4}} | {{sugar_4}} | {{oil_4}} | {{water_4}} | {{time_4}} |

## 预处理

| 步骤 | 操作 | 时间 | 目标状态 | 失败信号 | 为什么 |
| --- | --- | --- | --- | --- | --- |
| 1 | {{prep_action}} | {{prep_time}} | {{prep_target}} | {{prep_failure_signal}} | {{prep_reason}} |

## 操作步骤

| 步骤 | 操作 | 时间 | 火力 | 目标状态 | 失败信号 | 为什么 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | {{action}} | {{time}} | {{heat}} | {{target_state}} | {{failure_signal}} | {{reason}} |

## 关键判断点

- {{checkpoint_name}}：{{measurable_or_visible_standard}}

## 失败诊断

| 现象 | 可能原因 | 本次是否可补救 | 下次调整 |
| --- | --- | --- | --- |
| {{symptom}} | {{likely_cause}} | {{rescue_action}} | {{next_adjustment}} |

## 替代方案

- 食材替代：{{ingredient_substitution}}
- 工具替代：{{tool_substitution}}
- 设备调整：{{equipment_adjustment}}

## 食品安全

- {{safety_rule}}
- 无温度计判断：{{sensory_safety_check}}。可靠性低于温度计，风险较高时以延长加热或温度计为准。

## 相关原理

- `{{principle_id}}`：{{one_sentence_principle}}
