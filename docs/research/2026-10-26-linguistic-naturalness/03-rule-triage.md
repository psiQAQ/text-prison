# 候选规则分诊表（设计，不是已实现）

| 编号 | 名称 | 命中对象 | 检查技术 | 误报控制 / 例外 | 采纳建议 |
|---|---|---|---|---|---|
| R01 | BoilerplateOpeningZh | 中文：无信息的“当然可以/下面为你…” | 单句候选正则 | 提醒，不对礼貌邮件生效 | 可行、选用时 |
| R02 | BoilerplateEndingZh | 中文：“希望以上内容对你有所帮助”等套尾 | 正则 | 客服结尾可合理 | 可行、选用时 |
| R03 | MechanicalPivotZh | 中文：不是X而是Y，强制反转 | 正则抽候选 | 一次有意义的对比不应受罚 | 低风险候选，默认关 |
| R04 | AIFillerZh | 中文：在当今快速发展的时代等空话 | 完整短语命中 | 不同文种可能是直接引文 | 可行、选用时 |
| R05 | VagueAuthorityZh | 中文：研究表明/数据说明但无位置引用 | 仅文本候选，不判来源 | 需 Agent 核对紧邻正文、脚注、表格 | 默认不开自动规则 |
| R06 | AbstractBusinessZh | 中文：赋能、抓手、闭环等 | 仅术语候选 | 行业内和团队约定合法，词表白名单 | 默认关、窄用途 |
| R07 | OverloadedIntroEn | 英文：It is important to note that 等 | retext-simplify 风格存在/替换建议 | 不应删除真实逻辑限定 | 可行、选用时 |
| R08 | GenericTransitionEn | 英文：Moreover/Furthermore/In conclusion | 关键词模式 | 连接词常承担必要的逻辑关系 | 默认关 |
| R09 | AcronymFirstUseEn | 英文：缩写首次使用未定义 | Vale Std.Abbreviations.Acronyms | API 和常见缩写需例外 | 需同步 Std、按授权 |
| R10 | LongSentenceEn | 英文：句长超过选定分位阈值 | Vale Std.Readability.SentenceLength | 科研/API 容忍度比面向大众的帮助高 | 需同步 Std、默认关 |
| R11 | ExclamationAndSpacing | 英文感叹与间距 | 现有 Google/Microsoft | 已经存在，不重复造轮子 | 保持现状 |
| R12 | VagueLinkZhEn | 中英泛指链接 | 已有 TextPrison.VagueLink* | 已经存在，不新增 | 保持现状 |
| R13 | OverBoldMarkdown | 大量连续加粗标记 | Vale scope 模式或 markdown AST | 没有可靠全局密度计算，不当作低风险 Vale 规则 | 待定 |
| R14 | RepeatedSummary | 两段总结内容重复 | embedding + 语义判断 | Vale 简单正则不足以判断语义重复 | 只做人工审校 |
| R15 | NounStackAndAnomalousAnimacy | 名词串/无生命主语配有生命动词 | 依存解析、语义分类 | 正则误报高，不能放进默认 Vale | 离线研究 |
| R16 | SemanticPreservation | 改稿遗漏条件、否定或数值 | 对照原文的独立事实核验 | Vale 不能判断，不宣称自动可检查 | 写作过程保护 |

## 为什么不直接安装两个 AI 味插件

- TextPrison 已有唯一 Skill 入口；全套装入 sloptrim、sloptrim-cn 或 renhua 会重复指令并引入命令、插件、自动钩子及自动修订流程。
- 它们的模式可作为阅读参考，在尊重 Apache-2.0/MIT 和 NOTICE 的前提下择优编写原创规则；不能直接复用未核实的阈值，也不应借鉴声称“AI 分数”和“改写至检测器通过”的目标。
- 机械 Vale 规则只提示具体字符串命中。句法歧义、因果和指代属于有上下文的语言学判断，仍由现有 Skill 进行。

## 建议告警呈现

输出：`[规则名] 原文位置 → 可解释问题 → 是否影响理解 → 原意保护要求 → 候选处理`。只建议，不自动改写；相同问题定位，不叠加多个语义近似的告警。`severity=suggestion`；科研、API、Agent 指令默认只启用已有最保守规则。
