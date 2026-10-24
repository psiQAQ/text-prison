# 本地六模型评测与证据工作台 v0.3

Pi 负责写作与独立执行，Pi 和 agy 提供六位独立 AI 评委。保存真实 JSONL、产物及成本；四场景试跑属于探索性实验，正式收益门槛保持 `UNSET`。

## 当前六评委流程

2026-10-25 起，本轮采用 `ai_only`：取消人工初判、冻结和最终裁决。网页直接展示各模型意见；它们不是人工金标准，也不按多数票生成“正确答案”。旧 `pilot-20261024` 的数据和人工历史保留。

在仓库根目录的 PowerShell 中运行。下面的初始化只执行一次；实验已存在时直接使用后续命令恢复。初始化从旧实验复制冻结输入、原始调用证据和预算账本，保留来源哈希，不复制人工记录。

```powershell
.\.venv\Scripts\python.exe -m eval init-ai --experiment ai-six-20261025 --inherit-from pilot-20261024
.\.venv\Scripts\python.exe -m eval plan
.\.venv\Scripts\python.exe -m eval run calibration --experiment ai-six-20261025
.\.venv\Scripts\python.exe -m eval run pilot --experiment ai-six-20261025
.\.venv\Scripts\python.exe -m eval summarize --experiment ai-six-20261025
.\.venv\Scripts\python.exe -m eval serve --experiment ai-six-20261025 --port 8765
```

打开 <http://127.0.0.1:8765>，选择批次和候选查看来源、六位评委的逐项证据、错误类型、不确定项及失败状态，可以导出当前结果。此模式没有人工填表、提交或冻结按钮。模型结果随运行逐步写入；重新选择批次或刷新页面可载入最新进度。

`calibration` 保留为 CLI 阶段名称，表示对 12 条冻结材料完成冒烟、结构和引文检查。它不再表示“对人工金标准校准成功”。所有模型就绪且校准侧车有效后才进入试跑。语义分歧本身不阻塞试跑；无效响应、超时和模型调用失败须保留并诊断。

报告分别给出每个模型的语义指标和覆盖率，并按固定必需事实 ID 比较状态分歧。自由提取声明不直接计算一致率；缺失的模型和失败生成不能从分母中消失。模型间一致不等于正确，不计算无金标准的准确率。

网页的“已完成”表示已返回有效评审记录；汇总中的 `completed_review_coverage` 还要求该评审没有未决事实或不确定项，因此可能更低。候选被评委判为语义失败，也不同于模型调用失败；两类状态分别保留。

## 模型、权限与预算

| 用途 | 宿主与模型 | 请求设置 |
|---|---|---|
| 写作／独立执行 | Pi `openai-codex/gpt-6-luna` | medium |
| 评委一 | Pi `deepseek/deepseek-flash` | high |
| 评委二 | Pi `openai-codex/gpt-6-sol` | high |
| 评委三 | agy `gemini-4-argon-high` | High 型号 |
| 评委四 | agy `gemini-3.8-flash-high` | High 型号 |
| 评委五 | agy `claude-opus-5-5-high` | High 型号 |
| 评委六 | agy `claude-sonnet-5-5-high` | High 型号 |

Pi 启动器默认在 `~/.pi/agent/bin/pi-launcher.js`；非默认安装使用 `TEXTPRISON_PI_LAUNCHER`、`TEXTPRISON_NODE`、`PI_CODING_AGENT_DIR`。agy 使用本机安装程序。沿用现有认证，不复制密钥、不修改全局默认模型。实际模型返回标识与请求型号分别记录，未返回时不推断。

Pi 每次使用新工作区，关闭默认扩展、MCP、其他 Skill、模板、目录上下文与通用 shell。写作者仅获得限定路径读写；原生 D 另有固定检查工具。agy 评委使用专用 agent，并在每个任务目录安装拒绝全部工具执行的局部 hook；接受结果前核验会话与调用审计、配置哈希和零工具尝试。它不修改全局 hooks，工作目录本身也不等于安全沙箱。隐藏验收在模型工具范围外运行。

当前 agy 的 `init.tools` 是目录广告，不能用它证明所选 agent 的可执行权限。适配器固定已检查的二进制 SHA-256，并用真实合成文件读取探针验证 hook 拒绝；升级二进制后须重新核验兼容性。产品版本未能从当前程序取得时记为未知，不以内部语言服务器版本代替。依据及实测见 [v0.3 验证记录](../validation/v0.3/README.md)。

上限 **276 次 CLI、累计 14400 秒**，包含从旧实验继承的调用、失败、重试及耗时，不因换实验名称清零。计划分配：冒烟 7、校准 72、写作 16、反馈修订 8、独立执行 8、触发 8、候选评审 144，共 263；另有 13 次故障预留。单次最长 300 秒。Pi 工具回合上限仍为 8。未使用的预留不自动扩样。

一次 CLI 不等于一次内部模型请求。保留原始 usage；累计事件不重复求和，无法观测的模型请求数和成本保持未知。agy 的用户轮次数不能直接当作模型调用数。不同宿主的系统提示成本也包含在各自实际用量中。

恢复默认复用完成记录。诊断后使用 `--retry-failed` 保留原失败并创建新尝试，重试消耗同一预算。变更来源、规则或分配需要新实验；若继承已有结果，必须同时继承其真实成本与来源身份。未完成预算行必须先核对已记录进程退出，不得在模型仍运行时释放。

本次采集在 255/276 次停止：两位 Claude 的配额错误后，保留已有结果并将后续 21 项标为 `blocked`，没有继续撞同一配额。当前剩余额度只够这 21 项首次尝试，不能同时覆盖全部 15 份既有失败；恢复前须核对配额、待执行清单和预算，不能把无差别重试当作必然补齐。完整状态与失败证据见 [v0.3 记录](../validation/v0.3/README.md)。

前台服务用 `Ctrl+C` 停止，网页也有“停止服务”。后台进程停止前核对本次 PID 和归属，不按进程名批量终止。停止服务不删除评审数据。

## 历史人工批次

旧实验可用 `--experiment pilot-20261024` 查看。`human_blind` 模式保持原有独立初判、整批冻结、揭盲和裁决规则；本次没有删除其数据库或替用户填写。取消人工评审适用于新的 `ai_only` 流程，不能把旧记录改标为 AI 结果。

## 证据与接口

| 路径 | 内容 |
|---|---|
| `runs/<实验>/experiment.json`、`inputs/` | 冻结规则、数据、schema、提示及哈希 |
| `assignments.json` | 包括未运行项的全部计划分配 |
| `jobs/<分配>--<尝试>/` | 提示、原始事件、stderr、receipt、run、产物与评审侧车 |
| `reviews.sqlite` | 评审模式与各模型结果；历史人工库另保留初判和裁决 |
| `budget.sqlite` | 持久化调用次数与耗时 |
| `summary.json`、`SUMMARY.md` | 分母、覆盖、成本及人工进度 |

`run.schema.json` 为 v0.2，旧版保留在 `schemas/run-v0.1.schema.json`。离线导入：

```powershell
.\.venv\Scripts\python.exe -m eval import old-run.json --kind run --output runs/imported-run.json
.\.venv\Scripts\python.exe -m eval import events.jsonl --kind pi --output runs/imported-events.json
```

转换不改原文件。模型侧车先做 JSON/schema/证据引用校验，汇总由代码派生。无效评审保留为失败；用量不完整时总额未知，已观测部分另列。Pi 美元值只是目录估算，不是账单核验。

`python -m eval tokens --experiment ai-six-20261025` 生成 `o200k_base` 离线长度估算，注明 tokenizer 版本与词表哈希。词表缺失时失败；取得下载授权后可加 `--fetch-tokenizer`，只缓存到项目 `.local/tiktoken/`。该结果仅比较规则文本长度，不等于模型账单 Token、完整上下文或产品成本收益。

方法见 [PROTOCOL](PROTOCOL.md)、[METRICS](METRICS.md)、[PREREGISTRATION](PREREGISTRATION.md)。历史 `validation/` 和根清单描述原始包，六模型工程证据另存 `validation/v0.3/`，v0.2 证据保持历史含义。
