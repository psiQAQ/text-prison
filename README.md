# TextPrison / 文字狱

**按输出类型约束表达，保留原意，用真实结果评估效果。**

这是一个可安装的技术写作 Skill，以及可复核的本地评测工具。项目名暂定 `TextPrison`，仓库和 Skill 名为 `text-prison`。未核验商标、域名或包名可用性。

## 当前状态

2026-10-25：实验流程升级到 v0.3，采用 Pi 与 agy 的六位 AI 评委，取消本轮人工填写、冻结和裁决门槛。已生成 24 份候选，8 项隐藏执行验证通过；候选评审有效 108/144，失败 15，另有 21 项因两位 Claude 配额耗尽未尝试。共用 255/276 次调用、约 2.53 小时，结果标为部分完成。见 [当前验证记录](validation/v0.3/README.md) 和 [分组结果](validation/v0.3/RESULTS.md)。

运行记录继续使用 v0.2 schema。旧双评委实验及人工记录保留，新实验继承既有调用和用量，不重新计算预算起点。[旧工程验证](validation/v0.2/README.md)仅证明上一版状态。

新方案引入原子事实支持+必需事实保留、独立行为测试、等修订机会对照、部署基率校正和预注册统计；原先固定百分比只保留为历史假设，不再是默认验收标准。

## 当前可用

- 一份共用 `SKILL.md`，六类输出规则，英文/中文语言规则，Codex 隐式调用元数据。
- 项目级安装器：支持 Codex `.agents/skills/text-prison`、Claude `.claude/skills/text-prison`、Pi `.pi/skills/text-prison`；拒绝覆盖，不修改目标项目的 AGENTS.md、CLAUDE.md、权限或 hooks。`both` 仍仅指 Codex 和 Claude。
- 离线 Markdown/JSON 机械检查器，支持显式文本契约、英文句长警告、术语别名、链接文字、标题层级、JSON 和本地 JSON Schema。
- 4 个合成场景、12 条校准材料、隐藏执行验证器、版本化 schema、原始日志与缺失值明确的汇总。
- 本地模型评审网页：直接查看六位 AI 的独立证据、失败状态和分歧，无需人工填表。历史人工批次仍可按原流程读取。

自动触发依赖宿主按 description 选择 Skill，不能保证每次发生。显式冒烟通过不等于隐式触发可靠。四场景属于探索性试跑，不宣称正式收益；人类阅读理解、Codex/Claude 原生实测和证据驱动的规则压缩尚未完成。

## 安装与检查

在仓库根目录执行；以下是 Windows PowerShell 示例。已有环境直接使用 `.venv`，不要重复创建。其他系统使用对应虚拟环境的 Python 路径。

```powershell
# 首次创建并安装已锁定的开发环境；仅使用检查器可只安装 requirements.lock。
uv venv .venv
uv pip sync --python .venv/Scripts/python.exe requirements-dev.lock

# 仅在明确指定的已有项目中安装；将路径替换为目标项目目录。
.\.venv\Scripts\python.exe tools/install_skill.py --agent pi --project ../your-project

# 检查示例，完整证据写入独立 JSON，不全部注入模型上下文。
.\.venv\Scripts\python.exe skills/text-prison/scripts/check.py examples/draft-good.md --profile research --lang en --contract examples/contract.json --report runs/example-good.json

# 检查 JSON；没有 schema 时只能得到语法检查结果。
.\.venv\Scripts\python.exe skills/text-prison/scripts/check.py examples/config.json --profile structured --lang en --schema examples/schema.json

# 执行离线回归，不调用模型。
.\.venv\Scripts\python.exe -m pytest --basetemp runs/tests/all -q
```

Codex 可显式使用 `$text-prison`，Claude Code 可显式使用 `/text-prison`，Pi 使用 `/skill:text-prison`。自然语言请求用于测试隐式触发，例如“将这份安装说明改成步骤清晰的中文文档，保留所有条件和参数”。宿主版本与来源参见 `sources.json`。

安装器生成每份副本的 `install-manifest.json`。只维护 `skills/text-prison` 这一份源文件。此原型没有更新/卸载命令；更新前应审查目标副本与 manifest 的差异，不要删除未知用户文件。安装器运行时并不安装 Python 依赖。

## 结果解释

退出码 `0` 表示本次执行的机械检查没有 error，允许存在 warning；`1` 表示发现契约/语法/schema 错误；`2` 表示工具、依赖、参数或 schema 配置问题。依赖缺失可能在 Python 导入阶段直接报错，不能当作检查通过。

机械报告的 `semantic_status` 和 `asd_ste100_conformance` 始终为 `not_evaluated`。检查器不判断事实是否真实、引用是否支持结论，也不读取完整 STE 词典。语义评审另存带逐项证据的侧车；本轮没有人工金标准，只能报告各模型判断、覆盖和分歧，不能称为准确率或人工验收。未做检查不是零错误。`required_literals` 是字符串保护，不是事实正确性验证。

## 打开模型评审

```powershell
.\.venv\Scripts\python.exe -m eval serve --experiment ai-six-20261025 --port 8765
```

打开 <http://127.0.0.1:8765>，选择候选即可查看已完成的 AI 证据。首次生成、模型配置、预算、恢复与报告命令见 [评测使用说明](eval/README.md)。原始实验放在已忽略的 `runs/`，不纳入提交。

`examples/draft-semantic-error.md` 故意保留数字但删除限制、加强确定性并添加行为。它可以通过字面检查。这是用于防止虚假“合规保证”的反例，不是产品效果展示。

## 项目资料

| 文件 | 内容 |
|---|---|
| [docs/DESIGN.md](docs/DESIGN.md) | 范围、路由、语义保护、规则证据与运行/评测分离 |
| [docs/RELATED_WORK.md](docs/RELATED_WORK.md) | 相关实现、原始文献与采纳边界 |
| [eval/PROTOCOL.md](eval/PROTOCOL.md) | 实验分组、独立验收、触发与失败处理 |
| [eval/METRICS.md](eval/METRICS.md) | 指标公式、分母、覆盖、成本与区间 |
| [eval/PREREGISTRATION.md](eval/PREREGISTRATION.md) | 正式测试前冻结的目标与门槛 |
| [docs/IMPLEMENTATION_DELTA.md](docs/IMPLEMENTATION_DELTA.md) | 当前实现、兼容性与尚未覆盖范围 |
| [eval/prompts/semantic-review.md](eval/prompts/semantic-review.md) | 独立语义评审指令与证据要求 |
| [eval/README.md](eval/README.md) | Pi/agy 六评委实验、网页与导出命令 |

五个 `submodules/` 上游固定到明确提交，只作研究参考，不自动安装或运行。机器来源索引标明已核验范围，未读原文不称为已核验。原始 ZIP、根 `MANIFEST.sha256.json`、`DOCS_PATCH.md` 与历史验证文件保持基线含义；六评委证据另存 `validation/v0.3/`。

## 非目标

不做思想或观点审查，不以绕过 AI 文本检测器为目标，不自动“人性化”全部文本，不强制论文和 JSON 使用维修手册语气，不自动授权危险操作，不加入 MCP 或全局 hooks。评审网页仅在显式启动后监听本机 loopback。
