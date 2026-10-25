# 在写作任务中使用 AutoCorrect

仅在已选范围需要中文排版建议且允许运行命令时使用。它不检查语义，也不替代 Vale。版本、规则及输入限制的唯一清单见 [配置目录](../autocorrect/README.md)。

## 调用前

1. 确认可执行文件和版本。不存在、版本未核对或用户只要文字指导时不运行，不安装或调用下载器。
2. 先读项目配置和文稿惯例。默认用项目 `.autocorrectrc` 的绝对路径；选择 Skill 保守配置时，从当前已安装 Skill 目录解析 `autocorrect/conservative.yml`，不依赖源码仓库。
3. 确认配置实际存在且可读，确认输入为可读文件并在授权范围内。文件模式从项目根启动，核对 `.gitignore`、`.autocorrectignore` 和原文开关注释；忽略导致未覆盖时报告，不改配置绕过它。
4. Markdown 使用已有文件；纯散文才允许 `.txt` 或可靠的 UTF-8 stdin。stdin 不支持 Markdown 保护，不能用 `--type markdown` 补救。没有合适文件时跳过，不为检查私自保存片段。
5. 识别代码、公式、原样引文、front matter、HTML 和标识符等保护范围。纯文本含代码/公式时跳过；Markdown 若无法可靠区分候选提示是否在可编辑正文，也跳过。

## 命令

以下变量均须指向已核对的绝对路径，工作目录为当前项目根：

```powershell
autocorrect --lint --format json --config $autoCorrectConfig $documentPath
$autoCorrectExitCode = $LASTEXITCODE
```

纯散文可在宿主确保 UTF-8 管道后使用：

```powershell
$draft | autocorrect --lint --format json --config $autoCorrectConfig --stdin
$autoCorrectExitCode = $LASTEXITCODE
```

不要将上述变量或片段直接拼成未转义的 shell 文本；使用正常参数传递。保留 stdout 和 stderr，禁止 `--fix`、裸目录、`init`、`update` 及自动修改原文开关注释。

## 解释与修订

- 退出 `0` 仍可能有建议。读取 `messages[].lines` 的位置和原文/候选文本，以及 `messages[].error`；`count` 不是提示总数。
- 非零退出、错误字段、读取错误、损坏或无法对应输入的输出记 `Failed`，不把局部可解析 JSON 当作完整成功。该工具的状态不能套用 Vale 的 0/1/2 约定。
- 零消息时先核对文件确实在本次覆盖范围，未处理或忽略不能记为通过；只说明所选规则没有报告可适用的问题，不给中文质量总分。
- 工具建议只在排版授权或项目惯例支持时采纳。只改某节或术语的请求不因此扩成全文空格统一；不要把 `new` 整行覆盖到含代码或其他保护内容的原文。

与 Vale 同时选择时，每轮各调用一次，共用一次修订和至多一次复查。只审阅时只报告。缺失的引擎记 `Not Run`，另一方继续，不追加等待补跑。未采纳或残留建议可保留并简述理由。
