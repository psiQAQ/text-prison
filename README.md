# TextPrison / 文字狱

**按输出类型约束表达，保留原意，用真实结果评估效果。**

这是一个可安装的 Skill 起步原型，以及下一阶段的项目设计和 A/B 实验协议。项目名暂定 `TextPrison`，仓库和 Skill 名为 `text-prison`。未核验商标、域名或包名可用性。

## 文档修订状态

2026-10-24：研究与实验设计更新为文档协议 v0.2，**运行时实现和记录 schema 仍为 v0.1**。本次仅修改 Markdown，没有新增自动语义评分、原生宿主采集或实际效果数据。覆盖说明见 [DOCS_PATCH.md](DOCS_PATCH.md)。

新方案引入原子事实支持+必需事实保留、独立行为测试、等修订机会对照、部署基率校正和预注册统计；原先固定百分比只保留为历史假设，不再是默认验收标准。

## 当前可用

- 一份共用 `SKILL.md`，六类输出规则，英文/中文语言规则，Codex 隐式调用元数据。
- 项目级安装器：复制到 `.agents/skills/text-prison` 和/或 `.claude/skills/text-prison`；拒绝覆盖已有安装，不修改 AGENTS.md、CLAUDE.md、权限或 hooks。
- 离线 Markdown/JSON 机械检查器，支持显式文本契约、英文句长警告、术语别名、链接文字、标题层级、JSON 和本地 JSON Schema。
- 测试、故意含有语义错误的反例、规则来源记录、A/B 协议和记录 schema。

自动触发依赖宿主按 description 选择 Skill，不能保证每次发生。起步包交付时未进行宿主端触发测试、模型调用、人工阅读实验或真实 Token 对比；本次文档修订也没有执行这些实验。测试通过不等于标准认证或效果提升。

## 安装与检查

在解压后的项目目录执行。以下 Python 命令适用于 Windows、macOS 和 Linux；Python 环境需由使用者选定。

```sh
# 安装离线检查器运行依赖；建议在项目虚拟环境中执行。
python -m pip install -r requirements.txt

# 仅在明确指定的已有项目中安装；将路径替换为目标项目目录。
python tools/install_skill.py --agent both --project ../your-project

# 检查示例，完整证据写入独立 JSON，不全部注入模型上下文。
python skills/text-prison/scripts/check.py examples/draft-good.md --profile research --lang en --contract examples/contract.json --report reports/example-good.json

# 检查 JSON；没有 schema 时只能得到语法检查结果。
python skills/text-prison/scripts/check.py examples/config.json --profile structured --lang en --schema examples/schema.json

# 安装测试依赖并运行回归测试。
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Codex 可显式使用 `$text-prison`，Claude Code 可显式使用 `/text-prison`。自然语言请求用于测试隐式触发，例如“将这份安装说明改成步骤清晰的中文文档，保留所有条件和参数”。显式调用成功不能替代隐式触发验证。宿主版本和来源参见 `sources.json`；发布前应固定版本并回归。

安装器生成每份副本的 `install-manifest.json`。只维护 `skills/text-prison` 这一份源文件。此原型没有更新/卸载命令；更新前应审查目标副本与 manifest 的差异，不要删除未知用户文件。安装器运行时并不安装 Python 依赖。

## 结果解释

退出码 `0` 表示本次执行的机械检查没有 error，允许存在 warning；`1` 表示发现契约/语法/schema 错误；`2` 表示工具、依赖、参数或 schema 配置问题。依赖缺失可能在 Python 导入阶段直接报错，不能当作检查通过。

`semantic_status` 和 `asd_ste100_conformance` 在本原型中始终为 `not_evaluated`。检查器不判断事实是否真实、引用是否支持结论，也不读取完整 STE 词典。未做检查不是零错误。`required_literals` 是字符串保护，不是事实正确性验证。

`examples/draft-semantic-error.md` 故意保留数字但删除限制、加强确定性并添加行为。它可以通过字面检查。这是用于防止虚假“合规保证”的反例，不是产品效果展示。

## 项目资料

| 文件 | 内容 |
|---|---|
| [docs/DESIGN.md](docs/DESIGN.md) | 范围、路由、语义保护、规则证据与运行/评测分离 |
| [docs/RELATED_WORK.md](docs/RELATED_WORK.md) | 相关实现、原始文献与采纳边界 |
| [eval/PROTOCOL.md](eval/PROTOCOL.md) | 实验分组、独立验收、触发与失败处理 |
| [eval/METRICS.md](eval/METRICS.md) | 指标公式、分母、覆盖、成本与区间 |
| [eval/PREREGISTRATION.md](eval/PREREGISTRATION.md) | 正式测试前冻结的目标与门槛 |
| [docs/IMPLEMENTATION_DELTA.md](docs/IMPLEMENTATION_DELTA.md) | 后续代码/配置修改及兼容性要求 |
| [eval/prompts/semantic-review.md](eval/prompts/semantic-review.md) | 独立语义评审模板，尚非自动能力 |

`eval/run.schema.json`、`skills/text-prison/assets/rules.json`、`sources.json`、`NOTICE.md` 保持起步包版本。新文献先登记在 RELATED_WORK；`validation/` 是原始本地检查记录，不是 A/B 实验结果。

## 非目标

不做思想或观点审查，不以绕过 AI 文本检测器为目标，不自动“人性化”全部文本，不强制论文和 JSON 使用维修手册语气，不自动授权危险操作，不在首版加入 MCP、常驻服务或全局 hooks。
