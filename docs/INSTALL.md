# 安装和维护 TextPrison

TextPrison 的写作指导无需运行时依赖。Vale 提供已选规则的机械诊断；AutoCorrect 是可选的中文排版建议工具，两者分别安装。本文提供安装步骤；实际安装、配置加载和宿主调用状态需要按当时执行结果核对。

## 1. 选择安装范围与途径

希望只在一个项目中使用，选择项目安装；希望当前用户在多个项目中使用，选择全局安装。两种范围都只安装 Skill，Vale、AutoCorrect 分别按需准备。

| 安装途径 | 支持范围 | 前提 | 已有同名目标 |
|---|---|---|---|
| npx 从 GitHub 获取 | 项目、全局 | 符合 Skills CLI 要求的 Node.js/npm，可访问来源 | 可能覆盖，先检查并保全 |
| 本仓库 Python 安装器 | 项目 | Python 3.10+，本地已有仓库 | 拒绝覆盖 |

安装不同时设置 hooks、MCP 或全局指令，也不证明宿主已加载 Skill。

### 从 GitHub 安装：npx

使用 [Vercel Skills CLI](https://github.com/vercel-labs/skills)，以下命令不固定 CLI 版本。先确认已有 Node.js/npm 满足其当前要求，并允许下载 CLI、读取来源及写入所选安装范围。npx 可能先询问是否下载 `skills` 包；随后按 CLI 当前提示选择宿主和安装方式。本项目不发布同名 npm 包。

**npx 能覆盖同名安装。** 项目安装前检查 Git 状态、目标 Skill 和根目录 `skills-lock.json`；全局安装前检查所选宿主的用户目录及已有安装记录。两者均需识别链接实际指向的位置。目标已有内容时先按[更新流程](#4-更新时保全旧副本)保全，不把交互确认当作内容备份。

项目安装：在已有目标项目的根目录运行，不要进入宿主的 Skill 子目录后执行。PowerShell 示例：

```powershell
$projectRoot = 'D:/path/to/your-project'
Set-Location -LiteralPath $projectRoot
npx skills add psiQAQ/text-prison
```

全局安装：在普通工作目录运行下面这一条，不再执行上面的项目安装命令：

```powershell
npx skills add psiQAQ/text-prison --global
```

按需选择一种范围即可。CLI 支持将宿主目录链接到公共副本，也支持独立复制；链接会共享实际文件，独立复制则分别维护。选择前核对它将写入哪些宿主，安装后记录实际目标、方式、退出状态和锁记录，并确认其他 Skill 未变。项目安装的 `skills-lock.json` 与全局安装状态应分别核对，不把项目锁路径套到全局范围；npx 不生成本项目 Python 安装器的 `install-manifest.json`。

以下是 2026-10-25 对 [CLI 命令说明](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)及[宿主路径表](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)的文档核对，列出安装容器路径，实际 Skill 名称为 `text-prison`。这不是未固定版本 CLI 的新安装实测；具体目标以当前 CLI 预览和安装结果为准。此前 CLI 1.7.4 的项目复制实测单独保留在[安装交付记录](plans/chinese-publish-install.md#10-首次交付结果2026-10-25)。

| npx 宿主 | 项目路径 | 全局路径 |
|---|---|---|
| Codex | `.agents/skills/text-prison/` | `~/.agents/skills/text-prison/` |
| Claude Code | `.claude/skills/text-prison/` | `~/.claude/skills/text-prison/` |
| Pi | `.agents/skills/text-prison/` | `~/.agents/skills/text-prison/` |

`~` 表示当前用户主目录。尤其注意 npx 的 Pi 路径与下方 Python 安装器不同。链接可能将这些路径指向公共副本，不能仅凭表格认定内容独立。

仓库简写跟随默认分支。需要精确复现时，取得发布的完整提交 SHA，并采用当前 CLI 支持的 GitHub tree 来源，例如 `https://github.com/psiQAQ/text-prison/tree/<完整40字符SHA>/skills/text-prison`。该形式已在此前 1.7.4 安装中验证，使用其他 CLI 版本时仍需核对实际解析的提交；不要把占位文字原样执行，也不要在一次安装后重复安装另一种来源。

**先比对安装文件，再同步 Vale 包。** 对照所选发布 SHA 的 Skill 文件树，核对全部相对路径、内容和锁中的 ref/哈希；明确记录 Git 换行转换，不能宽泛忽略差异。之后再同步必要规则，将新增包目录单独记录。安装器的缓存或系统临时文件不属于 Skill 内容。此前实测的 CLI 1.7.4 支持进程级 `DISABLE_TELEMETRY=1`；如需限制其他版本的遥测，先核对该版本说明，不将历史结论泛化，也不写入全局环境。

### 从本地仓库安装：Python

前提是已有 Python 3.10 或以上版本、目标项目已存在且取得写入授权。此安装器只使用标准库，不会安装 Python 包，也不修改全局配置。

以下主线使用 Windows PowerShell。将两个示意绝对路径换成实际路径，在 TextPrison 仓库根目录操作：

```powershell
$repositoryRoot = 'D:/path/to/text-prison'
$projectRoot = 'D:/path/to/your-project'
Set-Location -LiteralPath $repositoryRoot
python tools/install_skill.py --agent codex --project $projectRoot
```

只执行所需宿主的一次安装命令；上例选择 Codex，其他宿主替换 `--agent` 参数。下面的位置相对于 `$projectRoot`，仅描述 Python 安装器；显式调用语法同样可用于 npx 安装的 Skill。

| 宿主 | Python 安装器 `--agent` 参数 | 项目内安装位置 | 在宿主对话中显式调用 |
|---|---|---|---|
| Codex | `codex` | `.agents/skills/text-prison/` | `$text-prison` |
| Claude Code | `claude` | `.claude/skills/text-prison/` | `/text-prison` |
| Pi | `pi` | `.pi/skills/text-prison/` | `/skill:text-prison` |
| Codex 与 Claude Code | `both` | 上述 Codex、Claude Code 两个独立目录 | 分别使用对应调用方式 |

Python 安装器的 `both` 不包含 Pi。它在复制前检查两个目标；任一目标已存在都会拒绝安装，不以覆盖方式修复。它也拒绝经过符号链接或 Windows reparse point 的安装子路径。这些拒绝覆盖行为不能套用于上面的 npx 路线。

正常完成时，安装器返回退出码 `0`，打印安装目录，并在每个副本中生成逐文件 SHA-256 的 `install-manifest.json`。这表明复制操作完成；宿主能否发现、加载和执行 Skill 仍需在之后获准的实际使用中确认。若提示目标项目不存在，检查 `$projectRoot`；若提示拒绝覆盖，转到[更新流程](#4-更新时保全旧副本)，不要删除原目录再盲目重试。若复制中途失败，先核对报错与已经写入的文件，保留现场，不把残留目录视为成功安装。

Python 安装副本含 Skill、用途和语言规则、品牌摘要、Vale 配置及原创规则、AutoCorrect 配置和说明。它不含仓库子模块、原始 ZIP、研究记录，也不复制源目录中已同步的 `vale/styles/Google/`、`vale/styles/Microsoft/`、`vale/styles/.vale-config/`。其余内容不能仅因处于 `styles/` 就被当作可删除缓存。安装前应检查源 Skill 是否含不应分发的定制或私密材料。

## 2. 按需安装 Vale

只使用写作指导时跳过本节和下一节。机械诊断需要独立 CLI；只有明确授权时才安装，Agent 不会因发现工具缺失而自动下载。Vale 的官方 Windows 发布二进制不需要 Go、Python 或 Node.js；Node.js 是上面 npx 安装途径的要求，不是 Vale 的要求。

先阅读随 Skill 分发的 [Vale 配置、版本与规则说明](../skills/text-prison/vale/README.md)。其中维护 CLI 支持范围、固定包版本和启用规则；本文不另存一份版本表。支持范围是维护选择，不能视为本机实测兼容记录。

Windows 可按 [Vale 官方安装说明](https://docs.vale.sh/topics/installation) 使用 winget：

```powershell
winget install -e --id errata-ai.Vale
```

也可以从 [Vale 官方发布页](https://github.com/vale-cli/vale/releases) 手动选择符合维护范围、匹配本机系统和架构的发布包。核对官方 checksums 或发布资产 SHA-256，检查归档成员，再解压到用户级的独立版本目录。先用可执行文件绝对路径调用；只有明确授权时才另行修改用户 PATH。选择发布包前核对版本，不能把包管理器当前提供的版本默认为支持范围内。

修改 PATH 前备份未展开的原值、注册表值类型和已有条目，保留 `REG_EXPAND_SZ` 等原类型，只增加已确认的工具目录，不使用 `setx` 覆写。更新注册表后可以在刷新环境的新 PowerShell 进程中核对命令发现；这不表示正在运行的宿主或终端自动刷新，仍需重启它们才能继承新环境。

安装后在可找到 Vale 的 PowerShell 中执行：

```powershell
vale --version
```

若采用绝对路径安装，使用 `& '实际绝对路径/vale.exe' --version`。找不到命令时核对安装位置或重新打开终端，不自动重复安装。版本不在维护范围、版本无法确认时，机械检查记为 `Not Run`，先决定是否调整安装版本。版本输出只证明程序能启动，不证明配置加载或诊断有效。

### 可选：准备 AutoCorrect

中文排版建议使用独立的 AutoCorrect CLI。版本、规则开关和输入限制统一维护在 [AutoCorrect 配置说明](../skills/text-prison/autocorrect/README.md)，不与 Vale 的包同步混用。未批准安装时只使用中文写作参考，并把 AutoCorrect 记为 `Not Run`；不能由“支持中文”推断已经安装或运行它。

获准后按上述权威入口取得官方系统和架构匹配的发布二进制，核对资产摘要，放入独立用户级版本目录。若需要 PATH，沿用 Vale 的保全原则。用 `autocorrect --version` 核对实际程序，再按[使用说明](USAGE.md#5-可选的中文排版建议)确认配置、输入和诊断；版本输出同样不证明排版规则已正确加载。安装不授权 `--fix` 或修改项目配置。

## 3. 选择配置并准备所需规则

先检查目标项目是否已有 Vale 配置。日常使用默认采用项目配置并保留它；只有没有项目配置，或用户已经选择随 Skill 提供的规则时，才采用 Skill 配置。切换配置的影响合并到写作方案选择中，不另外反复询问。项目配置需要的资源按该项目规定处理，不能照抄本节同步命令替代它。

配置选择、所需包和是否同步见 [Vale 配置说明](../skills/text-prison/vale/README.md)。以下仅演示已选英文开发配置的情况，所有路径都指向已安装副本，而不是仓库源目录：

```powershell
$skillRoot = Join-Path $projectRoot '.agents/skills/text-prison'
$configPath = Join-Path $skillRoot 'vale/dev-en.ini'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "配置不存在：$configPath"
}
```

其他宿主或全局安装根据[安装路径表](#1-选择安装范围与途径)设置 `$skillRoot`，并核对实际链接目标。确认所选配置确实需要包且尚未准备好，并获得同步授权后，才执行：

```powershell
vale sync --config $configPath --no-global
```

同步会联网下载所选配置声明的固定包，并写入该副本的 `vale/styles/`；它可能替换同名上游资源，重建 `.vale-config/`。同步前保全已有定制，不把定制放入上游包目录。无需包的配置不执行 `sync`，已有可确认的共享包也不重复同步。包布局、版本和维护限制以 [Vale 配置说明](../skills/text-prison/vale/README.md)为准。

同步后核对所选配置实际启用的规则文件及版本来源，记录配置、包版本、同步时间和输出。只有目录存在不足以证明包完整或版本正确。若发现下载失败、规则缺失或版本未确认，保留具体原因，不继续宣称“规则就绪”。若新包出现包内 `.vale.ini`、嵌套依赖或共享配置，先检查是否影响其他配置，不按原假设继续更新。

Skill 内的 `vale/styles/.gitignore` 精确忽略上述生成目录，不改写目标项目根 `.gitignore`。需要将上游包纳入项目 Git 的用户应自行决定如何调整。未知目录和本地定制不属于自动清理对象。

接下来按[使用说明](USAGE.md)指定一个实际文档，不默认检查整个项目。此处没有自动试运行步骤。

## 4. 更新时保全旧副本

Python 安装器拒绝覆盖；npx 能覆盖同名安装。两种途径都按以下顺序保全后更新，先区分项目/全局范围，以及独立复制/共享链接：

1. Python 副本对照 `install-manifest.json`；npx 项目安装对照项目根 `skills-lock.json`，全局安装对照 CLI 实际维护的安装记录，均结合对应发布文件树。识别本地修改、后来同步的包和新增文件，不把未列出的文件自动判为垃圾。保全相关安装记录及其他 Skill，不能用只含 TextPrison 的锁替换原锁。
2. 明确旧副本的保留绝对路径、新副本的安装范围及用户定制，取得这次替换操作的授权。
3. 将完整旧副本保全到用户选定位置，确认配置、术语材料和未知文件均有保留，再腾出已批准的安装目标。遇到占用或权限问题时停止处理该路径，不强制删除或改 ACL。
4. 按第 1 节所选途径安装新副本；先与发布文件核对，再人工比较并合并仍适用的定制，不整目录覆盖回去。npx 更新须保留其他锁条目及其他 Skill，不顺带安装其他宿主。
5. 核对新配置的包来源、版本和布局；只有另行授权后才同步所需包。固定版本升级属于依赖变更，不在日常写作时自动执行。
6. 保留旧副本，直到用户确认新副本可用并批准清理。共享链接还需核对其他宿主是否指向同一份内容，避免更新或移动公共副本时影响它们。文档交付、复制完成或版本输出都不能替代这个确认。

Python 安装器和 npx 的复制方式生成独立、自包含的副本，修改一份不会更新另一份。若 Python `both` 的两份副本都需要英文包，就分别准备。npx 选择链接方式时，先解析实际目标；多个宿主指向同一份内容时只维护该份资源，不重复同步。共享全局副本的修改可能影响多个项目，因此先确认使用者与作用范围。

项目术语以项目已有词汇配置或术语文档为单一来源。没有这类材料时由写作 Agent 标出缺口，需用户确认的术语单独列出，不在每份 Skill 副本中生成一套术语库。

## 5. macOS / Linux 差异

总体顺序与 Windows 相同：安装 Skill → 按需安装 CLI → 核对版本 → 按需同步 → 明确指定文档。npx 主线命令也相同；项目安装先进入目标项目根目录，确认已有目标已按需保全：

```bash
projectRoot='/absolute/path/to/your-project'
cd "$projectRoot"
npx skills add psiQAQ/text-prison
```

若选择全局范围，则在普通工作目录执行 `npx skills add psiQAQ/text-prison --global`，不再同时执行项目安装命令。

选择 Python 路线时，Python 命令和 shell 变量写法不同；例如从仓库根目录安装 Codex 副本：

```bash
repositoryRoot='/absolute/path/to/text-prison'
projectRoot='/absolute/path/to/your-project'
cd "$repositoryRoot"
python3 tools/install_skill.py --agent codex --project "$projectRoot"
skillRoot="$projectRoot/.agents/skills/text-prison"
configPath="$skillRoot/vale/dev-en.ini"
```

按 [Vale 官方安装说明](https://docs.vale.sh/topics/installation)选择系统适用的包管理器，或从官方发布页选用系统和架构匹配的发布包；同样先确认授权及维护版本范围，不把 Linux 通用包管理器命令当作所有发行版都适用。

版本与同步命令分别为 `vale --version` 和 `vale sync --config "$configPath" --no-global`。同步仍只用于已经选定且需要包的配置；两种安装途径的覆盖差异、多宿主维护和保全旧副本的要求不变。AutoCorrect 按其配置说明选择系统对应发布包，不运行 Vale 的包同步。
