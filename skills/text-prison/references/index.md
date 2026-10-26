# 按任务选择参考

先选择用途，再选择语言；只读适用项。核心保护与编辑边界见 [Skill 入口](../SKILL.md)，这里不重复。

| 文档用途 | 参考 |
|---|---|
| 解释、README 概览、概念教程 | [explanation](explanation.md) |
| 安装、操作、故障处理 | [procedure](procedure.md) |
| API、参数、查询手册 | [reference](reference.md) |
| 科研摘要、结果解释、论证 | [research](research.md) |
| AGENTS、SKILL、Agent 指令 | [agent-spec](agent-spec.md) |

用户明确指定使用 TextPrison 的技术回答也按此表选用途：概念回答通常读 explanation，科研结论按 research 处理；聊天正文只是交付形式，不增加第六种用途，也不要求写入文件。

中文读 [中文规则](lang-zh.md)，英文读 [English](lang-en.md)。混合文档按章节采用相应语言约定；不把英文句法规则全局套到中文上。

开发文档通常再读 [Google 摘要](google.md)，英文 UI 文案和产品帮助通常再读 [Microsoft 摘要](microsoft.md)，简体中文本地化读 [Microsoft 中文摘要](microsoft-zh.md)。选一个主线；项目已有约定优先。科研和 Agent 指令默认不加载品牌风格，确有组织或表达需求时才补读。

任何用途出现术语、指代或关系歧义、名词串或名词化隐藏动作、主句被插入信息打断、操作与解释混杂、体裁不合或重复铺垫时，按需读 [STE-inspired](ste-inspired.md)。它为上面的用途补充消歧与可读性指导，不另设一种用途，也不作为每次写作必读的语法规范。科研保留限定与论证，API/reference 保留定义、表格和标识符；不为主动句或短句改变技术含义。纯机器输出不进入本 Skill。

中文排版任务再读 [中文排版约定](chinese-typography.md)。需机械建议时读 [AutoCorrect 调用说明](autocorrect.md)，配置与版本在 [AutoCorrect 目录](../autocorrect/README.md) 维护。不是每份中文文档都要改变排版。

需要风格、术语或链接检查时读 [Vale 调用说明](vale.md)；配置、版本、包和规则清单只在 [Vale 配置目录](../vale/README.md) 维护。Vale 的 Google/Microsoft 包不提供完整中文写作规范。两个工具均不负责理解文档用途或判断事实正确性。
