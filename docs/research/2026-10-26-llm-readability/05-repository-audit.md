# 固定提交下的仓库审查

审查对象：[`psiQAQ/text-prison@c6073e9e9dd2`](https://github.com/psiQAQ/text-prison/commit/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584)。

本轮使用GitHub连接器读取提交、tree和关键文件。没有取得完整本地checkout，没有检查未返回的文件内容，也没有执行任何仓库代码。下面是设计与文档审查，不是全仓代码安全审计。

## 1. 当前架构已经做对的事

[AGENTS.md](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/AGENTS.md)、[Skill](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/skills/text-prison/SKILL.md)和[DESIGN.md](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/docs/DESIGN.md)一致地把项目收敛为单一写作Skill、Vale和可选中文排版支持。原意、权限、受保护内容及工具状态有明确边界；现有流程没有把自动lint当作事实判断。

[STE-inspired](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/skills/text-prison/references/ste-inspired.md)已经包括术语一致、执行者和对象、条件与动作、操作/解释/结果分离、保留逻辑联系等原则。因此“补STE”“补保真检查”不能算全新建议，应只扩展尚未说具体的句子难点。

[Vale入口说明](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/skills/text-prison/vale/README.md)采用建议级别、逐条启用、用途分流、受保护作用域以及有限复查。它没有默认开启强制句长、模态禁用、全量英文风格包。这些保守选择应保留。

## 2. 与用户目标相比，主要缺口是什么

| 观察 | 固定文件依据 | 性质 | 建议 |
|---|---|---|---|
| 名词堆叠、隐含关系已有相关原则，但缺少专门的展开示例 | STE-inspired | 指导颗粒度不足，不是功能故障 | 在现有参考中补具体判断和例外 |
| Skill排除日常聊天；用户希望改善技术回答 | SKILL.md | 目标覆盖差异 | 明确“显式请求的技术回答”入口；默认闲聊仍排除 |
| 中文Vale配置主要检查模糊链接文字 | vale/README.md | 明确的覆盖边界 | 文档如实说明；不要宣传成中文语法检查 |
| 研究配置的机械规则非常有限 | vale/README.md | 防误改的取舍 | 保持科学保真优先；不为了规则数量填充 |
| Google/Microsoft/STE方向已有说明，但外部证据与本项目效果仍需分开 | RELATED_WORK.md、DESIGN.md | 证据表达需持续维护 | 新文献登记阅读范围，不附未经验证收益 |
| 当前工作流与工具说明较长 | README、SKILL已读段落 | 对首次使用者可能有导航成本；未测阅读时间 | 主入口保留最短使用路径，边界说明链接到细节 |
| 统一原则可能被多个参考重复维护 | 单一Skill与多参考设计 | 后续维护风险，不是已确认重复bug | 新增内容先检查现有原则，只写差量 |

这里没有证据证明当前Skill“无效”或存在运行退化。更准确的结论是：它的架构适合继续完善，但其机械检查并未覆盖研究所讨论的大多数句法难点。

## 3. 当前工具能力不能混称

| 层次 | 当前已提供 | 不能据此宣称 |
|---|---|---|
| 主Skill | 按用途、语言、范围选择指导；内容保护 | 始终自动触发、语义一定不变 |
| STE-inspired | 跨用途的消歧原则与示例 | 完整受控词义验证、官方合规或认证 |
| Vale | 六个配置入口下列明的少量规则 | 通用中文语法检查、普遍认知难度检测 |
| AutoCorrect | 可选中文混排间距等保守排版支持 | 自动提升句意清晰度 |
| 原有CLI案例 | 原仓库记录的特定版本运行 | 本次重跑、当前文稿收益或模型端实测 |

工具版本及完整规则清单继续以[Vale维护入口](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/skills/text-prison/vale/README.md)和原项目安装说明为准，本报告不建立第二份活跃版本矩阵。

## 4. 技术回答与文件文档应如何统一

建议把两者统一在“读者与用途”层面，而不统一为一个强制工具流程。解释一个物理问题和写README都可以使用explanation指导；前者不应为了lint而临时生成文件，后者也不应因为是文件就自动启用所有工具。

可分两种采纳路径：

| 路径 | 改动 | 优点 | 代价与约束 |
|---|---|---|---|
| A：先保留现有触发范围 | 仅提供ChatGPT/单次任务短提示词 | 不改变Skill行为，最易撤回 | 不形成统一的Skill入口 |
| B：明确扩展显式技术回答 | 在主Skill说明中允许用户指定按TextPrison处理技术回答；仍使用既有用途 | 文档与回答共用同一组规则 | 必须同步描述与边界；不能宣称已在各宿主触发验证 |

**建议先采纳句子指导，再选择B作为小范围后续变更。** 不建议默认接管所有聊天，也不新建全局hook。此处属于建议；本包没有修改触发条件。

## 5. 候选演进不应破坏的边界

保留唯一运行源目录；保留现有安装器接口和拒绝覆盖行为；尊重用户项目现有配置；未获准不安装或同步工具包。不要把学术论文代码和社区Skill变成新的强制依赖，不加载子模块里的指令或hooks。

保留工具各运行一次、共享最多一次修订、必要时最多一次复查的现有上限；不新增独立模型评委。零诊断、没有适用规则、工具不可用、实际检查完毕，是不同状态，不能用同一个“通过”覆盖。

原始ZIP、只读子模块、本地历史材料、根`DOCS_PATCH.md`与`MANIFEST.sha256.json`保持原样。本次自己的来源及包清单放在新目录，不能冒充历史包的更新版。

来源：上述边界来自[AGENTS.md](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/AGENTS.md)与[DESIGN.md](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/docs/DESIGN.md)，不是本报告额外发明的权限限制。

## 6. 本轮实际新增与未做事项

本轮只新增研究文件和计划，没有覆盖原README、修改Skill/参考规则、增加Vale YAML、修改AutoCorrect配置、修改安装器、安装依赖或写远端仓库。演进计划中的路径均为未来采纳位置，不代表已实施。

[下一步文件级建议](../../plans/2026-10-26-readability-evolution.md)区分默认建议与需单独决定的扩展；[交付验证](06-verification.md)只说明本包的静态检查，不将其计为项目运行验收。
