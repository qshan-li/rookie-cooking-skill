# {{meal_name}} 一餐计划

份量：{{servings}}  
用餐对象：{{household_members_or_default}}  
总时长：{{total_time}}  
主要设备：{{equipment_summary}}  
目标：{{meal_goal}}

## 菜单

| 菜品 | 类型 | 份量 | 预计时间 | 主要设备 | 风险点 |
| --- | --- | --- | --- | --- | --- |
| {{dish_name}} | {{dish_type}} | {{servings}} | {{time}} | {{equipment}} | {{risk}} |

## 购物清单

清单模式：{{shopping_list_mode}}

### 主料

| 食材 | 总量 | 覆盖菜品 | 购买/处理提示 |
| --- | ---: | --- | --- |
| {{ingredient}} | {{total_amount}} | {{dishes}} | {{shopping_note}} |

### 调料和辅料

| 项目 | 总量 | 覆盖菜品 | 可替代 |
| --- | ---: | --- | --- |
| {{seasoning}} | {{total_amount}} | {{dishes}} | {{substitution}} |

## 厨房排程

| 时间点 | 动作 | 设备 | 检查点 |
| --- | --- | --- | --- |
| T-{{minutes}} | {{action}} | {{equipment}} | {{check}} |

## 并行规则

- 先做需要浸泡、腌制、焯水、炖煮、烤制或冷却的步骤。
- 同一时间只安排一个高风险动作，例如热油、炸制、快速爆炒、处理生肉生海鲜。
- 生熟砧板和刀具分开；处理完生肉、禽类、海鲜后再处理即食食材。
- 如果设备冲突，优先安排长时间等待菜，快炒菜最后出锅。

## 本次使用的偏好 / 假设

- 人数：{{servings_or_profile_servings}}
- 设备：{{applied_equipment}}
- 口味：{{applied_taste}}
- 家庭成员：{{applied_household_members_or_none}}
- 历史反馈：{{applied_feedback_or_none}}
