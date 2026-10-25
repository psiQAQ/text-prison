# TextPrison / 文字狱

一个中英文写作 Skill，按文档用途选用规则，在保留技术含义的前提下改善表达，并按需调用 Vale 和 AutoCorrect 检查。

## 当前可用范围

Skill 包含五种文档用途的指导、中英文参考、六套 Vale 配置和可选的中文排版配置。中文指导分别说明产品本地化、社区排版偏好和科研表达的适用范围；英文风格包不提供完整中文规范。

只使用文字指导时，无需安装额外工具。[Vale](skills/text-prison/vale/README.md)按所选规则检查风格、术语和链接；[AutoCorrect](skills/text-prison/autocorrect/README.md)提供可选的中文间距建议。是否采纳提示，以项目惯例和用户授权的修改范围为准。缺少工具时说明该项未运行，不自动下载；检查完成也不代表语义正确或写作效果已得到验证。

## 安装与使用

先读 [安装说明](docs/INSTALL.md)，选择目标项目和宿主，再按 [使用说明](docs/USAGE.md) 指定要处理的文档及修改范围。可通过 npx 从 GitHub 安装；已有本地仓库时，也可使用 Python 标准库安装器。

以下命令从目标项目根目录安装 Skill，供 Codex 使用。npx 可能覆盖同名目录，运行前须确认 `.agents/skills/text-prison` 不存在；若已有副本，先按安装说明保全，再更新：

```powershell
npx --yes skills@1.7.4 add psiQAQ/text-prison --skill text-prison --agent codex --copy --yes
```

其他宿主的安装路径、固定提交安装方法及调用方式见安装说明。npx 使用 Vercel Skills CLI，并写入项目 `skills-lock.json`；Python 安装器拒绝覆盖已有目录，并生成 `install-manifest.json`。两种方式都只安装 Skill，不同时安装检查工具。Skill 的唯一源目录为 [skills/text-prison](skills/text-prison/SKILL.md)。

存在影响结果的方案取舍时，Skill 会提出 2–3 个选项并给出推荐；对象和动作已明确的局部改写则直接处理。它按用途、语言和写作风格读取所需规则。两个工具同时使用时，每轮各检查一次；根据提示最多修订一次，必要时再各复查一次。只审阅时不改写。

宿主可以为相关文档请求自动选择此 Skill，实际是否触发取决于宿主。当前没有自动触发、读者理解效果或成本改善的实测保证。

## 保留资料

- [当前设计范围](docs/DESIGN.md)：任务流程、职责和限制。
- [已批准实施方案](docs/plans/text-prison-vale.md)：设计依据和单次 Opus 审阅记录。
- [中文支持与发布安装计划](docs/plans/chinese-publish-install.md)：实施方案、Opus 意见处理及安装验收记录。
- [来源目录](docs/RELATED_WORK.md)及 [机器来源索引](sources.json)：规范、参考实现和此前的来源核验范围。
- [归属说明](NOTICE.md)：第三方资料与许可边界。

五个上游子模块保持固定版本，仅作只读参考，不安装、不执行。原始 ZIP、根 `MANIFEST.sha256.json` 与 `DOCS_PATCH.md` 保留原包的历史含义，不代表当前功能或验证状态。

本仓库不再运行或维护 Agent 实战、模型评委、A/B 实验、测试套件或评审网页。原提交和归档标签保留在 Git 历史中；已删除的忽略目录原始数据没有另行备份。

## 使用边界

保留事实、条件、权限、数字、单位、引用和不确定性。规则借鉴不等于完整 ASD-STE100 认证，也不证明语义正确。代码、命令、标识符和原样引文按用户要求保护，不为文风统一擅自修改。

不做观点审查，不以规避 AI 文本检测为目标，不自动安装工具或修改全局指令。
