# {{dish_name}} 失败诊断

## 已使用上下文

- 观察到的事实：{{observed_facts}}
- 本次假设：{{assumptions_or_none}}
- 相关记忆：{{relevant_memory_or_none}}

## 安全分诊

- 风险食材 / 场景：{{safety_risk_context}}
- 是否需要先丢弃或充分复热：{{discard_or_reheat_rule}}
- 仍缺少的安全事实：{{missing_safety_fact_or_none}}
- 判断优先级：安全结论先于口感补救。

## 通用诊断

| 现象 | issue_label | 优先排查 | 可能原因 | 立即补救 | 下次调整 |
| --- | --- | --- | --- | --- | --- |
| 太咸 | `too_salty` | 调味量和收汁程度 | {{cause}} | {{rescue}} | {{next_adjustment}} |
| 太淡 | `too_bland` | 盐分、鲜味、酸甜平衡 | {{cause}} | {{rescue}} | {{next_adjustment}} |
| 出水 | `too_watery` | 食材含水、锅温、盐加入时机 | {{cause}} | {{rescue}} | {{next_adjustment}} |
| 口感老/柴 | `meat_dry` | 加热时间、切法、预处理 | {{cause}} | {{rescue}} | {{next_adjustment}} |
| 糊底 | `burnt` | 油量、锅温、翻动频率、糖分 | {{cause}} | {{rescue}} | {{next_adjustment}} |

## 单菜专属诊断

| 现象 | 可能原因 | 状态证据 | 下次调整 |
| --- | --- | --- | --- |
| {{dish_specific_symptom}} | {{likely_cause}} | {{evidence}} | {{next_adjustment}} |

## 安全判断

- {{safety_related_symptom}}：{{discard_or_reheat_rule}}

## 反馈归档

- 归一化 issue label：{{issue_label}}
- 可选动作：Record feedback only / Save durable preference / Do not record
- 写入前确认：{{confirmation_needed}}

## 记忆处理

- 本次反馈记录：{{feedback_record_plan}}
- 长期记忆：{{memory_candidate_or_confirmation_needed}}
