# 本地评测与人工工作台 v0.2

Pi 负责写作、独立执行和双 AI 评审，保存真实 JSONL、产物及成本。人工工作台用于一位评委的独立初判与最终裁决。四场景试跑属于探索性实验，正式收益门槛保持 `UNSET`。

## 从校准开始

以下命令在仓库根目录的 PowerShell 中运行，使用项目虚拟环境。环境安装见 [仓库说明](../README.md)。`doctor` 只核对认证就绪，不消耗推理调用；`run` 会调用模型。

```powershell
.\.venv\Scripts\python.exe -m eval doctor
.\.venv\Scripts\python.exe -m eval validate
.\.venv\Scripts\python.exe -m eval plan
.\.venv\Scripts\python.exe -m eval run calibration --experiment pilot-20261024
.\.venv\Scripts\python.exe -m eval serve --experiment pilot-20261024 --port 8765
```

打开 <http://127.0.0.1:8765>，按批次操作：

1. 阅读来源、候选、必需事实、输出契约和严重程度规则。自行添加声明，逐项填写判断与原文证据；可以保存草稿并恢复。
2. 提交全部 12 条独立初判，再冻结整批。冻结前，接口也不返回 AI 结果、实验组或写作模型。
3. 揭盲后查看两位 AI 的证据和分歧，提交每条最终裁决。初判保留且不可覆写；最终判断不采用多数票。
4. 导出评审记录。多标签页冲突会拒绝覆盖；保留自己的文字后重新载入。

全部校准最终裁决提交后，试跑命令才能通过人工门禁：

```powershell
.\.venv\Scripts\python.exe -m eval run pilot --experiment pilot-20261024
.\.venv\Scripts\python.exe -m eval summarize --experiment pilot-20261024
```

产物齐全时，第二批有 24 份候选，按相同步骤完成初判和裁决。`summarize` 在揭盲前隐藏语义结果，防止提前泄露 AI 判断。本轮没有人类阅读理解实验。

前台服务用 `Ctrl+C` 停止。后台启动需保留本次 PID、命令和日志，停止前核对 PID 的路径与归属，不能按进程名批量停止。

## 模型、权限与预算

| 用途 | 模型与请求设置 |
|---|---|
| 写作／独立执行 | `openai-codex/gpt-6-luna`，`medium` |
| 评委一 | `deepseek/deepseek-flash`，`high` |
| 评委二 | `openai-codex/gpt-6-sol`，`high` |

启动器默认在 `~/.pi/agent/bin/pi-launcher.js`。非默认安装可设置 `TEXTPRISON_PI_LAUNCHER`、`TEXTPRISON_NODE`、`PI_CODING_AGENT_DIR`。沿用用户认证，不复制密钥或改变全局默认模型。请求与服务端实际设置分别记录；未返回模型快照时保留 null。

每次调用使用新工作区，关闭默认扩展、MCP、其他 Skill、模板、目录上下文与通用 shell。写作者仅获得限定路径读写；原生 D 另有固定检查工具，评委无工具。Pi 工作目录本身不是安全沙箱，路径限制由显式评测扩展执行；隐藏验收在模型工具范围外运行。检测到全局 `SYSTEM.md` / `APPEND_SYSTEM.md` 或非零 provider 重试时停止并报告，不修改用户配置。

最多 128 次 CLI、累计 14400 秒，每次最多 300 秒、8 个工具回合；115 次计划分配与 13 次故障预留分开。失败计入预算。Pi 内部模型请求数与 Token 另记，一次 CLI 不等于一次模型请求。人工等待不计入 CLI 时间。

恢复命令默认复用已有记录。诊断后用 `--retry-failed` 创建保留原始失败的新尝试，仍消耗总预算。冻结揭示过的评审不能替换。输入、规则或计划改变需要新实验名称。进程意外终止留下未完成预算行时，先核对 receipt 的 PID 已退出；不得在仍运行时释放预算。

## 证据与接口

| 路径 | 内容 |
|---|---|
| `runs/<实验>/experiment.json`、`inputs/` | 冻结规则、数据、schema、提示及哈希 |
| `assignments.json` | 包括未运行项的全部计划分配 |
| `jobs/<分配>--<尝试>/` | 提示、原始事件、stderr、receipt、run、产物与评审侧车 |
| `reviews.sqlite` | 初判、冻结状态、裁决及修订历史 |
| `budget.sqlite` | 持久化调用次数与耗时 |
| `summary.json`、`SUMMARY.md` | 分母、覆盖、成本及人工进度 |

`run.schema.json` 为 v0.2，旧版保留在 `schemas/run-v0.1.schema.json`。离线导入：

```powershell
.\.venv\Scripts\python.exe -m eval import old-run.json --kind run --output runs/imported-run.json
.\.venv\Scripts\python.exe -m eval import events.jsonl --kind pi --output runs/imported-events.json
```

转换不改原文件。模型侧车先做 JSON/schema/证据引用校验，汇总由代码派生。无效评审保留为失败；用量不完整时总额未知，已观测部分另列。Pi 美元值只是目录估算，不是账单核验。

`python -m eval tokens --experiment pilot-20261024` 生成 `o200k_base` 离线长度估算，注明 tokenizer 版本与词表哈希。词表缺失时失败；取得下载授权后可加 `--fetch-tokenizer`，只缓存到项目 `.local/tiktoken/`。该结果仅比较规则文本长度，不等于模型账单 Token、完整上下文或产品成本收益。

方法见 [PROTOCOL](PROTOCOL.md)、[METRICS](METRICS.md)、[PREREGISTRATION](PREREGISTRATION.md)。历史 `validation/` 和根清单描述原始包，当前工程证据另存 `validation/v0.2/`。
