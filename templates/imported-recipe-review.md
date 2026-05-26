# {{dish_name}} 导入改写记录

导入日期：{{import_date}}  
原始来源：{{source_description_or_url}}  
导入状态：`draft`  
目标文件：{{target_recipe_path}}

## 原始菜谱要点

- 菜名：{{source_dish_name}}
- 原始份量：{{source_servings_or_unknown}}
- 主要食材：{{source_main_ingredients}}
- 关键步骤：{{source_key_steps}}
- 模糊点：{{ambiguous_terms_or_missing_parameters}}

## 改写要求

- [ ] 转成 `templates/recipe-full.md` 和 `templates/recipe-kitchen.md` 结构。
- [ ] 补齐 g、ml、时间、火力、目标状态和失败信号。
- [ ] 补齐食品安全提示。
- [ ] 补齐至少 1 个原理引用。
- [ ] 补齐失败诊断和替代方案。
- [ ] 写入 `## 来源说明`，说明来源、许可证或用户提供上下文、改写程度。
- [ ] Review 状态保持 `draft`，直到人工 review 后再改为 `passed`。

## Review 决策

- 是否可进入菜谱库：{{yes_no_or_pending}}
- 主要风险：{{open_risks}}
- 下次动作：{{next_action}}
