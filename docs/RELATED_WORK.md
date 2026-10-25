# 来源目录与只读参考快照

当前用途更新于 2026-10-25；原书目和快照核验日期为 2026-10-24。本页保留来源入口、归属和此前阅读范围。旧评测实施建议已撤除；历史研究方法条目仅为书目，不是本仓库继续开展测试的计划。

完整机器记录见 [sources.json](../sources.json)。固定提交和 README 阅读不代表代码审计、效果复现或第三方内容许可已全部核实。除已记录的有限核验范围外，不把登记链接当作重新阅读原文。

日常写作参考 STE 的指令消歧、Google 的读者任务组织及 Microsoft 的信息呈现原则。中文部分增加微软简体中文本地化指南与社区排版约定，机械排版可选用 AutoCorrect。来源不提供 TextPrison 的收益保证，不采用固定节省率、理解提升率或模型评分作为产品承诺。

## 当前运行材料的来源

2026-10-25 新增阅读范围记录在 `sources.json` 的 `runtime_sources`，不改变下方历史书目的核验状态。Vale CLI 官方文档支持配置、作用域、stdin、退出码和包同步的说明；固定标签 Google v0.7.1、Microsoft v0.15.1 的所选规则、元数据及发布脚本支持当前配置。未下载核验发布 ZIP，也未执行 CLI 或规则。

Google 和 Microsoft 写作指导为官方页面的自主概括；STE-inspired 仅借鉴已记录的社区快照，不声称重新阅读完整 ASD 标准。实际规则及逐项来源见 [Vale 目录](../skills/text-prison/vale/README.md)，写作指导入口见 [规则索引](../skills/text-prison/references/index.md)。

中文补充阅读范围：Microsoft 简体中文 PDF 的第 4–8、11、27–28、35–38、43–44 页；中文文案排版指北的空格、标点、全半角、名词及争议部分。只分发自主摘要，不附完整原文。AutoCorrect 固定 v2.16.3 的参数、配置合并、stdin 与 JSON 分支，以及 Skills CLI v1.7.4 的复制、锁文件、提交 SHA 和遥测行为已做源码核对；实际安装另记，不能由来源登记推定运行成功。来源指针及限制见机器索引新增条目和 [AutoCorrect 目录](../skills/text-prison/autocorrect/README.md)。

注意同名项目：R04 指官方 Vale CLI 及 Google/Microsoft 风格包；R32 的 `stuffbucket/vale` 是另一个独立的 STE 检查器，只保留为参考，不能作为 Vale CLI 的安装来源。

## 1. 原始来源目录

下列为来源入口。此前原文阅读范围保留在各条目中；本次同步仅对 R01、R02、R03、R31、R32 的固定本地材料进行了新增核对，其余条目在机器索引中为 `bibliography_only`。除有限短语外，本文使用自主概括，不分发完整 STE 词典或付费标准。这些来源仅作历史书目与只读参考，不构成运行实验或测试的指令。

<a id="r01"></a>
**R01 — ASD-STE100 Skill（社区实现）。** [仓库](https://github.com/danyuchn/asd-ste100-skill)；[固定版本 SKILL.md](https://github.com/danyuchn/asd-ste100-skill/blob/cd62d297d5ef7cf9f59718cadc233ab2876ea013/SKILL.md)。用途：模式与边界设计；本次核对版本 0.4.0 及保留模态、条件的条款。

<a id="r02"></a>
**R02 — SimpleEnglish（社区实现与作者自评）。** [仓库](https://github.com/AminBlg/SimpleEnglish)；[固定版本 SKILL.md](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/skills/simple-english/SKILL.md)；[固定版本历史实验入口](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/results/RESULTS.md)。用途：近邻方案、候选外部基线与危险规则排除。本次核对元数据 2.1.1 及模态词限制，未重跑作者实验。

<a id="r03"></a>
**R03 — ste（社区检查器与作者自评）。** [仓库](https://github.com/stazelabs/ste)；[固定版本实验结果入口](https://github.com/stazelabs/ste/blob/922c9773d0004f4c40b2e1373db9ed949321373d/docs/experiment-results.md)。用途：独立检查器、共享规则偏差案例；本次仅核对 README 的功能、限制与结果自述及根许可证。

<a id="r04"></a>
**R04 — Vale（官方工具文档与 vale-cli 社区风格包）。** [Styles](https://docs.vale.sh/topics/styles)；[Scopes](https://docs.vale.sh/topics/scopes)；[Vocabularies](https://docs.vale.sh/keys/vocabularies)；[Google 包](https://github.com/vale-cli/Google)；[Microsoft 包](https://github.com/vale-cli/Microsoft)。用途：语法树作用域与可选适配器。R04 不是 R32 `stuffbucket/vale` 的来源身份，不共用版本或许可证结论。

<a id="r05"></a>
**R05 — skill-creator（Anthropic 官方示例）。** [SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)。用途：开发集迭代、with/without 试验、原生触发评估；不是统计效力保证。

<a id="r06"></a>
**R06 — SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks.** arXiv:2602.12670v4，2026-06-14，预印本。[固定版本](https://arxiv.org/abs/2602.12670v4)；[全文](https://arxiv.org/html/2602.12670v4)；[项目代码](https://github.com/benchflow-ai/skillsbench)。用途：配对任务、verifier、宏平均与局限审查。

<a id="r07"></a>
**R07 — Inspect。** [官方文档](https://inspect.aisi.org.uk/)。用途：评测编排职责分离，候选而非强制依赖。

<a id="r08"></a>
**R08 — ASD-STE100。** [官方网站](https://www.asd-ste100.org/)。此前文献审阅记录部分官方说明页返回 403，未取得完整标准正文；本次未重新请求该网站，不宣称完整规范核验。保留前版 STE-inspired 定位。

<a id="r09"></a>
**R09 — Google Developer Documentation Style Guide。** [Highlights](https://developers.google.com/style/highlights)。用途：技术写作与一致性原则，不提供本项目效果阈值。

<a id="r10"></a>
**R10 — Microsoft Writing Style Guide。** [Scannable content](https://learn.microsoft.com/en-us/style-guide/scannable-content/)。用途：信息组织与扫描阅读，不等于全部内容必须列表化。

<a id="r11"></a>
**R11 — ISO 24495-1:2023, Plain language — Part 1: Governing principles and guidelines。** [官方摘要](https://www.iso.org/standard/78907.html)。此前文献审阅仅查阅公开信息，未查阅完整条文；本次仅同步书目。

<a id="r12"></a>
**R12 — ISO 9241-11:2018, Usability: Definitions and concepts。** [官方摘要](https://www.iso.org/standard/63500.html)。概念框架；摘要明确并不规定具体评估方法。

<a id="r13"></a>
**R13 — Issues in Conducting Empirical Evaluations of Controlled Languages。** CLAW 1996。[原始论文存档](https://mt-archive.net/90/CLAW-1996-Holmback.pdf)。此前文献审阅记录已查看正文与页面图；其记录指出两项程序任务效果不同，不能概括为所有文本普遍受益。本次仅同步书目。

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
**R20 — Adapting Sentence-level Automatic Metrics for Document-level Simplification Evaluation。** NAACL 2025。[出版页](https://aclanthology.org/2025.naacl-long.327/)；[PDF](https://aclanthology.org/2025.naacl-long.327.pdf)。此前文献审阅记录已检查首页与结果表所在页面；本次仅同步书目。用途：句子级分数的文档迁移风险。

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

<a id="r31"></a>
**R31 — STE-Prompt（menonpg/ste-prompt，社区提示词与插件）。** [仓库](https://github.com/menonpg/ste-prompt)；[固定 README](https://github.com/menonpg/ste-prompt/blob/f59ae8de5497c81ece60e0a8fac11fe6a54d3777/README.md)。用途：对照按需 Skill、命令和常驻指令入口，以及科研/风险文本的适用例外。本次未核验各宿主安装行为，也未验证作者对易读性的描述。

<a id="r32"></a>
**R32 — vale（stuffbucket/vale，独立 Go STE 检查器与 MCP 实现）。** [仓库](https://github.com/stuffbucket/vale)；[固定 README](https://github.com/stuffbucket/vale/blob/d96df3eb63f174b6933e29f3d97d4f17e74ab7c3/README.md)。用途：作用域解析、可诊断规则、CLI/MCP 接口和参考词表来源登记。与 R04 分开；本次读取 README、根 LICENSE、随仓库保存的 OpenSTE LICENSE 和 PROVENANCE.txt，未审计全部实现或重新核对 OpenSTE 上游。

## 2. 固定的参考快照

下表于 2026-10-24 核对本地 `HEAD`、README 和根 LICENSE。五个根许可证均声明 MIT；这只说明所读许可证文本，不将 ASD-STE100 标准正文、字典或其他第三方内容自动纳入同一授权。README 所述功能未经上游代码执行验证。

| 来源 | 本地子模块 | 固定提交 | 本次阅读范围 |
|---|---|---|---|
| R01 | [asd-ste100-skill](../submodules/asd-ste100-skill/README.md) | `cd62d297d5ef7cf9f59718cadc233ab2876ea013` | README、LICENSE、SKILL 元数据与模态保留条款 |
| R02 | [SimpleEnglish](../submodules/SimpleEnglish/README.md) | `a6fcb4fde098b33617cc1578d151ebf58774b883` | README、LICENSE、SKILL 元数据与模态词限制 |
| R03 | [ste](../submodules/ste/README.md) | `922c9773d0004f4c40b2e1373db9ed949321373d` | README、LICENSE；未读取完整实验轨迹 |
| R31 | [ste-prompt](../submodules/ste-prompt/README.md) | `f59ae8de5497c81ece60e0a8fac11fe6a54d3777` | README、LICENSE；未测试安装入口 |
| R32 | [vale](../submodules/vale/README.md) | `d96df3eb63f174b6933e29f3d97d4f17e74ab7c3` | README 中用途、接口、作用域与许可说明；根及 OpenSTE LICENSE、OpenSTE PROVENANCE.txt |

R32 的根 LICENSE 另列 OpenSTE 的 MIT 归属；本地 PROVENANCE.txt 记录 `19f01781a6162246ac56d4cab84835842609a31c`。这项记录只核实随仓库保存的声明，不证明该上游提交或词表内容已经独立审计。

各已读文件的 SHA-256、Git blob 身份、固定链接和许可入口保存在 [机器索引](../sources.json)。SHA-256 对应本机检出的原始字节；跨平台换行转换可能改变该哈希，Git 提交和 blob 身份用于核对上游版本。子模块内容不并入运行时 Skill，不参与当前工作流。
