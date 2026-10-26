# 项目扫描器与语料测量工具选型（只读研究）

调查时间：2026-10-26。此表不是兼容性或安装试验；未对各仓库运行程序，许可须以实际采用的版本及模型文件为准。“引入”不等于复制代码或开启其 hooks。

| 项目 | 上游仓库或官方页 | 检测类型 | 语言 | 结论 | 边界 |
|---|---|---|---|---|---|
| [Vale / 当前已用](https://github.com/vale-cli/vale) | [源码](https://github.com/vale-cli/vale) | 中英 Markdown 文风、术语、固定模板 | 现有 | 建议、默认保留 | 保留唯一通用扫描入口；新规则需有作用域例外 |
| [AutoCorrect / 当前可选](https://github.com/huacnlee/autocorrect) | [源码](https://github.com/huacnlee/autocorrect) | 中西文混排、排版 | 现有 | 建议、默认不扩大 | 不等于中文语法或语义 |
| [Vale Std](https://github.com/vale-cli/Std) | [源码](https://github.com/vale-cli/Std) | 句长、缩写、英文被动、标点 | 英语 | P1 可选 | 依赖 Vale≥3.20；需按授权同步，不默认启用被动否定规则 |
| [retext-readability](https://github.com/retextjs/retext-readability) | [源码](https://github.com/retextjs/retext-readability) | 传统英文可读性分数 | 英语 | 参考/P2 | Flesch 等公式不适用于中文，不证明语义正确 |
| [retext-simplify](https://github.com/retextjs/retext-simplify) | [源码](https://github.com/retextjs/retext-simplify) | 英文冗长短语诊断 | 英语 | 参考/P1 | 可将部分规则改写为自有 Vale；注意修辞例外 |
| [textlint](https://github.com/textlint/textlint) | [源码](https://github.com/textlint/textlint) | 规则插件化检查 Markdown | 取决于插件 | 不建议再添默认引擎 | Node 依赖/与 Vale 重复，只有独特规则才值得单独选用 |
| [Harper](https://github.com/automattic/harper) | [源码](https://github.com/automattic/harper) | 本地英文语法拼写 | 英语 | P2 手动选用 | 对科研术语、缩写需词表；不解决中文篇章逻辑 |
| [LanguageTool](https://github.com/languagetool-org/languagetool) | [源码](https://github.com/languagetool-org/languagetool) | 多语言语法/措辞、可自建 | 视语言规则 | P2 手动选用 | Java 服务更重、不同语言覆盖不等 |
| [pycorrector](https://github.com/shibing624/pycorrector) | [源码](https://github.com/shibing624/pycorrector) | 中文错字及模型语法纠错 | 中文 | P2 手动选用 | 有的模型依赖大体积文件且可能联网下载；绝不自动改专名 |
| [sloptrim](https://github.com/seyedehsanhadi/sloptrim) | [源码](https://github.com/seyedehsanhadi/sloptrim) | 英文 AI 模板模式定位 | 英语 | P1 借鉴规则 | Apache-2.0；包含 hooks/得分，但不继承；不是作者鉴定 |
| [sloptrim-cn](https://github.com/pakco77/sloptrim-cn) | [源码](https://github.com/pakco77/sloptrim-cn) | 中文 24 个机器可检 AI 腔模式 | 中文 | P1 借鉴规则 | Apache-2.0；项目新且低流行度、存在误报；不启用 hooks/得分 |
| [renhua](https://github.com/RiAnBee/renhua) | [源码](https://github.com/RiAnBee/renhua) | 中文保义润色 Skill | 中文 | 仅参考 | 不是机械检查器，和 TextPrison 核心能力重叠 |
| [humanizer-zh](https://github.com/syw2039/humanizer-zh) | [源码](https://github.com/syw2039/humanizer-zh) | 个人文风与模板腔写作指导 | 中文 | 仅参考 | 属于 Agent 提示 Skill，不能替代可验证检查 |
| [TextDescriptives](https://github.com/HLasse/TextDescriptives) | [源码](https://github.com/HLasse/TextDescriptives) | 句长、POS、依存长度、相邻句连贯性 | 依赖 spaCy 模型 | P2 离线研究 | Python/spaCy；中文指标可计算但读数不一定已校准 |
| [BiberPlus/Neurobiber](https://github.com/davidjurgens/biberplus) | [源码](https://github.com/davidjurgens/biberplus) | 96 英语句法/修辞风格特征 | 英语 | P2 离线研究 | Python/spaCy/可选 GPU 模型；不适合每次对话 |
| [pybiber](https://github.com/browndw/pybiber) | [源码](https://github.com/browndw/pybiber) | Biber 风格分类计数 | 英语 | P2 对比参考 | 指标方案与 BiberPlus 有差异，不等于真人评分 |
| [LingFeat](https://github.com/brucewlee/lingfeat) | [源码](https://github.com/brucewlee/lingfeat) | 255 项词汇句法篇章可读性特征 | 英语 | 研究参考 | 依赖多，其中高级语义在仓库自述有问题 |
| [LexicalRichness](https://github.com/LSYS/LexicalRichness) | [源码](https://github.com/LSYS/LexicalRichness) | MATTR、MTLD、词汇丰富度 | 分词后可用 | P2 研究参考 | 中文分词质量与 token 定义决定结果 |
| [HanLP](https://github.com/hankcs/HanLP) | [源码](https://github.com/hankcs/HanLP) | 中文分词、词性、依存/语义模型 | 中英 | P2 有需求才接入 | 代码与模型的许可分别核查，模型较重 |
| [Stanza](https://github.com/stanfordnlp/stanza) | [源码](https://github.com/stanfordnlp/stanza) | 中文等多语词法与依存解析 | 多语 | P2 有需求才接入 | 模型下载和推理成本；离线资源许可单独核查 |
| [TAACO](https://soletlab.asu.edu/taaco/) | [源码](https://soletlab.asu.edu/taaco/) | 150+ 篇章衔接指标 | 英语研究工具 | 方法论参考 | 公开可用不等于开源许可已确认 |
| [AlphaReadabilityChinese](https://github.com/corpustalk/AlphaReadabilityChinese2.0) | [源码](https://github.com/corpustalk/AlphaReadabilityChinese2.0) | 中文词法、依存及篇章难度指标 | 中文 | 仅方法论参考 | 看到桌面发行物，不将其视为代码开源/许可证已确认 |

## 判断开源工具质量时必须区分

1. **代码开源、模型权重、语料库、词典**可能属于四种不同许可；不要仅凭 README 写“free”就转存权重或词库。
2. **文字模式检出率 ≠ 读者理解率 ≠ AI 来源鉴定准确率**；sloptrim 公开的 matched ROC-AUC 在不同模型/改写条件下差异明显，不宜把其数值外推到中文或 GPT-6。
3. 若需要用户真实成效，应该由独立的授权读者研究验证，而非临时在仓库重建已退役的评测基础设施。
4. `pycorrector` README 说明默认统计语言模型可能在首次使用时下载约 2.8 GB 文件；这类潜在联网及依赖成本不能隐含在日常 TextPrison 工作流里。
5. 对 Vale 优先转译**少量可解释、低误报、可定位**的通用模式；高阶 NLP 建议作为离线可选参考，不进入每次生成响应的关键路径。
