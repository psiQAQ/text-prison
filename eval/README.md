# 评测资料：文档协议 v0.2，运行时 schema v0.1

这里是实验设计与记录接口，不是已运行的 Benchmark。本次只更新 Markdown。原型没有原生宿主 runner、usage 适配器、正式任务集、人工实验结果或 Token 节省数据。

## 阅读顺序

| 文件 | 作用 |
|---|---|
| [相关研究](../docs/RELATED_WORK.md) | 相近实现、论文方法、可借鉴与不可外推之处 |
| [PROTOCOL.md](PROTOCOL.md) | A/B/C/D、必要的 C+ 反馈消融、独立执行与原生触发 |
| [METRICS.md](METRICS.md) | 精确分母、FSP/RFR、理解、执行、触发、成本、缺失与区间 |
| [PREREGISTRATION.md](PREREGISTRATION.md) | 正式运行前冻结的风险界值、样本、统计与失败政策 |
| [语义审查模板](prompts/semantic-review.md) | 逐事实/逐编辑证据，不输出总质量分 |
| [实现差量](../docs/IMPLEMENTATION_DELTA.md) | 按现有路径安排下一阶段修改 |

## 使用边界

正式结论需要三条相互独立的证据：原始任务和来源、真实产物/动作/usage、预先冻结的评分与统计。风格检查器不是事实评委；模型评委不是人类读者；任务通过也不代表自动触发成功。

`run.schema.json` 仍是 0.1：允许 A/B/C/D/C+，但没有本次规划的新采集语义。新增反馈消融区块、外部基线或账单字段前，按实现差量迁移 schema；开发侧车不要冒充已稳定接口。

源包的 `validation/` 仅验证当时的检查器/安装器。不要将其纳入理解、Agent 成功率或 Token 效果表。没有真实数据时不生成结果页。
