# 中文支持、GitHub 发布与项目安装计划

日期：2026-10-25。起点：`9f68938`。状态：已完成一次 agy Claude Opus 审阅、修订、实施、GitHub 发布、npx 项目安装和 Vale CLI 核验。AutoCorrect 仅完成可选集成，未安装或运行；结果见第 10 节。

## 1. 目标与授权

根据用户指定的本地中文材料，补充 TextPrison 的中文表达和排版支持，发布到已配置的 GitHub 仓库，再通过 npx 将 Skill 安装到 QCBlender 的项目级 `.agents/skills/text-prison/`，使本机 Vale 可用。输入原件保留在忽略目录，不上传原始对话。

本轮已授权计划、一次 Opus 文档审阅、修订后的实施、本地提交和 GitHub 发布、npx 项目安装以及 Vale 安装与必要的实际可用性核对。此前“不安装、不推送”的限制只属于上一批交付，不阻止本轮明确要求。

AutoCorrect 属于额外本机工具，已另询问是否一并安装。无论答复如何，都可以完成可选集成和文档；未经明确答复不安装该工具。若批准，则补充下载、安装和有限 CLI 核对；否则其实际运行记 `Not Run`。不安装 zhlint，不创建第二套中文引擎。

不恢复 Agent 实战、模型评分、A/B、触发实验或测试框架，不修改 QCBlender 产品代码或文档，不执行 Blender 操作，不替用户选择项目开源许可证。不发布 npm 包；npx 使用已有的 Vercel Skills CLI 获取 GitHub 中的 Skill。

## 2. 已核实的现状与材料取舍

- 仓库已有单一 Skill、五种用途、两种语言指导、六套 Vale 配置和两个原创链接文字规则。Google/Microsoft 包当前只启用少量英文建议。
- 新材料列出的中文规范与排版引擎属于不同层次：微软中文本地化指南是参考文档，不是 `Packages = Microsoft` 的中文规则包；AutoCorrect 是另一个独立工具。
- 已通过 Microsoft 官方目录的重定向地址取得 58 页简体中文指南，阅读第 4–8、11、27–28、35–38、43–44 页。它明确区分软件界面与文档的标点约定，不支持把某一种全角转换作为所有中文输入的硬规则。原 PDF 仅存忽略目录。
- 中文文案排版指北已读取，但其中空格、引号等部分为社区风格选择。科研数字、单位、百分比、公式及已给定产品拼写由领域和项目规则决定，不能机械套用社区示例。
- AutoCorrect v2.16.3 官方 README 提供 `--lint --format json`，也提供会改写文件的 `--fix`；本集成只使用诊断。默认配置包含代码块处理，不能直接采用默认值声称代码已保护。
- 本机 Node.js 为 24.19.0；npm 查询的 Skills CLI 为 1.7.4，要求 Node.js >=22.20.0。QCBlender 当前工作区干净，目标 Skill 不存在，已有其他 Skill 必须保留。
- 已配置远程为 `psiQAQ/text-prison`，当前默认分支 `work/unified-skill-vale` 指向 `934b326`；本地 `main` 已有 `9f68938`。发布时推送 `main` 并使默认入口指向它，保留现存远端分支，不强推。
- `vale` 和 `autocorrect` 当前未在命令搜索路径发现。使用官方 Windows x64 发布二进制无需安装其编译语言工具链。

## 3. 中文写作与检查设计

### 3.1 按需参考

在现有 `references/` 中增加中文本地化与排版摘要，并更新中文规则和索引。提炼已有来源支持的术语一致性、对象和条件、自然表达、信息顺序、标点与混排约定；保留自主改编与来源规则的区别。

只读任务需要的参考，不将中文规范全量灌入主 Skill，不复制微软完整指南或社区长段落，不把英文被动语态、词数和模态限制翻译成中文硬规则。科研段落保留证据强度、否定、适用条件和单位归属。

### 3.2 两个工具各自报告

Vale 继续负责已有显式规则，以及项目已存在的术语规则；没有项目术语表时不生成新词库。中文排版按需使用 AutoCorrect，英文任务不为此调用它。混合文本不全量加载英文品牌规则。

AutoCorrect 初版只将中文与西文/数字间距列为可选 warning 建议，明确关闭代码块处理、拼写替换、全半角转换及其他间距规则。优先顺序是项目明确配置、项目现有文稿的一致写法、Skill 默认建议。只有用户选择排版调整或项目惯例支持时才采纳；其余只报告，残留建议不增加修订轮次。

固定版本 2.16.3 源码已确认 `--config`、`--stdin`、文件的 `--type` 与 JSON 参数；但 stdin 分支硬编码为 `text`，不采用 `--type markdown`。因此 AutoCorrect 的 Markdown 必须是已授权存在的文件；stdin 只用于纯散文，粘贴 Markdown 不为了检查私自落盘。配置是在默认值上合并，因此逐项写明关闭项。显式配置文件不存在时库会退回默认值，必须在调用前验证路径存在且可读。JSON 分支没有依据诊断数量设置非零退出码，不能沿用 Vale 的 0/1/2 语义，也不能用退出 0 声称无建议。未批准安装时只按源码核对，所有运行说法明确为 `Not Run`；源码确认不了的输入不纳入支持范围。

默认尊重项目已有配置；选择随 Skill 分发的保守配置时显式指定其路径。不能静默改写项目根配置或关闭项目规则。若 CLI 不支持可靠的配置隔离、输入格式或保护范围，则缩小可支持输入并说明未运行，不另写 Python 包装引擎。

仅检查 `.md` 和 `.txt` 的明确文件或可可靠传递的 UTF-8 stdin。`.txt` 只用于纯散文，含代码或公式就跳过；Markdown 的原样引文、front matter、HTML 和公式不能假定与围栏代码有相同保护。只处理已授权正文范围，无法可靠区分时跳过相应诊断。AutoCorrect 不使用 `--fix`、裸目录扫描、`init`、CI 或 hooks；stdout 的建议也不能直接覆盖原文。

保留现有“初稿→检查→一次修订→至多一次复查”的总轮次。若同一轮选择两个引擎，各运行至多一次并合并为一轮诊断，不增加两个独立修订循环。只审阅时每个选定引擎最多检查原文一次、只报告。Vale 与 AutoCorrect 分开记录状态，一方缺失则另一方照常处理，缺失方记 `Not Run`，不在后续轮次补跑。

### 3.3 来源与文档同步

更新 Skill、用途路由、安装使用说明、README、设计说明、项目规则与来源索引中“Vale 是唯一机械引擎”的旧表述，改成明确的职责分工。原有 Vale 配置表保持唯一维护入口；新增 AutoCorrect 的配置与调用说明也只维护一份。

原始 ZIP、两份本地输入对话、根 manifest/patch 与五个只读子模块保持不变。历史方案和旧核验记录不改写成新功能已运行的证据。

## 4. 单次 Opus 审阅与修订

先将本计划存入 Git，使用已有 agy 可执行文件和已验证的隔离调用方式，指定 `claude-opus-5-5-high`，一次会话、一个用户回合、最多 300 秒。只发送计划正文和必要约束，不发送原始私密对话、凭据或 QCBlender 源码。

审阅模型不授予工具、网络、子 Agent 或文件修改能力。要求检查中文规则边界、配置与调用假设、已有项目保护、发布入口、npx 安装路径、工具安装及验收。主 Agent 核实意见并记录采纳或不采纳理由，然后直接实施，不再等待一般性确认。

若审阅失败，保留具体错误并诊断；不把失败写成审阅完成，不自动更换模型。若是明确可修复的调用问题，在同一用户授权内修复；模型调用未完成前不绕过审阅进入实施。

## 5. GitHub 发布与 npx 安装

1. 核对待推送的新提交、公开文件、来源归属和凭据/本机私密信息。保留已有远端历史，不删除历史报告或强推清理。只推本轮所需的 `main`；归档标签保留本地。
2. 推送前重新查询远端 `main`：不存在或为本地祖先时才继续，否则停止并报告分叉。将任务分支串行快进合入 `main`，推送后核对远端 SHA；通过已有 GitHub CLI 管理连接设置默认分支为 `main`，再匿名读取公开 Skill。设置失败时如实报告默认入口未完成，不把推送成功等同于全部发布完成。无需额外 GitHub Release 或 npm 发布。
3. 安装前完整检查待安装 Skill 的指令、文件和外部调用范围。当场重新检查 QCBlender 的 Git 状态、既有 `.agents` 路径及锁文件，不沿用计划阶段快照。1.7.4 的 copy 模式会清空同名目标；目标必须不存在，若已存在或出现用户并发修改，先保全并判断，不让非交互安装覆盖未知内容。
4. 固定版源码确认支持完整 40 字符提交 SHA：先尝试 branch clone，随后对 SHA 做定向 fetch。从 QCBlender 根目录执行 `npx --yes skills@1.7.4 add https://github.com/psiQAQ/text-prison/tree/<本轮完整提交SHA>/skills/text-prison --skill text-prison --agent codex --copy --yes`。用实际推送 SHA 替换占位；不要在 `.agents` 内启动，不使用 `--global` 或 `--all`。源码已确认 Codex 的复制目标是项目 `.agents/skills`，不额外安装其他宿主。
5. 临时 npm 缓存放已忽略的任务目录；安装器自身强制创建的系统临时文件由其管理，并记录例外。已在 1.7.4 的 telemetry 源码确认 `DISABLE_TELEMETRY=1` 同时关闭遥测及审计请求；只为该进程设置。项目锁为根目录 `skills-lock.json`，更新时保留其他条目；非交互项目安装不应更新全局安装锁，仍核对相关全局状态是否发生意外变化。
6. **先比对安装副本，再同步包。** 将安装文件与本轮推送的 SHA 文件树按全部相对路径、内容比对，并核对锁中的 `ref` 与哈希；记录已确认的 Git 换行转换差异，不能宽泛忽略内容不同。1.7.4 会保留隐藏配置，但排除 `metadata.json`、`.git`、`__pycache__`、`__pypackages__`；本 Skill 不依赖这些条目。之后单列同步新增的上游目录并保持忽略，不提交包。检查资源自包含、只装一个 Skill、其他已安装 Skill 不变。

QCBlender 的改动限于新 Skill、它的已授权规则包及根 `skills-lock.json`；不提交或推送 QCBlender 仓库，不改其全局指令。若工具另有必需用户级状态写入，检查后记录例外。宿主实际自动触发和写作效果保持 `Not Run`，安装检查不冒充实战验收。

## 6. 本机工具与规则准备

### 6.1 Vale

优先复用符合维护范围的现有安装；若未发现可用版本，则下载官方 Vale 3.25.1 Windows x64 ZIP，核对官方 checksums 或发布资产 SHA-256，检查归档成员后解压到用户级固定版本目录。原件和下载记录放项目忽略目录，不提交二进制。

不安装 Go、Python、Rust 或新增包管理器。只添加该工具目录到用户 PATH：从注册表读取未展开的原值、保留原类型（包括 `REG_EXPAND_SZ`）和原项，不用 `setx`，保留备份。当前过程用绝对路径验证，新的 PowerShell 进程用刷新后的用户/机器 PATH 验证命令发现。报告为“注册表 PATH 已更新，新环境下验证通过”；正在运行的宿主或终端需要重启才能继承，不把手动刷新环境的子进程说成旧宿主已自动刷新。

在 QCBlender 新安装的 Skill 副本中按现有固定 URL 同步 Google、Microsoft 包，不在源码目录或其他 Skill 内同步。记录版本来源与规则布局，检测意外包内配置。无需包的配置不额外同步。

### 6.2 AutoCorrect（安装须单独答复）

若用户批准，采用 v2.16.3 官方 Windows x64 ZIP，核对发布资产摘要，安装到独立用户级版本目录并按 Vale 的相同原则处理 PATH。否则仅交付自包含配置和调用说明，明确本机中文排版诊断未执行。

## 7. 验收与交付

| 范围 | 必要证据 |
|---|---|
| 计划审阅 | Opus 模型、输入提交、完成状态、意见处理；私密原始日志不上传 |
| 文件质量 | 当前 YAML/INI/JSON、引用、安装器逻辑、来源和 `git diff --check`；不恢复测试框架 |
| GitHub 发布 | 本地与远端 main SHA 一致、默认分支为 main、匿名读取的 Skill 与该提交一致 |
| npx 安装 | 实际退出状态、目标路径、包同步前安装文件与推送 SHA 文件树核对、锁 ref/哈希、原 Skill 和锁记录保留 |
| Vale 可用 | 实际路径与版本、新进程命令发现、六套配置能加载；用一次性受控片段核对中英文链接诊断和受保护代码范围，不改真实文档 |
| AutoCorrect 可用 | 仅批准安装时核对版本、配置、JSON 诊断、正常/有建议/错误状态及代码保护；不自动改写，不宣称完整中文语法检查 |
| AutoCorrect 未批准安装 | 固定版源码支持所列命令和键名、配置自包含、文档明确 Not Run；本轮不尝试安装或执行该工具 |
| 保全与收尾 | 原始输入哈希、子模块提交及 QCBlender 无关内容不变；本地归档任务分支 |

临时受控片段只用于安装和 CLI 集成冒烟，不保存为测试套件，不调用 Skill 进行实战。状态按 `Passed`、`Failed`、`Not Run` 分项记录。公开文档只存版本和必要结果，机器绝对路径与详细安装收据留本地。最终给出计划、发布地址、安装位置、工具版本及未完成项。

## 8. 已查阅来源

- [Microsoft 本地化指南目录](https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides)及[官方简体中文 PDF](https://download.microsoft.com/download/1/5/9/159cb91c-b61b-4385-97ca-80ccc7ff1fa0/zho-chn-StyleGuide.pdf)：已阅读范围见第 2 节，原件 SHA-256 为 `dd154a01c2838fae76dca06d5d4e9c99ec72e77c9a2cc7c456ff62af740e438d`。
- [中文文案排版指北](https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.zh-Hans.md)：排版习惯及其中明确列出的例外、争议项。
- [AutoCorrect v2.16.3 README](https://github.com/huacnlee/autocorrect/blob/v2.16.3/README.md)及[发布资产](https://github.com/huacnlee/autocorrect/releases/tag/v2.16.3)：工具职责、lint 与默认代码块设置；CLI 细节实施前继续核实。
- [Vercel Skills CLI](https://github.com/vercel-labs/skills)与[命令说明](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)：npx 来源、项目安装、按 Skill/宿主选择和复制方式；实际调用固定 1.7.4。
- [Codex Skill 发现规则](https://learn.chatgpt.com/docs/build-skills)：项目 `.agents/skills` 和自动发现边界。
- [Vale 3.25.1 发布页](https://github.com/vale-cli/vale/releases/tag/v3.25.1)：官方 Windows 二进制和校验资产；既有规则依据仍见随 Skill 分发的 Vale 目录。

## 9. 单次 Opus 审阅处理记录

输入为计划初稿提交 `d134875dcd276945370fe8aeac2be70fffc7f9f4`。agy 使用 `claude-opus-5-5-high`、high effort；一次会话、一个用户回合，133.63 秒完成，退出码 0，终态 `SUCCESS`，工具尝试为 0。审阅原文与调用收据保存在忽略的 `.local/plan-review/opus-zh-publish-20261025/`，不纳入发布。

| 意见 | 处理 |
|---|---|
| P1-1：把社区间距偏好写成必要规则 | 采纳，改为可选 warning；项目配置和既有一致写法优先，只在相应编辑授权内采用 |
| P1-2：未安装 AutoCorrect 时的依据和边界不明 | 采纳，已读固定源码；未安装就只声明源码核对，关闭项显式列出，纯文本仅支持纯散文，分列 Not Run。补查发现 stdin 不采用 Markdown 类型，已明确收窄 |
| P1-3：安装未绑定发布 SHA，默认分支缺少门禁 | 采纳，核对远端祖先关系，管理连接设置 main；固定版支持完整 SHA，采用 SHA URL 并核对文件树和锁记录 |
| P2-1：同步包和安装比对次序冲突 | 采纳，先核对发布文件，再同步并单列生成目录 |
| P2-2：npx 路径、覆盖、锁和遥测未明 | 采纳，核对 1.7.4 实现；目标不存在才安装，保留项目锁其他条目，记录可能用户级写入 |
| P2-3：旧宿主看不到新 PATH | 采纳，保留注册表原始值与类型，区分新环境验证与旧宿主重启 |
| P2-4：只审阅与单引擎缺失口径 | 采纳，分别报告，不修改、不为缺失工具追加轮次 |
| P2-5：安装前状态可能已变化 | 采纳，安装前即时复核状态和路径 |

主 Agent 对上述 CLI 事实补读固定版本源码；这不是第二次模型审阅，也不是运行验收。新增来源和实际执行结果随实施记录，不将本次文档审阅当成产品质量认证。

## 10. 执行结果（2026-10-25）

实现与安装固定提交为 `fcf06ce9579eca380ac87b9d8a32dfe9b6ba7f72`；本节是其后的交付记录，未更改 Skill 文件树。仓库公开入口为 [psiQAQ/text-prison](https://github.com/psiQAQ/text-prison)，默认分支为 `main`。SSH 代理命令在当前 shell 下失败，发布改用同一仓库的 HTTPS 与已有 GitHub CLI 凭据连接；没有修改 remote 或 SSH 配置。

| 项目 | 状态与实际证据 |
|---|---|
| Opus 计划审阅 | **Passed**：一次调用完成，意见处理见第 9 节 |
| 静态核对 | **Passed**：29 个发布 Skill 文件、82 个本地引用、YAML/INI/JSON 和安装器语法检查；`git diff --check` 通过 |
| GitHub 发布 | **Passed**：发布提交与远端一致，默认分支为 main；匿名读取 SKILL.md 与提交内字节一致 |
| npx 项目安装 | **Passed**：Skills CLI 1.7.4、固定完整 SHA、Codex 项目复制模式；29 个文件全部核对，26 个字节一致、3 个仅为 Git 的 CRLF 转换；锁中的 ref 与 computedHash 均核对通过 |
| QCBlender 保全 | **Passed**：原有 43 个 Skill 的 154 个文件及 43 条锁记录未变；只新增 TextPrison 和同步规则包、合并根锁，不提交或推送目标项目 |
| Vale 本机安装 | **Passed**：官方 3.25.1 Windows x64 ZIP 与 checksums 校验通过；绝对路径运行及刷新环境后的 Windows PowerShell / PowerShell 7 命令发现通过。用户 PATH 保留原条目与 REG_EXPAND_SZ 类型；旧宿主未自动刷新，需重启 |
| 规则包 | **Passed**：Google v0.7.1 与 Microsoft v0.15.1 均通过官方发布资产 SHA-256 核对；分别比对 38、48 个解压文件，并核对各自三个启用规则与固定标签源码一致；没有包内共享配置 |
| 六套配置 | **Passed**：安装副本实际运行，退出码均为 0；受控 Markdown 分别产生 2/4/4/4/1/1 条预期范围内建议，代码与引用块中的相同文字未被报告。该结果证明诊断可用，不表示输入零问题 |
| 原始材料 | **Passed**：六份原始输入哈希及五个子模块提交保持不变 |
| AutoCorrect | **Not Run**：固定版源码和保守配置已核对；额外本机安装未获答复，未下载或执行二进制 |
| 宿主触发、Agent 实战与写作效果 | **Not Run**：不在本轮执行范围；没有创建或运行测试框架 |

六套配置的结果顺序为 conservative、dev-en、procedure-en、product-en、research-en、zh。包摘要分别为 Google `4b67fca1f2a88595b2a578ab98bbf3017a23af677b04f93e862843f3ea1a9a0b`、Microsoft `0b37660b244a9399d7f10225895773291d27b2967ed0d239a1d379b633e8cd16`。安装文件比对在同步包前完成；同步后再次确认这 29 个源文件未变，生成目录按随 Skill 分发的规则被忽略。

完整机器路径、PATH 备份、下载原件、命令输出及逐文件摘要保留在忽略目录 `.local/deployment-20261025/`。npx 缓存也在该目录；安装器自行管理的系统临时克隆是其既定行为，没有用它存放手动中间产物。没有升级 npm 或修改全局 Skill 锁。
