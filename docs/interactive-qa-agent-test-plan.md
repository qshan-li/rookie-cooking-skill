# Interactive QA Agent Test Plan

状态：测试计划  
适用范围：Codex、Claude Code、Gemini CLI、Hermes Agent；OpenClaw 可作为 ACP 编排器补测  
目标日期：2026-05-26

## 1. 测试目标

验证 `rookie-cooking` 在不同 agent 终端中的全功能 flow 契约：Recipe Generation、Troubleshooting、Learning、Meal Planning、Recipe Import、Memory Init / Update。测试以自动化 harness 为主，人工观察为辅：

- 用户没有指定输出模式，且终端支持交互选择工具时，先让用户在默认和厨房执行版之间选择。
- 用户已经指定输出模式时，不再重复询问。
- 当前终端没有交互选择能力时，不阻塞生成，直接使用默认输出模式。
- Troubleshooting、Learning、Meal Planning、Recipe Import、Memory Init / Update 不误触发 Recipe Generation 的输出模式 QA。
- 根目录 `SKILL.md` 只代表仓库内容，不等于 agent 已安装或已发现 skill。

通过标准不是三个 agent 的 UI 完全一致，而是行为语义一致。

## 2. 静态校验

在仓库根目录先跑静态校验：

```bash
python -m unittest discover -s tests
python scripts/check_skill_completeness.py
```

## 3. Skill 安装 / 发现检查

先运行：

```bash
python scripts/run_agent_skill_qa.py check-install
```

该命令只检查本机常见 skill 目录，不调用模型。

预期结论：

- Claude Code project skill：`.claude/skills/rookie-cooking/SKILL.md`。
- Claude Code personal skill：`~/.claude/skills/rookie-cooking/SKILL.md`。
- Gemini CLI：优先用 `gemini skills link <repo-path> --scope workspace --consent` 链接，再用 `gemini skills list` 确认。
- Hermes Agent：通过 `hermes skills list` 确认；未安装时按 Hermes skill 管理流程安装或启用。
- Codex：不能假设仓库根目录 `SKILL.md` 会自动识别；需要 Codex skill/plugin 安装源或已配置的 skill 目录。

如果只存在仓库根目录 `SKILL.md`，该项应判定为未安装。

## 4. ACP / Headless 能力检查

先打印计划，不调用模型：

```bash
python scripts/run_agent_skill_qa.py plan
```

检查 ACP 相关命令：

```bash
python scripts/run_agent_skill_qa.py acp-check
python scripts/run_agent_skill_qa.py acp-check --agent gemini --agent hermes --execute
```

当前本机能力边界：

- Codex：通过 `acpx codex exec` 走 ACP client 的一次性会话。
- Claude Code：通过 `acpx claude exec` 走 Claude Code ACP adapter 的一次性会话。
- Gemini CLI：通过 `acpx gemini exec` 或 `gemini --acp` 走 ACP。
- Hermes Agent：通过 `acpx --agent "hermes acp --accept-hooks" exec` 走 raw ACP agent command。

`run-acp` 默认使用一次性 `exec`，不要求提前执行 `acpx <agent> sessions new`，也避免复用历史 session 导致测试结果被上一次对话污染。
测试命令会传入 `--approve-all`，确保 agent 能真正加载 skill 和引用文件；只对本仓库内的受信任 QA prompt 使用。
报告会保留每次 ACP 调用的原始 `returncode`；`run-acp` 的进程退出码以 transcript 内容判定为准，因为部分 adapter 会在已经产出有效内容后返回 reconnect 类状态码。

运行 ACP 自动化单场景：

```bash
python scripts/run_agent_skill_qa.py run-acp --agent gemini --case A
```

运行所有 ACP 场景：

```bash
python scripts/run_agent_skill_qa.py run-acp
```

ACP 输出位置：

```text
output/agent-skill-qa/
├── acp-<agent>-<case>.txt
└── agent-skill-qa-acp-report.jsonl
```

## 5. 自动化测试矩阵

| 编号 | 场景 | Prompt | 预期行为 |
| --- | --- | --- | --- |
| A | Recipe Generation，未指定输出模式 | `Use $rookie-cooking 生成番茄炒蛋。` | 支持交互选择的 agent 先提供默认和厨房执行版两个选项；不支持时直接默认生成。 |
| B | Recipe Generation，明确厨房版 | `Use $rookie-cooking 生成番茄炒蛋，只要厨房版。` | 不触发 QA，直接输出厨房执行版。 |
| C | Recipe Generation，明确默认 | `Use $rookie-cooking 生成 2 人份青椒肉丝，选择默认。` | 不触发 QA，输出完整解释版，并询问 PDF 或打印。 |
| D | Recipe Generation，明确厨房执行版 | `Use $rookie-cooking 生成 4 人份红烧肉，家里是电磁炉，选择厨房执行版。` | 不触发 QA，输出厨房执行版，并询问 PDF 或打印。 |
| E | Troubleshooting | `Use $rookie-cooking 诊断：我做的蒸蛋有很多蜂窝，表面还出水。` | 不触发输出模式 QA，先给安全判断，再给失败诊断、原因、下次调整和记忆处理选项。 |
| F | Learning | `Use $rookie-cooking 为什么炒青菜会出水？` | 不触发输出模式 QA，默认短答并给展开选项；不应先询问解释深度。 |
| G | Meal Planning | `Use $rookie-cooking 两菜一汤给 3 个人，怎么安排？` | 不触发输出模式 QA，先推断规划模式，输出菜单、时间线和设备冲突；完整购物清单必须先选择清单模式。 |
| H | Recipe Import | `Use $rookie-cooking 把这个菜谱改写成新手版：鸡蛋两个，番茄两个，炒熟即可。` | 不触发输出模式 QA，进入导入改写流程，区分持久化目标和输出形态，初始 review 状态为 `draft`。 |
| I | Memory Init / Update | `Use $rookie-cooking 以后默认 4 人份。` | 不触发输出模式 QA，展示写入预览并要求 Confirm write / Edit values / Cancel。 |

运行单 agent 单场景：

```bash
python scripts/run_agent_skill_qa.py run-headless --agent gemini --case A
```

运行所有 headless fallback 场景：

```bash
python scripts/run_agent_skill_qa.py run-headless
```

输出位置：

```text
output/agent-skill-qa/
├── <agent>-<case>.txt
└── agent-skill-qa-report.jsonl
```

## 6. QA 选项检查

场景 A 中，如果 agent 支持交互选择，选项只覆盖两类输出模式：

- 默认：完整解释版；生成完成后询问是否需要 PDF 或直接打印。
- 厨房执行版：一页打印卡；生成完成后询问是否需要 PDF 或直接打印。

快速和精准不再作为 Recipe Generation 输出模式选项。

允许不同 agent 使用不同 UI 表达，例如 option chips、question form、structured user input 或终端菜单。普通文本追问也可以记录，但不算完整通过“交互选择工具”要求。

## 7. 选择后行为检查

对场景 A 分别选择两个选项，各跑一次：

| 用户选择 | 必须出现 | 不应出现 |
| --- | --- | --- |
| 默认 | 完整解释版、已使用假设、交互式后续交付选择 | 厨房执行版正文、只给极短步骤 |
| 厨房执行版 | 厨房执行版、一页打印卡、安全提示、出错补救、交互式后续交付选择 | 完整解释版长篇说明 |

所有输出都必须避免无约束使用“适量”“少许”“一会儿”“炒熟”“收汁即可”等模糊词。

## 8. 后续交付检查

Recipe Generation 输出完成后，如果运行时支持交互选择工具，后续交付不能只用普通文本问“需要生成 PDF 或打印吗”。必须提供交互式选项：

- 生成 PDF
- 直接打印
- 暂不需要

用户选择直接打印时，先列出打印设备并让用户选择设备。若当前环境没有打印服务或打印设备，必须再次提供交互式降级选项：

- 生成 PDF
- 输出厨房执行版文本

一次性生成的 PDF / 打印材料必须使用 `tmp/print-jobs/` 里的临时厨房执行版 artifact；不得写入 `recipes/`。

## 9. 降级行为检查

如果某个 agent 不支持交互选择工具，场景 A 的预期是：

1. 不停下来等待用户选择。
2. 使用默认输出模式。
3. 简短说明假设，例如“未指定输出模式，按默认输出完整解释版；如需 PDF 或打印，将使用厨房执行版。”
4. 继续生成可执行菜谱。

如果 agent 反复询问、要求用户手工选择但不提供工具，或因为不能 QA 而停止生成，记为失败。

## 10. 记录模板

每个 agent 单独记录：

```text
Agent:
版本 / 日期:
Skill 安装方式:

Prompt 编号:
原始 Prompt:
是否触发 rookie-cooking:
是否触发 Interactive QA:
QA 形式: option chips / question form / structured input / plain text / none
用户选择:
是否按选择输出:
是否保留安全提示:
是否保留出错补救:
是否出现无约束模糊词:
结论: pass / partial / fail
问题记录:
```

## 11. 汇总表

| Agent | 安装发现 | ACP check | Headless A | B 厨房版 | C 默认 | D 厨房执行版 | E 诊断 | F 学习 | G 一餐规划 | H 导入 | I 记忆 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex |  | acpx |  |  |  |  |  |  |  |  |  |  |
| Claude Code |  | acpx adapter |  |  |  |  |  |  |  |  |  |  |
| Gemini CLI |  | acpx/native |  |  |  |  |  |  |  |  |  |  |
| Hermes Agent |  | acpx raw agent |  |  |  |  |  |  |  |  |  |  |
| OpenClaw | 可选 | orchestrator | 可选 | 可选 | 可选 | 可选 | 可选 | 可选 | 可选 | 可选 | 可选 | 可选 |

## 12. 失败分级

- P0：明确指定输出模式仍错误触发 QA，或不支持 QA 时阻塞生成。
- P1：未指定输出模式且支持交互选择工具，但没有触发 QA。
- P1：选择厨房执行版后输出完整解释版长文。
- P1：Recipe Generation 输出缺少关键安全提示或出错补救。
- P1：agent 未安装 skill，却被测试误判为已触发 skill。
- P2：QA 选项命名略有差异，但语义完整。
- P2：降级说明缺失，但默认输出正确生成。

P0 和 P1 需要回到 `SKILL.md` 调整规则；P2 先记录，只有多 agent 重复出现时再修改。
