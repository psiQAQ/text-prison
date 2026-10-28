# TextPrison 可读性调研与演进建议

日期：2026-10-26。审查基线：[`c6073e9e9dd2`](https://github.com/psiQAQ/text-prison/blob/c6073e9e9dd2f66c6e823c9dfc9818ea641bd584/AGENTS.md)。

**推荐方向：保留单一 Skill、Vale 和可选 AutoCorrect，补足“让读者看清对象与关系”的写作指导，而不是增加一批检查器或强制压缩字数。**

原始交付是文档增量包，按仓库根目录组织路径。2026-10-26 本地整理时将本入口移入研究目录；后续获准的 P0＋P1 改动及核对结果见[实施记录](../../plans/2026-10-26-readability-evolution.md)。原 ZIP 与包清单保留为原始输入，不代表整理后的工作区文件或当前 Skill 行为。

| 阅读目的 | 文档 |
|---|---|
| 查看主要结论、问题和适用方案 | [调研报告](01-report.md) |
| 从原论文引用追踪相关研究 | [17 篇文献地图：种子论文、8 篇直接引用、8 篇扩展](02-literature.md) |
| 比较开源工具和论文代码 | [工具选型](03-tools.md) |
| 立即复制一段写作提示词 | [提示词与编辑示例](04-prompts.md) |
| 了解原基线下的能力与缺口 | [固定提交审查](05-repository-audit.md) |
| 查看关于 AI 文本可读性与稳定控制的对话记录 | [讨论记录](08-discussion-on-ai-readability-control.md) |
| 查看本次采纳范围及实施情况 | [P0＋P1 实施记录](../../plans/2026-10-26-readability-evolution.md) |
| 核对阅读范围、文献获取和包清单 | [交付说明](README.md)及[验证记录](06-verification.md) |

报告中的研究建议不等于已验证效果；具体采纳状态以实施记录为准。文献全文仅存放在 Git 忽略的 `docs/reference/2026-10-26-llm-readability/`，文件版本、来源与摘要登记在 [sources.json](sources.json)。下载不等于全文审读或实验复现。

原包再次解压会恢复旧路径，并可能覆盖整理后的同名文档，应用前应先保全本地修改。固定提交审查和原包检查只说明各自记录的对象；不能据此推定新版本已验证。
