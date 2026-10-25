# Vale 配置与规则目录

本页是 Vale 配置、包版本和启用规则的维护入口。文字指导不依赖 Vale；本目录不包含 Python 后端或其他插件。中文排版可另选 [AutoCorrect 配置](../autocorrect/README.md)，不把英文 Google/Microsoft 包称为完整中文规则。文件提供、工具安装和具体文档检查分别记录。

## 选择配置

CLI 文档基线为 [Vale 3.25.1](https://github.com/vale-cli/vale/releases/tag/v3.25.1)，维护范围为 `>=3.25.1,<4`。这不是对旧版不兼容或新版已实测的断言。范围外、未知版本先停止机械检查，不自动升级。六份配置的提示阈值均为 `suggestion`。

| 配置 | 文档用途 | 上游包 | 首次准备 | Markdown 启用规则 | 纯文本启用规则 |
|---|---|---|---|---|---|
| [dev-en.ini](dev-en.ini) | 英文开发文档 | Google v0.7.1 | 同步 Google | VagueLinkEn；Google.HeadingPunctuation、Spacing、Exclamation | Google.Spacing、Exclamation |
| [procedure-en.ini](procedure-en.ini) | 英文操作说明 | Google v0.7.1 | 同目录已有匹配版本时不重复同步 | 与 dev-en 相同；操作消歧由 Skill 另行指导 | 与 dev-en 相同 |
| [product-en.ini](product-en.ini) | 英文产品帮助 | Microsoft v0.15.1 | 同步 Microsoft | VagueLinkEn；Microsoft.HeadingPunctuation、Spacing、UIVerbs | Microsoft.Spacing、UIVerbs |
| [research-en.ini](research-en.ini) | 英文科研说明 | 无 | 不运行 sync | VagueLinkEn | 无，记 Not Run |
| [zh.ini](zh.ini) | 中文文档 | 无 | 不运行 sync | VagueLinkZh | 无，记 Not Run |
| [conservative.ini](conservative.ini) | 中英混合、多用途、Agent 指令 | 无 | 不运行 sync | VagueLinkEn、VagueLinkZh | 无，记 Not Run |

表中 VagueLinkEn/Zh 的完整规则名为 `TextPrison.VagueLinkEn` / `TextPrison.VagueLinkZh`。只处理 `.md` 和 `.txt`；其他扩展名不在初版覆盖范围。中文科研使用 zh；混合语言用 conservative，不自动分类段落后拼接多个检查结果。

Google/Microsoft 只通过 `Style.Rule = suggestion` 逐项启用；没有全量 `BasedOnStyles = Google, Microsoft`，也没有全局启用 Vale 拼写、句长、被动语态、第一人称或模态禁用规则。操作配置与开发配置目前机械规则相同，分开保留选择入口，不暗示额外 STE 检查。

## 规则含义和边界

| 规则 | 为什么保留 | 必须人工判断的情况 |
|---|---|---|
| [VagueLinkEn](styles/TextPrison/VagueLinkEn.yml) | 提示整段链接文字只有 click here、here、read more 或 learn more（允许末尾标点和空白） | 卡片上下文已足够明确时可保留；没有来源不能编造目标名称 |
| [VagueLinkZh](styles/TextPrison/VagueLinkZh.yml) | 提示整段链接文字仅为规则列出的七种泛指表述 | 中文覆盖仅限这些链接文字，不检查一般语法；`nonword: true` 避免默认英文词边界 |
| Google.HeadingPunctuation | 提醒英文标题末尾句号 | 局部修改承诺保留标题时只报告，不改锚点 |
| Google.Spacing | 提醒部分英文句末空格问题 | 缩写、文本中的标识符可能误报，不能直接套用 action |
| Google.Exclamation | 提醒开发文档中的感叹号 | 原样引用、界面标签或用户要求的语气保留 |
| Microsoft.HeadingPunctuation | 提醒英文标题末尾标点 | 问句标题可能合理；保留标题的范围约束优先 |
| Microsoft.Spacing | 提醒部分英文句末空格问题 | 技术记号与产品名称需核对原意 |
| Microsoft.UIVerbs | 提醒跨设备说明可考虑中性操作动词 | swipe 等手势或特定输入方式是必要信息时不替换 |

所有启用的上游规则均在本配置降为建议，不构成自动修复命令。初版不启用 Microsoft.Accessibility：其通用词匹配可能把技术状态词 disabled 等作为用语建议，超出本次保守覆盖。

Markdown 保留默认跳过的 block scopes，另跳过整个 `blockquote`；inline scopes 保留 `tt/code/kbd/samp` 并加 `q`。Vale 的 Markdown 解析默认略过代码、规定格式的数学表达和 URL；任意引号内文字并不自动等同于原样引文。Agent 仍需识别受保护内容，不能靠配置代替语义判断。纯文本没有这些标记作用域；只有适用的正文规则可运行，代码/公式/引文密集且无法确定范围时跳过机械检查。

## 准备上游包

以下命令仅在用户已授权下载和写入规则包时执行。先按配置表选一个入口，令 `$skillRoot` 指向实际使用的已安装 Skill。安装位置由项目安装说明提供，不在此重复维护。

```powershell
$configPath = Join-Path $skillRoot 'vale/dev-en.ini'
vale sync --config $configPath --no-global
```

这个示例同步 Google；产品帮助选择相应入口。先核对配置内容与目标目录，确认允许下载和写入后再执行。无包配置无需 sync。配置中的固定下载地址为：

- [Google v0.7.1 / Google.zip](https://github.com/vale-cli/Google/releases/download/v0.7.1/Google.zip)
- [Microsoft v0.15.1 / Microsoft.zip](https://github.com/vale-cli/Microsoft/releases/download/v0.15.1/Microsoft.zip)

`StylesPath = styles` 相对于配置文件。六个入口共用此目录；同步会替换同名包并重建 `.vale-config/`，不要在 Google/Microsoft 包内做本地定制。固定标签的发布脚本只打包对应规则目录，未带包内配置；发布脚本及规则文件的静态核对不能替代实际下载内容核验。实际同步时另记资产摘要、布局及启用规则内容。发现非空 `.vale-config/`、意外 `config/`、嵌套依赖或手改上游规则时，先核实来源和配置隔离，暂不继续检查或同步。

首次同步后保留命令、配置固定 URL、日期和同步输出。已读取的两份 `meta.json` 只记录 feed 和 Vale 版本约束，不记录包的发行版本，不能用它证明下载的是所选标签。没有可信同步记录或独立内容核对时报告“包版本未确认”；即使有来源记录，也不声称发布资产完整性已验证。更新要重新核对启用规则及包布局并取得依赖变更授权，不能每次调用都下载最新。

本目录的 [styles/.gitignore](styles/.gitignore) 精确忽略同步包和 `.vale-config/`，原创规则仍可提交。项目安装器也只排除这些生成目录，保留原创内容；不修改目标项目根 `.gitignore`。多宿主副本各自准备，互不自动更新。

## 调用与诊断

按 [Vale 调用说明](../references/vale.md) 核对输入、授权和配置，再检查明确文件或可靠的 UTF-8 stdin。不要因路径拼错把路径字符串当文本检查，也不要默认扫描整个项目。

运行完成有建议与运行失败不同：退出码 `0` 仍可能有 warning/suggestion，`1` 表示已完成且有 error 诊断，`2` 表示处理失败。需结合 stdout/stderr 和实际覆盖对象判断，不能只看 JSON 能否解析。零提示不证明语义正确，未匹配任何规则也不能记成通过。

## 来源与许可边界

查阅日期：2026-10-25。上述版本、规则名和内容来自固定文件；这里只分发配置、原创规则与自主说明，不包含 Google/Microsoft 规则包、完整指南或 STE 字典。用户同步的第三方包沿用各自许可，不能把它们视为 TextPrison 自有许可。

- [Google v0.7.1 规则目录](https://github.com/vale-cli/Google/tree/v0.7.1/Google)及[发布脚本](https://github.com/vale-cli/Google/blob/v0.7.1/.github/workflows/main.yml)。
- [Microsoft v0.15.1 规则目录](https://github.com/vale-cli/Microsoft/tree/v0.15.1/Microsoft)及[发布脚本](https://github.com/vale-cli/Microsoft/blob/v0.15.1/.github/workflows/main.yml)。
- [CLI](https://docs.vale.sh/topics/cli)、[StylesPath](https://docs.vale.sh/keys/stylespath)、[Packages](https://docs.vale.sh/keys/packages)、[BasedOnStyles](https://docs.vale.sh/keys/basedonstyles)、[MinAlertLevel](https://docs.vale.sh/keys/minalertlevel)。
- [existence](https://docs.vale.sh/checks/existence)、[Scopes](https://docs.vale.sh/topics/scopes)、[SkippedScopes](https://docs.vale.sh/keys/skippedscopes)、[IgnoredScopes](https://docs.vale.sh/keys/ignoredscopes)、[Markdown](https://docs.vale.sh/formats/markdown)。
