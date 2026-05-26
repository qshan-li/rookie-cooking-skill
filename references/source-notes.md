# 来源记录

本 Skill 的标准菜谱基础参考来源为 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)。仅参考单菜谱的原料、计算和基础操作，不 fork 整个仓库；每道菜都按本 Skill 模板重写，补充状态判断、失败诊断、替代方案、食品安全和原理说明。

## 全局来源

| 来源 | 用途 | 许可证检查日期 | 说明 |
| --- | --- | --- | --- |
| Anduin2017/HowToCook | 家常菜基础用量和步骤参考 | 2026-05-26 | 单菜谱参考，生成内容需重写并记录改写程度。 |

## 单菜记录模板

| 菜名 | 上游 URL | 检查日期 | 许可证依据 | 改写程度 | 本 Skill 补充 | 可信度 |
| --- | --- | --- | --- | --- | --- | --- |
| 番茄炒蛋 | https://github.com/Anduin2017/HowToCook/blob/master/dishes/vegetable_dish/西红柿炒鸡蛋.md | 2026-05-26 | Unlicense，仓库 `LICENSE` | 重写 | 状态判断、失败诊断、厨房版、食品安全、原理引用 | 高 |
| 青椒肉丝 | HowToCook 未找到精确同名单菜；参考 https://github.com/Anduin2017/HowToCook/blob/master/dishes/meat_dish/香干肉丝.md、https://github.com/Anduin2017/HowToCook/blob/master/dishes/meat_dish/青椒土豆炒肉/青椒土豆炒肉.md、https://github.com/Anduin2017/HowToCook/blob/master/dishes/meat_dish/辣椒炒肉.md | 2026-05-26 | Unlicense，仓库 `LICENSE` | 原创重写，相关参考 | 上浆、滑炒、锅温、青椒出水诊断、食品安全 | 中 |
| 蒸蛋羹 | https://github.com/Anduin2017/HowToCook/blob/master/dishes/vegetable_dish/鸡蛋羹/鸡蛋羹.md | 2026-05-26 | Unlicense，仓库 `LICENSE` | 重写 | 蛋水比例、过滤、蒸汽控制、蜂窝诊断、食品安全 | 高 |
| 清炒小青菜 | https://github.com/Anduin2017/HowToCook/blob/master/dishes/vegetable_dish/炒青菜.md | 2026-05-26 | Unlicense，仓库 `LICENSE` | 重写 | 少水快炒、锅温、盐时机、出水诊断、厨房版 | 高 |
| 红烧肉 | https://github.com/Anduin2017/HowToCook/blob/master/dishes/meat_dish/红烧肉/简易红烧肉.md | 2026-05-26 | Unlicense，仓库 `LICENSE` | 重写 | 焯水、煸炒、糖色、软烂判断、油脂处理、食品安全 | 高 |

记录要求：

- 每新增一道参考或改写菜谱，都必须补一行。
- 如果 HowToCook 没有对应菜谱，记录实际参考来源或标记为原创整理。
- 不复制上游长段文字；只保留事实性参数和独立重写后的执行说明。
