# 文献地图：从语言难度到可控改写

范围：1篇种子论文、8篇该论文直接引用的研究、8篇本次沿主题扩展的研究。不是完整参考文献重排，也不是穷尽式系统综述。直接引用关系来自种子论文的References；扩展项不冒称被它引用。逐条阅读范围见[sources.json](sources.json)。

本地已取得这 17 篇论文的 PDF，下载版本与文件摘要见来源表的 `local_copy`；正文保存在 Git 忽略的 `docs/reference/2026-10-26-llm-readability/`。下方继续使用公开外部链接。文件解析和身份核对不等于全文审读；正式版与作者稿不同之处单独注明。

**优先阅读顺序建议：P00 → P03 → P06 → E01 → E06 → E07。** 这条路线先认识现象和反例，再确定改写方法与证据边界。只关心中文时加读E08；只关心模型训练时加读P05。

## 一、种子论文

### P00 · Why is AI-generated language so hard to understand?（2026，预印本）

[摘要和版本](https://arxiv.org/abs/2610.29162) · [正文、附录与完整引用目录](https://arxiv.org/html/2610.29162v1) · [PDF](https://arxiv.org/pdf/2610.29162)

本次关注的起点。主要判断及限制集中写在[调研报告第2节](01-report.md)，这里不重复其样本和结果。阅读时应区分描述性比较、带长度惩罚的机制示例，以及作者提出的解释假说；三者的证据强度不同。

## 二、种子论文直接引用的8篇研究

### P01 · Do LLMs write like humans? Variation in grammatical and rhetorical styles（2025，PNAS）

[出版社正文](https://www.pnas.org/doi/10.1073/pnas.2422455122)

研究比较模型与人类的语法、修辞风格，揭示模型输出的名词化倾向以及文体差异。它帮助解释为什么“语法正确”仍可能让读者感到生硬。

**边界与采用：** 风格差异不自动等于理解失败。TextPrison宜根据README、研究说明或操作文档分别调整表达，不宜设一个跨文体通用的“人类风格分数”。这是工程推论，不是论文已经验证的产品方案。

### P02 · Why Does ChatGPT “Delve” So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models（2025，COLING）

[正式出版页与 PDF](https://aclanthology.org/2025.coling-main.426/) · [作者预印本](https://arxiv.org/abs/2412.11385)

研究一组在LLM文本中过度出现的词，并探讨人类反馈等来源。它提示所谓“AI味”可能来自偏好和词汇分布，而不仅是句子太长。

**边界与采用：** 不能由个别词的过度使用推出这些词永远有错。项目可减少无信息套话，但不建议建立一张全局“AI词禁用表”，更不能用同义词轮换破坏技术术语的一致性。

### P03 · A Long Way to Go: Investigating Length Correlations in RLHF（2024，COLM）

[论文与接收信息](https://arxiv.org/abs/2310.03716)

研究在多个RLHF设置中发现，输出变长会显著影响奖励，奖励模型容易受偏好数据的长度偏差影响。

**边界与采用：** 这不是“所有RLHF都喜欢长文”的定律，但足以反对“强化学习必然压缩输出”的概括。不要把字数增减本身作为TextPrison成功的方向性指标；更不能因为模型回答更短，就断言它更清楚。

### P04 · Revisiting the Uniform Information Density Hypothesis（2021，EMNLP）

[论文出版页](https://aclanthology.org/2021.emnlp-main.74/)

研究用阅读时间和可接受性数据检验均匀信息密度假说，并比较不同量化方式与作用范围。

**边界与采用：** “分布较均匀”不是“信息越少越好”，不同定义也不等价。可以借鉴的写作直觉是避免把多个新概念和关系挤在一个位置；不能据此制定统一每句字数或每词惊异度阈值。

### P05 · Uniform Information Density-Based Preference Optimization（2026，arXiv 预印本）

[论文正文](https://arxiv.org/html/2610.14578v1) · [作者代码](https://github.com/CLCS-SUSTech/UIDPO)

本地下载的 arXiv v1 首页标注“Preprint. Under review.”。种子论文书目将其列为 Third Conference on Language Modeling，但本次 [OpenReview 条目](https://openreview.net/forum?id=7PEYAPbjtN)访问受限，未独立核实会议录用；不把下载稿标成已核实的会议正式版。

将全局信息波动与局部变化纳入偏好优化目标，并报告偏好基准及语言分析结果。它把信息分布从解释概念推进到模型训练目标。

**边界与采用：** 这是需要训练的算法，不是Skill、API参数或提示词模板。偏好基准提升不等于目标读者阅读更快。作者仓库的许可尚未核清，当前不建议复制代码或作为运行依赖；可保留为训练侧研究参考。

### P06 · Poor writing, not specialized concepts, drives processing difficulty in legal language（2022，Cognition）

[正式论文DOI](https://doi.org/10.1016/j.cognition.2022.105070) · [作者摘要页](https://mollicaf.github.io/publication/martinez-202-xwhat/)

研究结合语料比较与读者实验，考察嵌套句法等特征对记忆、理解的影响。2026-10-26 核对的[正式发表版公开副本](https://www.pure.ed.ac.uk/ws/portalfiles/portal/256304933/Poor_Writing_MARTINEZ_DOA17022022_VOR_CC_BY_NC_ND.pdf)摘要报告两项实验，总 N = 184；作者网页仍保留 108 人的旧摘要，不能将该数当成正式版的总样本量。研究提示专业文本的困难不能全部归因于读者不懂术语。

**边界与采用：** 法律文本、读者与任务均有特定范围。可借鉴“先改善组织，再判断是否解释术语”，不可照搬效果量，也不能将所有技术概念改成日常近义词。

### P07 · Large-scale evidence of dependency length minimization in 37 languages（2015，PNAS）

[出版社页面](https://www.pnas.org/doi/10.1073/pnas.1502134112) · [更正](https://pmc.ncbi.nlm.nih.gov/articles/PMC4655573/)

研究跨语言语料中的依存长度倾向，为“相关词尽量靠近”提供背景。出版社页面列有后续更正，本次不重新引用或核算其表格结果。

**边界与采用：** 跨语言分布规律不是每句话的硬标准。可优先处理隔断主语和动作的长插入语；不宜给中文、公式或API名称统一设距离上限，也不宜用解析器结果自动拆句。

### P08 · Why Does Surprisal From Larger Transformer-Based Language Models Provide a Poorer Fit to Human Reading Times?（2023，TACL）

[论文出版页](https://aclanthology.org/2023.tacl-1.20/)

研究发现，所测更大模型给出的惊异度未必更贴近人类阅读时间，并分析了命名实体与功能词等类别上的偏差。

**边界与采用：** 不能把大模型的逐词概率直接换算为读者脑力负担。若未来独立开发“难读位置高亮”，应标为模型估计而非精确认知测量；当前仓库不引入这类新后端。

## 三、沿主题扩展的8篇研究

以下E类文献不在本次核对的种子论文参考书目中。部分已由TextPrison旧书目登记，本轮重新核对了出版摘要；不把已有条目包装成全新发现。

### E01 · Controllable Sentence Simplification / ACCESS（2020，LREC；预印本2019）

[正式出版页与 PDF](https://aclanthology.org/2020.lrec-1.577/) · [作者论文](https://arxiv.org/abs/1910.02677)

ACCESS分别控制长度、改写程度、词汇复杂度和句法复杂度，使简化围绕受众需求，而不是生成一个适合所有人的版本。

**问题与解法：** “写简单点”没有说明究竟要删内容、换词还是调整结构。可把任务改为“保留专业术语和信息，只拆开修饰关系”。该提示词是对论文思想的工程迁移，不是复现ACCESS的训练或分数。

### E02 · MUSS: Multilingual Unsupervised Sentence Simplification by Mining Paraphrases（2022，LREC）

[论文](https://aclanthology.org/2022.lrec-1.176/) · [代码](https://github.com/facebookresearch/muss)

利用挖掘的改写数据训练句子简化模型，并在生成时控制长度、词汇复杂度等属性。论文在英语、法语和西班牙语上报告结果。

**问题与解法：** 专门模型提供可控改写路径，但论文语言覆盖不包括中文效果保证。当前README还保留旧Python兼容性提示；不适合直接当作TextPrison的轻量依赖。保留思想与文献入口，不增加部署工作。

### E03 · BLESS: Benchmarking Large Language Models on Sentence Simplification（2023，EMNLP）

[论文](https://aclanthology.org/2023.emnlp-main.821/) · [代码](https://github.com/ZurichNLP/BLESS)

在百科、新闻和医疗领域的少样本设置中比较44个模型，结合自动指标和部分人工分析观察简化能力与编辑类型。

**问题与解法：** 提示条件、模型和领域都影响结果，不能从一条成功示例推出跨模型稳定性。可借鉴少量有针对性的编辑示例，但不把整个基准引入当前仓库，也不据此替当下GPT版本排名。

### E04 · Optimizing Statistical Machine Translation for Text Simplification / SARI（2016，TACL）

[论文](https://aclanthology.org/Q16-1029/)

该工作提出面向简化任务的评价思路，SARI关注源文本与参考简化文本中的保留、删除和添加操作。

**问题与解法：** 适合特定输入—参考条件的编辑指标，不是随便输入一篇README就能得到的通用可读性分数。原始问答缺少对应参考简化文本时尤其不应强用。本项目只保留书目，不安装评分流程。

### E05 · LENS: A Learnable Evaluation Metric for Text Simplification（2023，ACL）

[论文](https://aclanthology.org/2023.acl-long.905/) · [上游项目](https://github.com/Yao-Dou/LENS)

用人工评价数据训练简化质量指标，强调与人工判断的相关性。它是评价模型，不是改写模型。

**问题与解法：** 原版LENS不能与后续的无参考LENS-SALSA混称；训练数据和语言范围也限制外推。可用来理解“为什么单看句长不足”，不应成为当前中文科研说明的验收分数。常见的`davidheineman/LENS`链接是上游的fork，本报告指向`Yao-Dou/LENS`。

### E06 · Dancing Between Success and Failure: Edit-level Simplification Evaluation using SALSA（2023，EMNLP）

[论文](https://aclanthology.org/2023.emnlp-main.211/) · [代码](https://github.com/davidheineman/salsa)

提出细粒度编辑标注框架，区分词汇、句法、概念层面的成功与失败，并训练LENS-SALSA。

**问题与解法：** 一个整体看似更顺的改写，可能同时含有正确改进与错误删除。项目可借鉴“逐项看实质修改及信息损失”的复核思路，不必引入标注工具、额外模型调用或标注数据集。

### E07 · Adapting Sentence-level Automatic Metrics for Document-level Simplification Evaluation（2025，NAACL）

[论文](https://aclanthology.org/2025.naacl-long.327/)

研究把句子级指标适配到段落和文档，检验其对错误的敏感性。论文指出常见句子级指标用于长文本时可能表现不佳。

**问题与解法：** 每句话容易读不代表整篇文档容易用。TextPrison的改写仍应保留跨段指代、推导次序和任务结构；无需为此引入综合评分仪表盘。

### E08 · MCTS: A Multi-Reference Chinese Text Simplification Dataset（2024，LREC-COLING）

[论文](https://aclanthology.org/2024.lrec-main.969/) · [代码与数据](https://github.com/blcuicall/mcts)

提供中文多参考简化数据、方法比较及通过翻译获得的平行数据，补充长期偏重英文的研究材料。

**问题与解法：** MCTS在这里是数据集名称，不是蒙特卡洛树搜索。数据集也不等于完整中文语法或科技写作规则。可关注中文的多种合理表达，不能把与单一参考答案的接近度当成唯一正确标准。

## 四、少量可核查的研究规模

只列已在本轮读取的官方或作者摘要中出现的数据，不从摘要反推未阅读的实验细节。

| 研究 | 数据或范围 | 如何使用这些数字 |
|---|---|---|
| P06 | 语料约 1000 万词；正式版摘要报告两项实验，总 N = 184 | 采用正式发表版摘要；作者网页的 108 人旧摘要另行标注，不是中文技术文档的收益数值 |
| E03 | 44个模型；3类领域 | 显示比较覆盖面，不是当前模型排行榜 |
| E06 | 21类编辑；约1.9万条编辑标注；840个简化结果 | 支持细粒度错误分析，不是TextPrison已完成的检查 |
| E02 | 英语、法语、西班牙语 | 划清论文实际验证语言，不外推中文 |

## 五、这些论文没有回答的项目问题

当前GPT在你的光学和软件说明中，使用哪一组提示词最稳定；中文段落应在何种条件下拆句；哪些新增规则值得付出误报成本——这些都没有被上述文献直接解决。本报告给出的候选提示和文件计划属于有依据的工程建议，不是现成的实证结论。

因此，本轮不输出“提高可读性X%”“降低阅读时间Y%”或模型优劣排名，也不因引用了评测论文就恢复仓库的实验代码。
