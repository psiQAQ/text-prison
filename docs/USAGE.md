# 使用 TextPrison

TextPrison 按文档用途选择规则、改写并核对原意。Vale 提供显式写作规则的机械诊断，AutoCorrect 可选地提供中文排版建议；缺少工具也可完成写作指导。先按[安装说明](INSTALL.md)准备所需宿主副本，显式调用方式见其中的[宿主表](INSTALL.md#1-将-skill-安装到已有项目)。自动发现由宿主决定，不保证不同宿主的触发行为一致。

## 1. 说明对象和允许的改动

在宿主对话中调用 Skill，并给出文件或粘贴文本、读者、用途和修改范围。例如在 Codex 中可以提出：

> $text-prison 请把 README 的安装章节改得更清楚。面向首次使用者，保留标题、命令和其他章节，不补充未经证实的安装步骤。

已经明确对象和动作的请求会直接按范围执行，不为“改通顺”重复弹出菜单。只有存在影响结果的真实选择时，Skill 才提出 2–3 个选项，例如保留结构的局部清晰化、按读者任务重组、仅检查。每项说明修改范围、适用规则、所选工具及调用次数、需要用户复核的内容；尚未选定时不开始依赖该选择的改写。

仅检查不修改原文。只改某一节、术语或表达时，即使检查结果包含其他问题，也不扩大修改范围。重组若影响标题锚点，先检查引用；跨文件修改超出授权时保留原锚点或请求扩大范围，不顺手修改其他文件。

普通聊天、纯代码修改、逐字转录和纯 JSON 等机器格式不进入文风优化。DOCX、PDF、HTML、MDX 等没有确认处理方式的输入不自动转换，也不安装转换器。

## 2. 写作与检查顺序

通常只读取当前用途和语言所需的参考，品牌、中文本地化及排版摘要按任务选择；操作说明确有需要时再读 STE-inspired。配置对应关系、包和版本分别见 [Vale 配置说明](../skills/text-prison/vale/README.md)和 [AutoCorrect 配置说明](../skills/text-prison/autocorrect/README.md)，不要求用户先掌握配置名才能选择写作方式。

改写任务依次进行：按已选范围写初稿 → 所选且就绪的工具各检查一次 → 合并适用诊断并作一次针对性修订 → 必要时至多复查一次。若选择 Vale 与 AutoCorrect，同一轮每个工具至多运行一次，共用这一次修订及至多一次复查，不形成两个独立循环。仅检查模式每个所选工具最多检查原文一次、只报告。缺少某个工具时该项记 `Not Run`，另一项可以继续，不在后续轮次补跑。没有额外模型评委，也不循环追求零警告。

每项修改都需核对主体、对象、否定、条件、不确定性、数字、单位、因果、版本和引用。代码、命令、标识符、公式和原样引文默认保留；来源缺失时明确缺口，不补造事实、操作前提或验收条件。科研中的 `may`、`might`、`could`、误差范围和适用条件不能为了简洁被删除。

两个工具的提示是否采纳，都取决于规则适用性和用户授权。局部清晰化不因标题提示改标题，只改术语不处理其他表达问题。误报保留原意并解释理由，不为一次提示关闭全局规则。修改词汇表、添加局部忽略同样需要处于已授权的文档或配置范围内。

中文排版优先遵循项目明确配置，再参考项目既有文稿的一致写法，最后才采用 Skill 默认建议。社区的中西文或数字间距属于可选风格，只有用户选择排版调整或项目惯例支持时才修改；其余可以报告但不强改。科学数字、单位、百分比和公式遵从领域与项目规则，不能为消除间距提示而破坏表示方式。

## 3. 指定文件运行 Vale

以下是供日后实际使用的 PowerShell 命令，不表示本仓库已运行。先按[安装说明](INSTALL.md)设置已安装副本的 `$skillRoot`，确认 CLI 版本、配置和实际启用的规则文件就绪。

若项目已有 Vale 配置，先读它并默认采用其绝对路径，保留原文件；下面的 Skill 配置只用于没有项目配置或用户已选它的情形。配置依赖全局资源时先明确采用范围，不隐式去掉 `--no-global`；缺包不自动同步。

```powershell
$configPath = Join-Path $skillRoot 'vale/dev-en.ini'
$documentPath = 'D:/path/to/your-project/README.md'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "配置不存在：$configPath"
}
if (-not (Test-Path -LiteralPath $documentPath -PathType Leaf)) {
    throw "文档不存在：$documentPath"
}
vale --config $configPath --no-global --output=JSON $documentPath
$valeExitCode = $LASTEXITCODE
```

显式检查文件存在，防止拼错路径被 CLI 当成直接文本。使用实际绝对路径、逐个指定文档，不默认传入仓库根目录。macOS/Linux 使用 `vale --config "$configPath" --no-global --output=JSON "$documentPath"`，事先用 shell 的文件检查确认两个路径存在，调用后立即保存 `$?`。

## 4. 用 Vale 检查粘贴文本和未保存的新稿

宿主能够可靠传递 UTF-8 stdin，且能确定配置与输入作用域时，可直接检查片段，不为检查擅自保存文件。格式必须明确为 `--ext=.md` 或 `--ext=.txt`；项目配置若依赖真实文件路径而无法判断应匹配的范围，记为 `Not Run`。

下面是 PowerShell 7 中传递 Markdown 片段的**假设命令**，不是已运行记录。配置与规则仍需先就绪；先按上节设置并核对 `$configPath`。

```powershell
$draft = @'
Read the [installation guide](https://example.com/install).
'@
$previousOutputEncoding = $OutputEncoding
try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $draft | vale --config $configPath --no-global --output=JSON --ext=.md
    $valeExitCode = $LASTEXITCODE
}
finally {
    $OutputEncoding = $previousOutputEncoding
}
```

无法确认宿主或终端的 UTF-8 传递行为时不套用该示例，说明未运行原因。初版纯文本没有 Markdown 的代码、引文和链接作用域；只有确实适用的纯文本规则才能运行。随 Skill 提供的中文、科研和保守原创规则仅覆盖链接文字，因此普通 `.txt` 没有适用规则时记为 `Not Run`，不能把未覆盖当成零问题。

## 5. 可选的中文排版建议

AutoCorrect 不检查语义或一般中文语法。版本、保守配置及规则开关的唯一入口为 [AutoCorrect 配置说明](../skills/text-prison/autocorrect/README.md)，完整调用和诊断约定见 [AutoCorrect 参考](../skills/text-prison/references/autocorrect.md)。选择中文排版建议不授权安装工具；工具未准备好时记录 `Not Run`。

先读取项目已有配置；采用随 Skill 提供的配置时，显式给出实际安装副本的绝对路径。配置路径不存在时，工具可能静默退回默认值，所以存在性和可读性检查是必需前置条件。下面的示意命令只检查已经存在的 Markdown 文件，不改写它：

```powershell
$autoCorrectConfig = Join-Path $skillRoot 'autocorrect/conservative.yml'
$documentPath = 'D:/path/to/your-project/docs/guide.md'
foreach ($inputPath in @($autoCorrectConfig, $documentPath)) {
    if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
        throw "文件不存在：$inputPath"
    }
    Get-Content -LiteralPath $inputPath -Raw -ErrorAction Stop | Out-Null
}
autocorrect --lint --format json --config $autoCorrectConfig $documentPath
$autoCorrectExitCode = $LASTEXITCODE
```

不使用 `--fix`、`init`、目录扫描，也不将 stdout 覆盖回文档。macOS/Linux 使用 `autocorrect --lint --format json --config "$autoCorrectConfig" "$documentPath"`，同样先核对两个绝对路径存在、可读，调用后立即保存 `$?`。

**Markdown 只支持已经存在且获准读取的文件。** 当前维护版本的 stdin 分支按纯文本处理，`--type markdown` 对该分支不生效。因此粘贴的 Markdown、带代码、公式或结构的片段不通过 AutoCorrect stdin 检查，也不为了检查擅自落盘。纯散文 `.txt` 或可靠 UTF-8 stdin 可以按参考文档使用；无法确认是否纯散文时跳过并说明原因。

Markdown 中已关闭围栏代码处理，但这不意味着原样引文、front matter、HTML 和公式获得相同保护。诊断只作用于用户允许修改的正文；无法可靠辨别作用位置时跳过相关提示。项目已有配置不被静默替换，排版建议也不扩大修改范围。

## 6. 理解检查状态

Vale 与 AutoCorrect 分开记录状态。下面的退出码表只适用于 Vale，不能套给 AutoCorrect。

同时查看退出码、stdout、stderr、实际检查对象和规则覆盖。下面的状态只说明机械检查，不能替代原意核对、人工阅读或科研验收。退出码依据 [Vale CLI 官方说明](https://docs.vale.sh/topics/cli)，不是本项目实测记录。

| 实际情况 | 如何记录和处理 |
|---|---|
| CLI 不存在、版本不支持或未确认、必需规则缺失、输入方式不可靠、没有适用规则 | `Not Run`，说明具体原因；保留已经完成的写作工作 |
| 退出码 `0`，输出表明检查正常完成 | `Passed` 仅指工具完成；仍须查看 warning / suggestion，不能据退出码声称无提示 |
| 退出码 `1`，输出表明检查完成且有 error 级提示 | 工具检查完成、有诊断；提示尚待处理不等于工具运行失败 |
| 退出码 `2`、未知退出码、错误对象或无法解释的输出 | `Failed`，报告工具、配置或文档处理错误；不改写为零问题 |
| 检查完成，没有适用诊断 | 只说“所选规则未发现问题”，说明实际覆盖范围 |

默认不使用 `--no-exit`。即使 JSON 能解析，也要判断它是否为按实际输入组织的诊断列表，而不是错误信息。调用前已知缺少规则记 `Not Run`；已经调用后发生资源加载错误则记 `Failed`，不可互相掩盖。

最后交付文档或改动入口，简要说明实质重排、待确认信息、采用的配置和 Vale 状态。项目自有配置的结果不能称为 TextPrison 固定规则集的结果。检查整个文件不意味着全文改写已获授权。

AutoCorrect 的 JSON 分支即使有建议也可能返回 `0`；`count` 表示文件结果数，不是问题数。读取 `messages[].lines` 中的建议，并检查 `error`、stderr、实际输入标识和输出结构。工具缺失、输入不支持或前置配置未就绪记 `Not Run`；实际调用出错、错误字段非空或输出无法解释记 `Failed`；正常完成则分别说明有建议或所选规则未发现建议。不能仅凭退出码 `0` 或 JSON 可解析写成“零问题”。

使用了 AutoCorrect 时一并给出它的状态及配置，不把另一引擎成功当成它通过。本文的命令和假设示例不构成运行证据；安装收尾需按实际文件比对、CLI 输出和环境核对分别报告 `Passed`、`Failed`、`Not Run`。CLI 冒烟通过也不证明宿主自动发现或写作效果已经验证。

## 7. 四个假设写作示例

以下都是文档内的假设输入与预期改写，用于说明选择和保护范围；未运行 Skill、Vale、AutoCorrect 或人工验收，不包含实际诊断数量。

### README：按首次使用者的任务组织

**假设输入：** 一份英文 README 先讲实现原理，再列安装与首个命令；原文已经给出完整命令、前提和故障处理。

**所选方案：** 按读者任务重组，采用英文开发写作规则；允许调整本文件章节，保留全部命令和技术事实。

**预期可观察变化：** 安装前提 → 安装 → 最小用例 → 常见故障 → 实现原理。已有信息重新定位，标题变化先核对锚点与引用；外部文件不在授权内时保留兼容锚点或列出待处理引用。

**必须人工核对：** 操作顺序是否符合软件实际要求，命令是否与支持版本一致，链接能否定位。结构清楚不能证明命令可用。

### 中文操作说明：写清条件和动作

**假设输入：** “完成导出后，如果还要修改，可以再打开它。”已知上下文中“它”指刚导出的配置文件，修改操作是用编辑器打开该文件。

**所选方案：** 局部清晰化，仅消除这一句的指代歧义，不改步骤顺序。

**预期改写：** “导出完成后，如需修改配置，用编辑器打开导出的配置文件。”

**必须人工核对：** 上下文是否确实支持“配置文件”和“编辑器”；若不支持，应询问或保留缺口。中文机械规则覆盖有限，不证明这句的操作条件完整。

### 产品帮助：让链接说明具体行动

**假设输入：** `Click [here](https://example.com/account) to manage your account.` 链接指向管理账户的页面。

**所选方案：** 英文产品帮助的局部清晰化，仅调整链接文字和对应句子，使用产品写作规则。

**预期改写：** `[Manage your account](https://example.com/account).`

**必须人工核对：** 链接目标保持不变，目标页面确实支持账户管理，动作名称与产品界面一致。本例是写作建议，不是已取得 Vale 诊断的复现结果。

### 科研段落：保留结论的适用条件

**假设输入：** “Under the tested conditions, the results suggest that method A may reduce error relative to method B.”

**所选方案：** 科研表达的局部清晰化，保留条件、比较对象和不确定程度，不套用要求消除弱化表达的风格提示。

**预期改写：** “The results suggest that method A may reduce error relative to method B under the tested conditions.” 只调整语序；若原句已足够清楚，也可以保留原句。

**必须人工核对：** 数据是否支持比较、测试条件是什么、误差定义是否明确，以及 `suggest` 和 `may` 是否符合作者的证据强度。Vale 不能确认这些科学判断。
