# 厨房实测验证记录规则

真实厨房验证用于校正文档参数，不用于装饰菜谱状态。没有实际做菜记录时，菜谱只能标记为 `draft` 或 `passed`，不能标记为 `validated`。

## 记录位置

- 每道菜的实测摘要写在对应菜谱的 `Review` 段落下。
- 详细记录可追加在同一菜谱末尾的 `## 厨房实测记录`。
- 修改了通用规则时，同步更新相关 `references/` 文件。

## 单次实测记录模板

```markdown
### 实测 {{date}}

- 操作者：{{cook_id_or_self}}
- 环境：{{stove}}, {{pan}}, {{thermometer_or_none}}
- 实际份量：{{servings}}
- 实际克数：{{ingredient_weights}}
- 实际时间：{{step_times}}
- 火力记录：{{heat_notes}}
- 状态判断：{{state_checks}}
- 失败点：{{failure_points_or_none}}
- 修正建议：{{recipe_or_reference_changes}}
- 结论：`keep-passed` / `revise-needed` / `validated-candidate`
```

## 标记为 validated 的条件

- 至少 1 次实测记录包含实际克数、时间、火力、状态判断和结论。
- 如果目标是满足执行计划 Step 10，至少 3 道标杆菜需要真实实测记录。
- 实测发现的偏差必须落实到菜谱或 reference，不能只写在记录里。
- 厨房执行版必须能在做饭时扫读，不依赖持续对话。

可用 `scripts/check_skill_completeness.py --require-benchmark-validations 3` 检查 Step 10 是否达到最低实测门槛。该命令在没有 3 道标杆菜 `validated` 记录时必须失败。

## 不允许

- 不允许根据文本自查标记 `validated`。
- 不允许把“看起来合理”当成实测。
- 不允许删除失败记录；失败记录应转成诊断或参数修正。
