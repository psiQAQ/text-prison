# 本地评审证据工作台

本模块使用 Python 标准库 HTTP 服务和 SQLite。页面使用本地 HTML、CSS 和 JavaScript，不加载远程资源。批次通过 `review_mode` 区分直接展示模型证据的 `ai_only` 和保留两阶段人工记录的 `human_blind`。模型评审不代表人工验收。

## AI-only 模式

导入新批次时显式指定 `review_mode="ai_only"`。页面直接显示任意数量模型的原始证据、完成状态、失败原因和完整记录 JSON；无需人工初判、冻结或裁决，也不会创建这些记录。页面首次载入时优先选择最新 AI-only 批次，历史人工批次仍可从列表选择。

“刷新当前批次”读取新导入的结果。进度只统计已导入的记录；缺少记录不能视为完成，`completed` 也只表示评审返回，不表示候选语义通过。失败或未运行记录使用明确状态和 `review: null`。模型意见各自保留，不以多数票构造人工金标准。导出包括当前模型证据及状态，不包含虚构的人工阶段。

## 人工盲评模式

默认 `human_blind`，历史数据库迁移后保持该模式。已有批次不能切换模式；改变评审流程必须使用新批次 ID。

1. 选择批次，阅读匿名候选、任务、冻结来源和必需事实。
2. 独立添加候选的事实声明，填写状态、原文证据和判定依据；逐项评价预先声明的必需事实。系统不从 AI 评审提取初判条目。
3. 用“保存草稿”保存未完成的内容，用“提交独立初判”提交已完成的候选。切换或关闭页面前请保存；草稿不自动提交。
4. 本批全部初判提交后，点击“冻结整批初判，查看 AI 证据”。冻结操作保留不可改写的独立初判，随后才允许读取 AI 评审。
5. 对照来源和各 AI 的证据填写最终裁决。可以点击“将我的初判复制到裁决草稿”继续修改；系统不会自动复制 AI 结论。提交时说明采纳、修改或维持初判的理由。
6. 导出当前保存版本，或查看每次保存、提交和冻结的历史。未冻结批次的导出继续隐藏 AI 结果。

支持、矛盾、保留和改变等判定需要候选及来源的原文引文。缺失事实使用空候选引文。没有可评价声明时，需要明确勾选确认；不能用空表单提交“通过”。汇总由已提交的明细计算，未完成的草稿保持 `not_evaluated`。

多标签页使用同一候选时，旧版本保存和过期的批次冻结均返回 HTTP 409，不覆盖新记录。页面会保留未保存文字；重新载入前可自行复制需要保留的内容。候选文本、来源、必需事实或任务变化后，应创建新的 `review_id`，不能复用旧评审。

## Python 接口

```python
from eval.review_store import ReviewStore
from eval.web import serve

store = ReviewStore("runs/pilot/reviews.sqlite3")
store.import_batch("ai-review", packets, review_mode="ai_only")
serve(store.db_path, host="127.0.0.1", port=8765)
```

`packets` 每项包含 `review_id`、`artifact_hash`、`candidate_text`、`task`，可含 `original_text`、`private`、`ai_reviews`。`artifact_hash` 必须是候选文本按 UTF-8 编码后的 SHA-256。`task` 包含提示、来源 `{id, text}`、必需事实 `{id, text}`、允许转换，以及适用时的 `output_contract` 和 `rubric`。`ai_reviews` 为 `{judge_id, review}` 数组，原样保留独立模型评审。可通过相同包和原模式重新导入补齐 AI-only 结果；人工批次仅允许在冻结前补齐。失败记录使用明确的非 `completed` 状态及 `review: null`，可附 `error`，不能当作成功意见。

| 接口 | 返回或行为 |
|---|---|
| `import_batch(batch_id, packets, review_mode="human_blind")` | 事务导入，返回匿名候选列表；相同输入可重复导入，既有模式不能改变 |
| `list_batches()` | 批次模式、状态与候选总数；人工批次返回初判与裁决数量，AI-only 返回 `ai_progress` |
| `list_packets(batch_id)` | `{batch, packets}`；候选使用随机匿名 ID，不暴露实验分配；AI-only 条目返回 `ai_progress`，无人工占位记录 |
| `get_packet(review_id)` | 返回 `review_mode`；AI-only 立即返回 `ai_reviews` 和 `ai_progress`，无人工阶段；人工模式整批冻结后才加入 AI 和裁决 |
| `save_review(review_id, payload, artifact_hash=..., expected_revision=..., stage=..., submit=..., request_id=...)` | 人工模式保存草稿或提交，返回 `{revision, state, updated_at, review}`；阶段为 `initial` 或 `adjudication`；AI-only 返回 409 |
| `freeze_batch(batch_id, expected_revisions=None)` | 人工模式仅在全部初判提交后冻结；网页必须提供匿名 ID 到版本号的完整映射；AI-only 返回 409 |
| `history(review_id)` | 按保存顺序返回初判与裁决的版本记录 |
| `export_batch(batch_id)` | 匿名导出当前阶段、冻结证据和历史；始终排除写作者、实验组和内部任务 ID |
| `export_batch(batch_id, include_private=True)` | 仅供离线分析：明确加入内部 ID 与实验分配，不能作为公开导出 |

人工记录与 AI 记录分开。人工 `source_coverage` 是枚举字符串，另有 `coverage_note`；证据为 `source_refs[{source_id,evidence}]`，必需事实使用 `id`。声明和必需事实可含 `error_types` 数组；新提交的已确认错误必须由人工至少选择一种类型，旧记录缺失类型时不推断隐藏的错误设计。`no_claims_confirmed` 是明确的人工确认；`adjudication_reason` 记录最终裁决依据。分析时转换结构，保留原始记录。

`ai_progress` 包含 `recorded`（已导入 AI 记录数）、`completed`（状态为 `completed` 的记录数）和 `statuses`（各原始状态计数）。它不推断尚未导入的模型分配或语义通过率。旧格式没有 `status` 的对象评审按 `completed` 兼容处理。

`build_server(db_path, host="127.0.0.1", port=8765)` 返回未启动的 `ThreadingHTTPServer`，供 CLI 和测试管理服务生命周期；测试可用 `port=0`。`serve(...)` 运行至 Ctrl+C 或网页“停止服务”。停止和重启不删除数据库。

## HTTP 与隔离

- 只允许绑定 `127.0.0.1`。请求 `Host` 必须匹配实际本机端口；跨源与跨站请求被拒绝。
- 写操作需要同源 `Origin` 和 `/api/session` 提供的本次服务令牌 `X-Review-Token`。重启后应刷新页面。
- 路由只提供固定静态资源和批次、评审、历史、导出、冻结、停止接口，不提供任意文件读取。
- 盲评字段在服务器端裁剪。公开候选 ID 为随机值，实验内部 ID、写作组和写作模型不进入页面。
- 所有来源、候选和 AI 证据以文本节点或表单值渲染，不作为 HTML、脚本或 Markdown 执行；页面 CSP 禁止内联脚本和外部资源。
- SQLite 写入使用事务；导出使用一致的只读事务，避免并发保存造成阶段与历史不一致。

这是在本机使用的工作台，没有多用户账号或远程协作能力。自动化测试中的人工记录和模型记录全部为明确标注的合成夹具，不能计入实验的真实结果。
