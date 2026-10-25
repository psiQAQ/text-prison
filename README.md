# TextPrison / 文字狱

一个中英文写作 Skill，按任务读取规则，保留技术含义，并按需使用 Vale 和 AutoCorrect 提供诊断。

## 当前可用范围

统一 Skill 包含五种用途指导、中英文参考、六套 Vale 配置及可选的中文排版配置。中文规则区分产品本地化、社区排版偏好和科研表达，不能把英文风格包当成完整中文规范。

文字指导无需运行依赖。[Vale](skills/text-prison/vale/README.md)处理显式风格、术语和链接规则；[AutoCorrect](skills/text-prison/autocorrect/README.md)可选地提供中文间距建议。项目惯例和用户范围优先，缺少某个工具时说明该项未运行，不自动下载。工具完成不证明语义或写作效果。

## 安装与使用

先读 [安装说明](docs/INSTALL.md)，选择目标项目及宿主，再按 [使用说明](docs/USAGE.md) 指定文档和修改范围。可使用 npx 从 GitHub 安装，也保留 Python 标准库安装器。

在目标项目根目录运行以下命令；先确认 `.agents/skills/text-prison` 不存在，已有副本按安装说明保全后更新：

```powershell
npx --yes skills@1.7.4 add psiQAQ/text-prison --skill text-prison --agent codex --copy --yes
```

宿主路径、固定提交安装及调用方式见安装说明。npx 路线使用 Vercel Skills CLI 并写入项目 `skills-lock.json`，可能覆盖同名目录；Python 路线拒绝覆盖并生成 `install-manifest.json`。安装 Skill 不会同时安装检查工具。仓库只维护 [skills/text-prison](skills/text-prison/SKILL.md) 这一份源文件。

Skill 在有实质取舍时提出 2–3 个适用选项并给出推荐；动作和对象已明确的局部改写直接处理。规则按用途、语言和写作风格读取。两个工具若同时使用，每轮各调用一次，共用至多一次修订和一次复查；只审阅时不改写。

相关文档请求仍可由宿主自动发现 Skill，是否触发取决于宿主。当前不提供自动触发、理解效果或成本改善的实测保证。

## 保留资料

- [当前设计范围](docs/DESIGN.md)：任务流程、职责和限制。
- [已批准实施方案](docs/plans/text-prison-vale.md)：设计依据和单次 Opus 审阅记录。
- [中文支持与发布安装计划](docs/plans/chinese-publish-install.md)：本轮方案、Opus 意见及处理。
- [来源目录](docs/RELATED_WORK.md)及 [机器来源索引](sources.json)：规范、参考实现和此前的来源核验范围。
- [归属说明](NOTICE.md)：第三方资料与许可边界。

五个上游子模块保持固定版本，仅作只读参考，不安装、不执行。原始 ZIP、根 `MANIFEST.sha256.json` 与 `DOCS_PATCH.md` 保留原包的历史含义，不代表当前功能或验证状态。

本仓库不再运行或维护 Agent 实战、模型评委、A/B 实验、测试套件或评审网页。原提交和归档标签保留在 Git 历史中；已删除的忽略目录原始数据没有另行备份。

## 使用边界

保留事实、条件、权限、数字、单位、引用和不确定性。规则借鉴不等于完整 ASD-STE100 认证，也不证明语义正确。代码、命令、标识符和原样引文按用户要求保护，不为文风统一擅自修改。

不做观点审查，不以规避 AI 文本检测为目标，不自动安装工具或修改全局指令。
