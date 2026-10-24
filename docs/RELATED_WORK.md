# 相关实现、原始研究与采纳边界

检索截止：2026-10-24。本文是文档设计修订依据，不是复现实验报告。公开仓库按当日可见页面审阅，未执行其代码；浮动分支尚未固定 commit，因此不能称为可复现的外部基线。论文优先使用正式出版页面；SkillsBench 使用明确版本 v4，不混用早期版本的任务数与结果。

## 1. 找到了哪些相近实现

| 实现 | 值得借鉴的机制 | TextPrison 的采纳方式 | 不直接照搬的部分 |
|---|---|---|---|
| danyuchn/asd-ste100-skill；所读 Skill 元数据为 0.4.0 [R01] | 严格模式与 STE 风格模式分开；强调指令消歧 | 明确 scope、语言和合规状态；保留按需加载 | 不将结构检查包装成完整标准认证 |
| AminBlg/SimpleEnglish；所读 Skill 元数据为 2.1.1 [R02] | 段落类型路由、普通/严格模式、规则与评测配套 | 用作英文文档领域的候选外部对照；参考路由与对照组织 | 不导入全局模态词禁令、全局同义词替换或聊天排版限制 |
| stazelabs/ste [R03] | 将部分写作规则变成独立检查器；公开实验及局限 | 保留可机器验证的规则 ID、诊断和计量口径 | 不用同一套风格规则的下降率证明真实理解能力 |
| Vale 及 Google/Microsoft 风格包 [R04] | 结构化作用域、模块化规则与领域词表 | 未来增加可选适配器；按规则映射去重、隔离代码/引用 | 不把两个完整风格包同时强制启用；社区包不等于官方认证 |
| Anthropic skill-creator [R05] | with/without Skill 比较、断言、时间/Token 记录、触发描述迭代 | 借鉴开发集闭环与宿主级对照 | 正式盲测必须提前冻结断言，不能看完输出后修改验收 |
| SkillsBench v4 [R06] | 相同任务、隔离环境、Skill 有无配对、独立 verifier、任务级聚合 | 借鉴任务封装、独立验收与版本记录 | 不按处理组收益筛选“有效任务”；不将其跨领域平均收益移植给本项目 |
| Inspect [R07] | 将数据集、执行和评分分开 | 可作为离线实验编排的候选组件 | 不强制新增依赖；它不能自动替代 Codex/Claude Code 的原生触发测试 |

SimpleEnglish 的一条规则限制可用模态词，包含禁用 may/might/could。科研文本中的这些词可能承载不确定性或条件能力，因此本项目不采纳这种全局限制；这是一项语义风险判断，不是对该项目真实错误率的测量。[R02]

## 2. 已有数据能支持到什么程度

| 来源及版本 | 作者报告的结果 | 可以支持 | 不能支持 |
|---|---|---|---|
| SimpleEnglish 当日结果页 [R02] | 9 个模型、8 个任务、144 次生成；平均 STE 违规率下降 81.3% | 其检查器和样本上的风格变化 | 人类理解提高 81.3%、下游 Agent 成功率提高 81.3% |
| stazelabs/ste 实验页 [R03] | 在所测模型上，检查器违规率下降约 88%–97% | 所测规则更少被违反 | 相同幅度的可读性或 Token 收益；作者自己说明提示词与检查器共享规则的偏差 |
| SkillsBench v4，2026-06-14 [R06] | 87 个任务、8 个领域、18 个配置；平均通过率 33.9%→50.5% | 这一特定基准上成对 Skill 干预的结果 | TextPrison 必然提高 16.6 个百分点；简短规则的效果已被单独因果识别 |

以上均未在本项目复现。SkillsBench 是预印本；其任务筛选、公开轨迹覆盖及重跑政策也限制外推。TextPrison 不复制按处理收益筛题或选择较健康轨迹替代失败结果的做法，避免选择偏差。[R06]

## 3. 将研究方法转成项目决策

| 研究/标准 | 方法精髓 | 本项目新增的量化逻辑 | 适用边界 |
|---|---|---|---|
| 受控语言实证研究，CLAW 1996 [R13] | 用真实读者比较理解与定位信息；区分任务复杂度与语言背景 | 限时关键题全对率、定位时间；按语言/领域经验分层 | 历史 SE 研究不是现行 STE 或 LLM 的效果验证 |
| ISO 24495-1 与 ISO 9241-11 [R11–R12] | 可理解、可使用的表达；特定情境中的使用效果 | 先定义读者、任务和使用情境，再定义指标 | 本轮仅核对公开介绍/摘要，未取得完整付费条文；标准不给本项目的百分比门槛 |
| FActScore，EMNLP 2023 [R14] | 将生成文本拆成原子事实，逐项核对来源支持 | 生成事实支持率；另加必需事实保留率，防止靠删信息获得高分 | 后者是 TextPrison 的适配，不是原 FActScore 指标；原评估领域不等于中文科研 |
| SALSA，EMNLP 2023 [R15] | 在局部编辑层面标注改进、错误与严重度 | 将遗漏、条件变化、模态变化等关联到具体 source/candidate span | 采用编辑级审查思想，不声称复现全部标注体系或学习评分器 |
| IFEval，2023 [R16] | 指令级与整份回答级的可验证遵循 | 同时报单条硬约束通过率与全部适用硬约束通过率 | 可验证格式遵循不等于事实正确；不采用会放宽 JSON 契约的“宽松通过” |
| CheckList，ACL 2020 [R17] | 最小功能、不变性、方向性测试 | 用最小变异定位否定、模态、单位、主体和条件错误；独立检查评委是否识别错误 | 人工构造的压力样本不代表真实任务分布 |
| SARI、LENS [R18–R19] | 在特定简化任务中，用参考文本或人类判断学习/评估编辑质量 | 仅作为适用英文改写任务的探索性辅助指标 | 不是通用问答分数；不能未经验证直接用于中文或开放式科研报告 |
| 文档级简化指标研究，NAACL 2025 [R20] | 句子级指标迁移到长文档存在失效风险 | 对代理指标先做领域验证；文档理解主终点保持独立 | 不因某项聚合方法在论文中有效就将其设为生产门禁 |
| AI Agents That Matter，2024 [R21] | 同时评估成功率、成本与可复现性 | 成本—质量前沿、每成功任务成本、等修订机会对照 | 不用更高推理预算造成的收益冒充规则本身收益 |
| Agent 评测实践与 LLM 评委研究 [R22–R23] | 区分代码/模型/人工评分，审查位置和冗长偏好 | 独立 verifier；评委盲化、交换顺序、人工校准；允许 uncertain | 换一个模型家族不自动形成独立真值 |
| Sample Size Justification 与 NIST [R24–R25] | 根据推断目标、可接受差异和精度解释样本量 | 预注册非劣效界值、功效/精度设计、零事件上界 | 不把固定 24/96 样本或“零错误”当作充分证据 |

## 4. 证据分级与采纳规则

本项目区分四种依据，而不把它们混合成“已证实有效”：

- **规范依据**：某指南建议怎样写。支持规则来源，不支持提升幅度。
- **直接工程证据**：公开实现、可执行检查器或原始日志。支持可实现性；效果取决于其任务与评价方式。
- **实证方法依据**：研究支持某种测量或实验方法。迁移到本领域后仍需校准。
- **项目假设**：新的组合、阈值、Token 预算或路由策略。必须明确标记并验证。

因此，原方案的阅读耗时下降 10%、Token 下降 30%、非劣效界值 3 个百分点、触发 95%/90% 不再作为默认验收标准。它们保留为历史设想，不是文献结论。新的门槛填写在 [预注册表](../eval/PREREGISTRATION.md)，在保留集运行前冻结。

## 5. 原始来源目录

下列为可核查入口。网页检索日均为 2026-10-24；链接为当日观察地址，不表示已完成代码审计。动态仓库成为实验对照前还须固定 commit、配置和许可证范围。除有限短语外，本文使用自主概括，不分发完整 STE 词典或付费标准。

<a id="r01"></a>
**R01 — ASD-STE100 Skill（社区实现）。** [仓库](https://github.com/danyuchn/asd-ste100-skill)；[所读 SKILL.md](https://raw.githubusercontent.com/danyuchn/asd-ste100-skill/master/SKILL.md)。用途：模式与边界设计。

<a id="r02"></a>
**R02 — SimpleEnglish（社区实现与作者自评）。** [仓库](https://github.com/AminBlg/SimpleEnglish)；[所读 SKILL.md](https://raw.githubusercontent.com/AminBlg/SimpleEnglish/main/skills/simple-english/SKILL.md)；[实验结果](https://github.com/AminBlg/SimpleEnglish/blob/main/evals/results/RESULTS.md)。用途：近邻方案、候选外部基线与危险规则排除。

<a id="r03"></a>
**R03 — ste（社区检查器与作者自评）。** [仓库](https://github.com/stazelabs/ste)；[实验结果及局限](https://github.com/stazelabs/ste/blob/main/docs/experiment-results.md)。用途：独立检查器、共享规则偏差案例。

<a id="r04"></a>
**R04 — Vale（官方工具文档与社区风格包）。** [Styles](https://docs.vale.sh/topics/styles)；[Scopes](https://docs.vale.sh/topics/scopes)；[Vocabularies](https://docs.vale.sh/keys/vocabularies)；[Google 包](https://github.com/vale-cli/Google)；[Microsoft 包](https://github.com/vale-cli/Microsoft)。用途：语法树作用域与可选适配器。

<a id="r05"></a>
**R05 — skill-creator（Anthropic 官方示例）。** [SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)。用途：开发集迭代、with/without 试验、原生触发评估；不是统计效力保证。

<a id="r06"></a>
**R06 — SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks.** arXiv:2602.12670v4，2026-06-14，预印本。[固定版本](https://arxiv.org/abs/2602.12670v4)；[全文](https://arxiv.org/html/2602.12670v4)；[项目代码](https://github.com/benchflow-ai/skillsbench)。用途：配对任务、verifier、宏平均与局限审查。

<a id="r07"></a>
**R07 — Inspect。** [官方文档](https://inspect.aisi.org.uk/)。用途：评测编排职责分离，候选而非强制依赖。

<a id="r08"></a>
**R08 — ASD-STE100。** [官方网站](https://www.asd-ste100.org/)。本轮直接访问部分官方说明页返回 403，未取得完整标准正文；本方案不据此宣称完整规范核验。保留前版 STE-inspired 定位。

<a id="r09"></a>
**R09 — Google Developer Documentation Style Guide。** [Highlights](https://developers.google.com/style/highlights)。用途：技术写作与一致性原则，不提供本项目效果阈值。

<a id="r10"></a>
**R10 — Microsoft Writing Style Guide。** [Scannable content](https://learn.microsoft.com/en-us/style-guide/scannable-content/)。用途：信息组织与扫描阅读，不等于全部内容必须列表化。

<a id="r11"></a>
**R11 — ISO 24495-1:2023, Plain language — Part 1: Governing principles and guidelines。** [官方摘要](https://www.iso.org/standard/78907.html)。仅查阅公开信息，未查阅完整条文。

<a id="r12"></a>
**R12 — ISO 9241-11:2018, Usability: Definitions and concepts。** [官方摘要](https://www.iso.org/standard/63500.html)。概念框架；摘要明确并不规定具体评估方法。

<a id="r13"></a>
**R13 — Issues in Conducting Empirical Evaluations of Controlled Languages。** CLAW 1996。[原始论文存档](https://mt-archive.net/90/CLAW-1996-Holmback.pdf)。查阅正文与页面图；其中两项程序任务的效果不同，不能概括为所有文本普遍受益。

<a id="r14"></a>
**R14 — FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation。** EMNLP 2023。[出版页](https://aclanthology.org/2023.emnlp-main.741/)；[全文](https://arxiv.org/html/2305.14251)。用途：原子事实支持；论文明确指出未测事实召回。

<a id="r15"></a>
**R15 — Edit-level Simplification Evaluation using SALSA。** EMNLP 2023。[出版页](https://aclanthology.org/2023.emnlp-main.211/)；[全文版本](https://arxiv.org/html/2305.14458v2)。用途：编辑定位、信息变化与严重度。

<a id="r16"></a>
**R16 — Instruction-Following Evaluation for Large Language Models（IFEval）。** 2023。[论文](https://arxiv.org/abs/2311.07911)。用途：可验证约束的单项与整体通过率。

<a id="r17"></a>
**R17 — Beyond Accuracy: Behavioral Testing of NLP Models with CheckList。** ACL 2020。[出版页](https://aclanthology.org/2020.acl-main.442/)；[全文](https://arxiv.org/html/2005.04118)。用途：MFT / INV / DIR 行为测试。

<a id="r18"></a>
**R18 — Optimizing Statistical Machine Translation for Text Simplification（SARI）。** TACL 2016。[出版页](https://aclanthology.org/Q16-1029/)。用途：有源文和参考简化文本时的编辑型辅助指标。

<a id="r19"></a>
**R19 — LENS: A Learnable Evaluation Metric for Text Simplification。** ACL 2023。[出版页](https://aclanthology.org/2023.acl-long.905/)。用途：经过领域验证后才考虑的学习型辅助指标；不要与 SALSA 的变体混淆。

<a id="r20"></a>
**R20 — Adapting Sentence-level Automatic Metrics for Document-level Simplification Evaluation。** NAACL 2025。[出版页](https://aclanthology.org/2025.naacl-long.327/)；[PDF](https://aclanthology.org/2025.naacl-long.327.pdf)。已检查首页与结果表所在页面。用途：句子级分数的文档迁移风险。

<a id="r21"></a>
**R21 — AI Agents That Matter。** 2024。[论文](https://arxiv.org/abs/2407.01502)；[研究项目](https://agents.cs.princeton.edu/)。用途：成本—准确率联合评价和可复现性。

<a id="r22"></a>
**R22 — Demystifying evals for AI agents。** Anthropic，2026-01-09。[官方文章](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)。用途：多种 grader、轨迹与结果、重复可靠性。

<a id="r23"></a>
**R23 — Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena。** 2023。[论文](https://arxiv.org/abs/2306.05685)。用途：位置、冗长与自我偏好等评委偏差，不借用论文中的一致率作本项目保证。

<a id="r24"></a>
**R24 — Sample Size Justification。** Collabra: Psychology，2022，8(1):33267。[正文](https://online.ucpress.edu/collabra/article/8/1/33267/120491/Sample-Size-Justification)；DOI: 10.1525/collabra.33267。用途：最小有意义差异、精度与样本量理由。

<a id="r25"></a>
**R25 — NIST/SEMATECH 比例置信区间与精确二项区间。** [比例区间](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)；[精确区间](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm)。用途：有限样本不确定性；本文零事件公式是独立二项模型的特例推导。

<a id="r26"></a>
**R26 — Agent Skills specification。** [官方规范](https://agentskills.io/specification)。用途：元数据与按需加载；不等于宿主必然触发。

<a id="r27"></a>
**R27 — Codex Skills。** [OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills)。用途：项目目录、显式/隐式调用边界。宿主实测需固定版本。

<a id="r28"></a>
**R28 — Claude Code Skills。** [官方文档](https://code.claude.com/docs/en/skills)。用途：宿主调用及上下文开销，不从静态文件长度推断整个会话成本。

<a id="r29"></a>
**R29 — OpenAI usage / caching / reasoning。** [Usage](https://developers.openai.com/api/docs/guides/agents-api/observability)；[Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)；[Reasoning](https://developers.openai.com/api/docs/guides/reasoning)。用途：provider 专用计量，保留原始字段并防止重复求和。

<a id="r30"></a>
**R30 — Anthropic Prompt caching。** [官方文档](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)。用途：Messages API 输入、缓存写入和读取分项；CLI 聚合对象仍须独立核验。
