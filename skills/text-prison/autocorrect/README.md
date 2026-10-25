# AutoCorrect 中文排版配置

AutoCorrect 是可选排版引擎，Vale 继续负责其显式风格、术语和链接规则。缺少 AutoCorrect 不影响写作指导或 Vale；不能把 Vale 的结果当作中文排版检查。

## 固定版本与规则

本目录的配置依据 **AutoCorrect 2.16.3**。其他版本先核对规则和 CLI 行为，不假定新增默认规则已被关闭，也不自动升级。发布二进制可直接运行，无需 Rust、Python 或 Node；使用 npm 版才需要 Node，且 npm 包名为 `autocorrect-node`，不是同名 Python 包。

[conservative.yml](conservative.yml)只将 `space-word` 设为 `2`（warning）：提出 CJK 与西文/数字的间距建议。`space-punctuation`、`space-bracket`、`space-backticks`、`space-dash`、`space-dollar`、`fullwidth`、`no-space-fullwidth`、`no-space-fullwidth-quote`、`halfwidth-word`、`halfwidth-punctuation`、`spellcheck` 均设为 `0`；`context.codeblock` 也设为 `0`。

该版本把用户配置合并到内置默认值，因此关闭项不能只省略。项目已有配置默认优先；用户选择本配置时才显式指定它，不把两份配置暗中拼接，也不改项目根 `.autocorrectrc`。即使本配置有建议，项目已采用的写法和编辑授权仍决定是否修改。

## 输入与保护范围

| 输入 | 本 Skill 的处理 |
|---|---|
| 已存在且可读的 `.md` 文件 | 可用文件输入；围栏代码关闭处理，逐项排除原样引文、front matter、HTML、公式等受保护内容 |
| `.txt` 文件或 UTF-8 stdin | 只用于纯散文；含代码、公式或结构标记时不运行 |
| 粘贴的 Markdown | 不用 AutoCorrect stdin 检查；需要已有、获准写入的文件，否则记 `Not Run`，Vale 的适用 stdin 路径仍可单独使用 |
| 其他格式或目录 | 不在初版范围，不扫描或转换 |

2.16.3 的 stdin 分支硬编码使用 `text`，即使附带 `--type markdown` 也不会启用 Markdown 保护。文件输入才采用相应格式。Markdown 的引文、元数据与 HTML 文本并非全部自动排除；无法可靠判断提示是否属于可编辑正文时，跳过此工具并说明缺口。不要往原文插入忽略注释来隐藏提示。

文件模式仍受当前项目的 `.gitignore` 和 `.autocorrectignore` 影响。显式 `--config` 选择配置，不取消忽略规则；不改用 stdin 绕过文件忽略。空结果不能单凭自身证明文件已处理。

## 调用和状态

完整流程见 [调用说明](../references/autocorrect.md)。只使用 `--lint --format json`，不使用 `--fix`、`init` 或 `update`。配置和输入路径都必须先验证存在、可读：缺失的配置在该版本可能退回内置默认值，不能依赖 CLI 报错。

JSON 格式为 `count` 与 `messages`，各消息包含 `filepath`、`lines`、`error`；各行含位置、原文、建议文字和 `severity`。`count` 是文件结果条数，不是提示总数。JSON 分支可能在有 error/warning 级建议时仍退出 `0`；无建议应同时核对输入、覆盖范围、输出结构与错误信息。Vale 的退出码表不适用于此工具。

配置解析、读取、输入处理或输出异常记 `Failed`；前置项不满足或覆盖不可靠记 `Not Run`。工具完成只说明已取得相应诊断，不能证明中文语法、科学含义或术语完整。

## 来源与维护

2026-10-25 已读取固定 v2.16.3 的以下文件；源码核对与本机运行分别记录，不能由本目录存在推定工具已安装：

- [CLI 参数](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect-cli/src/cli.rs)及[执行分支](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect-cli/src/lib.rs)。
- [默认配置](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect/.autocorrectrc.default)、[配置合并](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect/src/config/mod.rs)、[JSON 输出](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect/src/result/json.rs)。
- [Markdown 处理源码](https://github.com/huacnlee/autocorrect/blob/v2.16.3/autocorrect/src/code/markdown.rs)和[发布页](https://github.com/huacnlee/autocorrect/releases/tag/v2.16.3)。

这里只分发原创配置与说明，不附第三方二进制或完整中文规范。不引入 zhlint、自研排版包装器、CI 或自动修复循环；规则更新需要重新核对固定版本及用户授权。
