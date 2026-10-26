# 开源工具与研究代码选型

**首选组合不变：TextPrison写作指导 + 已有Vale + 按需AutoCorrect。** 新工具是否值得接入，应先回答“它新增了哪种现有规则做不到的诊断”，而不是看工具总数。

以下是2026-10-26的公开资料核对。没有运行、安装或对比这些工具；星标来自GitHub页面的约数展示。项目许可证标识不自动涵盖模型权重、数据、词典和外部规则包。

## 一、6个通用工具

| 项目与链接 | 页面星标 / 许可标识 | 适合解决什么 | 不能解决什么 | 对当前仓库的建议 |
|---|---|---|---|---|
| [Vale](https://github.com/vale-cli/vale) | 约6.3k；MIT | 按文档结构和作用域执行可配置风格规则 | 自动理解所有歧义、事实核验、全文STE认证 | 继续作为唯一显式写作规则引擎 |
| [AutoCorrect](https://github.com/huacnlee/autocorrect) | 约1.7k；MIT | CJK混排、空格和部分标点/词汇规则 | 名词串消歧、逻辑关系和科学结论保护 | 保持当前可选排版定位 |
| [textlint](https://github.com/textlint/textlint) | 约3.2k；MIT | JS生态中的可插拔自然语言lint | 默认就完整支持中文语义；每个插件都同质量 | 目标项目已有此生态时再单独讨论，不默认并装 |
| [retext](https://github.com/retextjs/retext) | 约2.4k；MIT | 插件化文本处理和语法树管线 | 通用“认知负担”或事实正确性证明 | 未来编辑器集成的参考，不进入当前运行栈 |
| [write-good](https://github.com/btford/write-good) | 约5.1k；MIT | 英文中的冗词、套话、部分被动等启发式提示 | 判断科研被动句或限定词是否应保留 | 只借鉴少量提示思路，不全量启用 |
| [proselint](https://github.com/amperser/proselint) | 约4.6k；BSD-3-Clause | 英文编辑规则与风格建议 | 中文语义、内容保真或读者理解保证 | 参考规则目录，不新建Python调用后端 |

星标只能说明关注度，不能证明日常收益。这里的选择依据首先是项目范围、语言与维护成本，其次才是生态规模。来源：T01—T06，见[sources.json](sources.json)。

### 需要特别注意的项目状态

**proselint的GitHub仓库现在标为镜像。** 其页面指向[Codeberg上的主仓库](https://codeberg.org/amperser/proselint)。后续查询维护动态应从主仓库开始；不能根据镜像的提交频率判定项目停更。

**write-good自称朴素英文lint工具。** 它包含被动语态、副词和其他风格建议；这类规则在科研说明中需要例外。将其所有建议自动修复，可能改变表达重点或删除必要限定。当前不建议叠加到Vale之后，形成重复告警。

**textlint是引擎，不等于一套统一的中文规则。** 某个语言的插件生态丰富，不能直接推出另一种语言同样完善。引入插件还需单独核对许可、作用域和维护状态。retext同样需要明确选定解析器与插件，不能仅凭支持“自然语言”就声称能可靠处理中文科技句法。

## 二、6个论文相关项目：参考价值不等于适合安装

| 项目 | 研究支持 / 角色 | 主要限制 | 当前结论 |
|---|---|---|---|
| [MUSS](https://github.com/facebookresearch/muss) | [E02](https://aclanthology.org/2022.lrec-1.176/)；句子改写模型 | 旧依赖说明；论文验证英语、法语、西班牙语；可能改变含义 | 研究参考，不纳入日常依赖 |
| [LENS上游](https://github.com/Yao-Dou/LENS) | [E05](https://aclanthology.org/2023.acl-long.905/)；简化质量指标 | 不是改写器；语言/领域迁移；许可未核清 | 只用于理解评价方法 |
| [SALSA](https://github.com/davidheineman/salsa) | [E06](https://aclanthology.org/2023.emnlp-main.211/)；编辑标注和指标 | 标注/模型成本；未审计实现和许可 | 借鉴错误分类，不引入评测工具 |
| [MCTS](https://github.com/blcuicall/mcts) | [E08](https://aclanthology.org/2024.lrec-main.969/)；中文数据与基准 | 不是中文文法检查器；数据许可须另核对 | 保留书目和数据入口 |
| [UIDPO](https://github.com/CLCS-SUSTech/UIDPO) | [P05](https://arxiv.org/html/2610.14578v1)；偏好训练方法 | 需要训练；根README与明确许可未核到 | 不复制、不安装，不称为已确认可复用开源组件 |
| [BLESS](https://github.com/ZurichNLP/BLESS) | [E03](https://aclanthology.org/2023.emnlp-main.821/)；模型简化基准 | 不是日常写作插件；未重跑、未审计全部代码 | 文献参考，不恢复基准流水线 |

MUSS当前README仍写有“Python 3.9尚不兼容”的提示。本轮没有在新环境试装，因此准确表述是“文档显示依赖陈旧，需要额外核验”，而不是断言所有现代环境都无法运行。

LENS的`davidheineman/LENS`是fork；本报告使用作者项目上游`Yao-Dou/LENS`。GitHub API对该上游和UIDPO返回的许可证字段均未识别到许可。`license=null`不证明仓库任何角落都没有许可，但也不提供复制或分发授权。

**公开可读的代码不自动等于已确认许可的开源依赖。** 本包仅给研究入口，不分发这些项目的源码、数据或权重。

## 三、仓库已经有的社区参考，不应再安装一遍

[现有RELATED_WORK](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/docs/RELATED_WORK.md)已登记：

| 已有项目 | 如何利用 | 本轮边界 |
|---|---|---|
| [asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill) | 参考受控语言与消歧思路；现有STE-inspired已吸收部分原则 | 不替代官方标准，不改变只读快照 |
| [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) | 比较提示词结构与限制策略 | 不照搬可能伤害科研模态的规则，不重述作者自评为独立证据 |
| [ste](https://github.com/stazelabs/ste) | 了解其他检查器的覆盖与误报权衡 | 不恢复第二个后端，不运行上游测试 |

本轮对这三项只核对项目中已有的来源登记，没有重新审计全部上游内容。固定提交和阅读范围见本次来源表C01—C03及原仓库来源页。另注意`stuffbucket/vale`与`vale-cli/vale`不是同一个项目，不应混用安装来源、版本或许可证结论。

## 四、怎样用好现有Vale，而不是过早更换引擎

[当前Vale目录](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/skills/text-prison/vale/README.md)已经采用少量逐条启用、建议级别和受保护作用域。建议维持这一策略。当前中文规则主要是模糊链接文字，不能宣传成中文语法或句子可读性检查；科研配置的覆盖也很窄，这是覆盖边界，不是运行故障。

下一步可考虑的规则候选，是项目明确约定的缩写写法、指定术语的一致性或明确冗余短语。每一条都应先说明适用正文、受保护文本、误报情形和允许的处理方式。没有低歧义规则时，保持现状比加入一条经常误报的规则更好。

不建议用正则表达式自动判定整类中文名词链、因果缺失或无生命主语。这些通常需要上下文与含义判断，应留给当前Agent按来源处理。也不建议为了“可读性”启用全局被动语态、第一人称、模态词或固定句长禁令。

## 五、组合方案与实际负担

| 方案 | 新依赖 | 额外模型调用 | 使用负担 | 建议 |
|---|---|---|---|---|
| 仅更新文字指导 | 无 | 不要求 | 最低；当前Agent做局部修改与核对 | 首选 |
| 文字指导 + 当前Vale | 不新增；要求已有可用工具和规则 | 不要求 | 有明确诊断输出；维护已有规则 | 文档场景按需 |
| 再加AutoCorrect | 仅在用户选用且已准备时 | 不要求 | 多一类排版建议；共用现有修订轮次 | 中文排版有需要时 |
| 并装多套lint | Node/Python等及额外包 | 不必然 | 告警重叠、作用域和版本维护增加 | 当前不推荐 |
| 自动重写模型 + 评分模型 | 模型、推理环境及权重 | 通常需要额外推理 | 语义漂移、隐私、延迟和解释成本 | 当前不推荐 |

“无额外模型调用要求”不代表提示词免费：更长上下文和输出仍可能增加Token与延迟。本次没有测量增量成本，也不宣称“低开销”已被证明。
