# v0.3 六模型探索性试跑结果

实验：`ai-six-20261025`；源汇总时间：`2026-10-24T19:37:57.873768+00:00`；导出时间：`2026-10-24T19:38:05.055321+00:00`。

导出范围：`partial`。计划分配 263 项，已留存尝试 255 次；CLI 已用 255/276 次、9114.79/14400 秒，待结算调用 0。调用数和耗时包含继承记录、失败、重试及诊断探针。

以下是模型独立意见与本轮执行证据。模型一致不等于正确，没有计算无金标准的准确率，也没有通过多数票产生真值。

## 运行范围与状态

| 尝试状态 | 次数 |
|---|---|
| completed | 227 |
| failed | 28 |

仍未尝试的分配保留在分母中；完整 ID 见 results.json。

写作与执行请求配置：`openai-codex/gpt-6-luna:medium`。评委请求配置如下；实际宿主/模型返回标识、未知值及每次尝试见 JSON。

| 评委 ID | 请求配置 |
|---|---|
| deepseek | deepseek/deepseek-flash:high |
| gpt | openai-codex/gpt-6-sol:high |
| gemini_argon | agy/gemini-4-argon-high |
| gemini_flash | agy/gemini-3.8-flash-high |
| claude_opus | agy/claude-opus-5-5-high |
| claude_sonnet | agy/claude-sonnet-5-5-high |

## 分组语义统计

“有效”表示有效评审已返回；“完整”还要求事实、严重度和不确定项均已解决。语义判定失败可以同时是一次有效且完整的评审。FSP 表示评委判断的生成事实支持，RFR 表示评委判断的必需事实保留，均为场景宏平均；范围体现未决项，括号为已测/分配场景。关键错误范围使用全部分配产物作分母。

### 流程校准材料


| 组 | 评委 | 有效 | 完整 | FSP 范围（场景） | RFR 范围（场景） | 关键错误范围 | 语义状态 | 涉及错误类型的产物数 |
|---|---|---|---|---|---|---|---|---|
| calibration/calibration | claude_opus | 12/12 | 11/12 | 61.1%–61.1% (6/6) | 58.3%–58.3% (6/6) | 33.3%–41.7% | failed:6, passed:6 | actor_object:1, causality:1, condition:4, execution:2, modality:2, negation:3, permission:2, quantity_unit:1, required_omission:2, scope:1, unsupported_addition:1 |
| calibration/calibration | claude_sonnet | 12/12 | 11/12 | 61.1%–61.1% (6/6) | 50.0%–50.0% (6/6) | 41.7%–50.0% | failed:8, passed:4 | actor_object:1, causality:1, condition:4, execution:1, modality:4, negation:4, other:1, permission:2, quantity_unit:1, required_omission:3, scope:4, unsupported_addition:1 |
| calibration/calibration | deepseek | 12/12 | 11/12 | 61.1%–61.1% (6/6) | 58.3%–58.3% (6/6) | 33.3%–41.7% | failed:7, passed:5 | causality:1, condition:5, execution:1, modality:2, negation:2, permission:2, quantity_unit:1, required_omission:2, scope:2, unsupported_addition:3 |
| calibration/calibration | gemini_argon | 12/12 | 12/12 | 62.5%–62.5% (6/6) | 58.3%–58.3% (6/6) | 33.3%–33.3% | failed:6, passed:6 | causality:1, condition:4, execution:1, modality:3, negation:2, permission:2, quantity_unit:1, required_omission:2, scope:1, unsupported_addition:1 |
| calibration/calibration | gemini_flash | 12/12 | 12/12 | 61.1%–61.1% (6/6) | 54.2%–54.2% (6/6) | 41.7%–41.7% | failed:7, passed:5 | causality:1, condition:5, execution:2, modality:3, negation:1, permission:2, quantity_unit:1, required_omission:1, scope:1, unsupported_addition:1 |
| calibration/calibration | gpt | 12/12 | 12/12 | 58.3%–58.3% (6/6) | 58.3%–58.3% (6/6) | 41.7%–41.7% | failed:7, passed:5 | causality:1, condition:4, execution:1, modality:2, negation:1, permission:2, quantity_unit:1, required_omission:1, scope:2, unsupported_addition:1 |

### Pilot 候选


| 组 | 评委 | 有效 | 完整 | FSP 范围（场景） | RFR 范围（场景） | 关键错误范围 | 语义状态 | 涉及错误类型的产物数 |
|---|---|---|---|---|---|---|---|---|
| controlled/B | claude_opus | 1/4 | 1/4 | 100.0%–100.0% (1/4) | 100.0%–100.0% (1/4) | 0.0%–75.0% | not_evaluated:3, passed:1 | 无已判错误类型 |
| controlled/B | claude_sonnet | 0/4 | 0/4 | 未知–未知 (0/4) | 未知–未知 (0/4) | 0.0%–100.0% | not_evaluated:4 | 无已判错误类型 |
| controlled/B | deepseek | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/B | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/B | gemini_flash | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/B | gpt | 4/4 | 4/4 | 97.7%–97.7% (4/4) | 95.8%–95.8% (4/4) | 25.0%–25.0% | failed:1, passed:3 | condition:1 |
| controlled/C | claude_opus | 1/4 | 1/4 | 100.0%–100.0% (1/4) | 100.0%–100.0% (1/4) | 0.0%–75.0% | not_evaluated:3, passed:1 | 无已判错误类型 |
| controlled/C | claude_sonnet | 1/4 | 0/4 | 90.0%–90.0% (1/4) | 100.0%–100.0% (1/4) | 0.0%–100.0% | failed:1, not_evaluated:3 | unsupported_addition:1 |
| controlled/C | deepseek | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/C | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/C | gemini_flash | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| controlled/C | gpt | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/C+ | claude_opus | 2/4 | 2/4 | 100.0%–100.0% (2/4) | 100.0%–100.0% (2/4) | 0.0%–50.0% | not_evaluated:2, passed:2 | 无已判错误类型 |
| feedback_ablation/C+ | claude_sonnet | 1/4 | 1/4 | 100.0%–100.0% (1/4) | 100.0%–100.0% (1/4) | 0.0%–75.0% | not_evaluated:3, passed:1 | 无已判错误类型 |
| feedback_ablation/C+ | deepseek | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/C+ | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/C+ | gemini_flash | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/C+ | gpt | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/D | claude_opus | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |
| feedback_ablation/D | claude_sonnet | 1/4 | 1/4 | 100.0%–100.0% (1/4) | 100.0%–100.0% (1/4) | 0.0%–75.0% | not_evaluated:3, passed:1 | 无已判错误类型 |
| feedback_ablation/D | deepseek | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |
| feedback_ablation/D | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/D | gemini_flash | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| feedback_ablation/D | gpt | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/A | claude_opus | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |
| product_native/A | claude_sonnet | 1/4 | 0/4 | 88.9%–88.9% (1/4) | 100.0%–100.0% (1/4) | 0.0%–100.0% | failed:1, not_evaluated:3 | causality:1, unsupported_addition:1 |
| product_native/A | deepseek | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |
| product_native/A | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/A | gemini_flash | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |
| product_native/A | gpt | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/D | claude_opus | 2/4 | 2/4 | 100.0%–100.0% (2/4) | 100.0%–100.0% (2/4) | 0.0%–50.0% | not_evaluated:2, passed:2 | 无已判错误类型 |
| product_native/D | claude_sonnet | 0/4 | 0/4 | 未知–未知 (0/4) | 未知–未知 (0/4) | 0.0%–100.0% | not_evaluated:4 | 无已判错误类型 |
| product_native/D | deepseek | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/D | gemini_argon | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/D | gemini_flash | 4/4 | 4/4 | 100.0%–100.0% (4/4) | 100.0%–100.0% (4/4) | 0.0%–0.0% | passed:4 | 无已判错误类型 |
| product_native/D | gpt | 3/4 | 3/4 | 100.0%–100.0% (3/4) | 100.0%–100.0% (3/4) | 0.0%–25.0% | not_evaluated:1, passed:3 | 无已判错误类型 |

## 固定事实分歧

仅比较同一候选的相同必需事实 ID。观察分歧的分母是双方已确定事实；覆盖分母是全部分配事实。`unassessable`、`unreviewed`、`no_review` 均不算已确定；`missing` 是模型判断内容缺失，不能与缺评混同。完整状态矩阵、逐事实状态及场景宏平均保存在 JSON。

| 批次 | 组 | 模型对 | 已确定事实分歧 | 可比较覆盖 | 全分母分歧范围 |
|---|---|---|---|---|---|
| 校准材料 | calibration/calibration | deepseek / gpt | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | deepseek / gemini_argon | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | deepseek / gemini_flash | 1/20（5.0%） | 20/20（100.0%） | 5.0%–5.0% |
| 校准材料 | calibration/calibration | deepseek / claude_opus | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | deepseek / claude_sonnet | 2/20（10.0%） | 20/20（100.0%） | 10.0%–10.0% |
| 校准材料 | calibration/calibration | gpt / gemini_argon | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | gpt / gemini_flash | 1/20（5.0%） | 20/20（100.0%） | 5.0%–5.0% |
| 校准材料 | calibration/calibration | gpt / claude_opus | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | gpt / claude_sonnet | 2/20（10.0%） | 20/20（100.0%） | 10.0%–10.0% |
| 校准材料 | calibration/calibration | gemini_argon / gemini_flash | 1/20（5.0%） | 20/20（100.0%） | 5.0%–5.0% |
| 校准材料 | calibration/calibration | gemini_argon / claude_opus | 0/20（0.0%） | 20/20（100.0%） | 0.0%–0.0% |
| 校准材料 | calibration/calibration | gemini_argon / claude_sonnet | 2/20（10.0%） | 20/20（100.0%） | 10.0%–10.0% |
| 校准材料 | calibration/calibration | gemini_flash / claude_opus | 1/20（5.0%） | 20/20（100.0%） | 5.0%–5.0% |
| 校准材料 | calibration/calibration | gemini_flash / claude_sonnet | 1/20（5.0%） | 20/20（100.0%） | 5.0%–5.0% |
| 校准材料 | calibration/calibration | claude_opus / claude_sonnet | 2/20（10.0%） | 20/20（100.0%） | 10.0%–10.0% |
| Pilot | controlled/B | deepseek / gpt | 1/22（4.5%） | 22/22（100.0%） | 4.5%–4.5% |
| Pilot | controlled/B | deepseek / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/B | deepseek / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/B | deepseek / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/B | deepseek / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | controlled/B | gpt / gemini_argon | 1/22（4.5%） | 22/22（100.0%） | 4.5%–4.5% |
| Pilot | controlled/B | gpt / gemini_flash | 1/22（4.5%） | 22/22（100.0%） | 4.5%–4.5% |
| Pilot | controlled/B | gpt / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/B | gpt / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | controlled/B | gemini_argon / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/B | gemini_argon / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/B | gemini_argon / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | controlled/B | gemini_flash / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/B | gemini_flash / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | controlled/B | claude_opus / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | controlled/C | deepseek / gpt | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | deepseek / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | deepseek / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | deepseek / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | deepseek / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gpt / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | gpt / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | gpt / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gpt / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gemini_argon / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | controlled/C | gemini_argon / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gemini_argon / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gemini_flash / claude_opus | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | gemini_flash / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | controlled/C | claude_opus / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/C+ | deepseek / gpt | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | deepseek / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | deepseek / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | deepseek / claude_opus | 0/10（0.0%） | 10/22（45.5%） | 0.0%–54.5% |
| Pilot | feedback_ablation/C+ | deepseek / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/C+ | gpt / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | gpt / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | gpt / claude_opus | 0/10（0.0%） | 10/22（45.5%） | 0.0%–54.5% |
| Pilot | feedback_ablation/C+ | gpt / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/C+ | gemini_argon / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/C+ | gemini_argon / claude_opus | 0/10（0.0%） | 10/22（45.5%） | 0.0%–54.5% |
| Pilot | feedback_ablation/C+ | gemini_argon / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/C+ | gemini_flash / claude_opus | 0/10（0.0%） | 10/22（45.5%） | 0.0%–54.5% |
| Pilot | feedback_ablation/C+ | gemini_flash / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/C+ | claude_opus / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/D | deepseek / gpt | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | deepseek / gemini_argon | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | deepseek / gemini_flash | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | deepseek / claude_opus | 0/10（0.0%） | 10/22（45.5%） | 0.0%–54.5% |
| Pilot | feedback_ablation/D | deepseek / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/D | gpt / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/D | gpt / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/D | gpt / claude_opus | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | gpt / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/D | gemini_argon / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | feedback_ablation/D | gemini_argon / claude_opus | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | gemini_argon / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/D | gemini_flash / claude_opus | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | feedback_ablation/D | gemini_flash / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | feedback_ablation/D | claude_opus / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/A | deepseek / gpt | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/A | deepseek / gemini_argon | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/A | deepseek / gemini_flash | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/A | deepseek / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/A | deepseek / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/A | gpt / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | product_native/A | gpt / gemini_flash | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/A | gpt / claude_opus | 0/17（0.0%） | 17/22（77.3%） | 0.0%–22.7% |
| Pilot | product_native/A | gpt / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/A | gemini_argon / gemini_flash | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/A | gemini_argon / claude_opus | 0/17（0.0%） | 17/22（77.3%） | 0.0%–22.7% |
| Pilot | product_native/A | gemini_argon / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/A | gemini_flash / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/A | gemini_flash / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/A | claude_opus / claude_sonnet | 0/5（0.0%） | 5/22（22.7%） | 0.0%–77.3% |
| Pilot | product_native/D | deepseek / gpt | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/D | deepseek / gemini_argon | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | product_native/D | deepseek / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | product_native/D | deepseek / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/D | deepseek / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | product_native/D | gpt / gemini_argon | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/D | gpt / gemini_flash | 0/16（0.0%） | 16/22（72.7%） | 0.0%–27.3% |
| Pilot | product_native/D | gpt / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/D | gpt / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | product_native/D | gemini_argon / gemini_flash | 0/22（0.0%） | 22/22（100.0%） | 0.0%–0.0% |
| Pilot | product_native/D | gemini_argon / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/D | gemini_argon / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | product_native/D | gemini_flash / claude_opus | 0/11（0.0%） | 11/22（50.0%） | 0.0%–50.0% |
| Pilot | product_native/D | gemini_flash / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |
| Pilot | product_native/D | claude_opus / claude_sonnet | 0/0（未知） | 0/22（0.0%） | 0.0%–100.0% |

## 独立执行

每个组只计算可执行任务的原始分配尝试；后续重试不替换首次失败。失败、超时及中断记为失败，未运行保留未知。

| 组 | 原始分配 | 尝试含重试 | 成功 | 未知 | 成功范围 | 约束违反范围 |
|---|---|---|---|---|---|---|
| controlled/B | 2 | 2 | 2 | 0 | 100.0%–100.0% | 0.0%–0.0% |
| controlled/C | 2 | 2 | 2 | 0 | 100.0%–100.0% | 0.0%–0.0% |
| product_native/A | 2 | 2 | 2 | 0 | 100.0%–100.0% | 0.0%–0.0% |
| product_native/D | 2 | 2 | 2 | 0 | 100.0%–100.0% | 0.0%–0.0% |

## 原生触发

触发意图为冻结合成设计标签；完整日志没有调用才记未触发，采集不足记未知。强制规则加载不计入自然触发成功。

| 计数 | 数量 |
|---|---|
| fn | 0 |
| fp | 0 |
| tn | 4 |
| tp | 4 |
| unknown_negative | 0 |
| unknown_positive | 0 |
| unlabeled | 0 |


| 指标 | 数值及分母 |
|---|---|
| 观测覆盖 | 8/8（100.0%） |
| TPR（已观测） | 4/4（100.0%） |
| FPR（已观测） | 0/4（0.0%） |
| 当前测试混合 precision | 4/4（100.0%） |
| 触发后的路由正确 | 4/4（100.0%） |
| 端到端路由下界 | 4/4（100.0%） |
| 端到端路由上界 | 4/4（100.0%） |

下表仅在类别条件率可迁移的假设下计算 PPV；基率是假设，不是测得的真实使用分布。

| 假设基率 | PPV | 未知敏感性范围 |
|---|---|---|
| 1.0% | 100.0% | 100.0%–100.0% |
| 5.0% | 100.0% | 100.0%–100.0% |
| 10.0% | 100.0% | 100.0%–100.0% |
| 50.0% | 100.0% | 100.0%–100.0% |

## 用量与费用

实际支出保留所有尝试。总量中任何记录未知则总量为未知，已观测和及覆盖另列；不能把已观测部分当总费用。Pi 美元为目录估算，agy 不提供可核验美元值，其输入总量与内部模型请求数也保持未知。CLI 次数不等于模型请求数。

| 账本 | 指标 | 总量 | 已观测和 | 已知记录/全部记录 |
|---|---|---|---|---|
| downstream_executor | estimated_cost_usd | 0.00297138 | 0.00297138 | 8/8 |
| downstream_executor | input_cache_write | 0 | 0 | 8/8 |
| downstream_executor | input_cached | 15488 | 15488 | 8/8 |
| downstream_executor | input_total | 36558 | 36558 | 8/8 |
| downstream_executor | model_calls | 28 | 28 | 8/8 |
| downstream_executor | output_reasoning | 279 | 279 | 8/8 |
| downstream_executor | output_total | 1419 | 1419 | 8/8 |
| evaluation_only | estimated_cost_usd | 未知 | 1.5039 | 87/222 |
| evaluation_only | input_cache_write | 未知 | 0 | 87/222 |
| evaluation_only | input_cached | 未知 | 166698 | 217/222 |
| evaluation_only | input_total | 未知 | 342275 | 87/222 |
| evaluation_only | model_calls | 未知 | 109 | 87/222 |
| evaluation_only | output_reasoning | 未知 | 810817 | 217/222 |
| evaluation_only | output_total | 未知 | 1200808 | 217/222 |
| production_writer | estimated_cost_usd | 0.0131079 | 0.0131079 | 25/25 |
| production_writer | input_cache_write | 0 | 0 | 25/25 |
| production_writer | input_cached | 62720 | 62720 | 25/25 |
| production_writer | input_total | 141317 | 141317 | 25/25 |
| production_writer | model_calls | 65 | 65 | 25/25 |
| production_writer | output_reasoning | 234 | 234 | 25/25 |
| production_writer | output_total | 9242 | 9242 | 25/25 |

各组全任务/可执行任务的用量与单位成功成本见 JSON 的 `costs_by_workflow`。反馈消融的修订费用和含一次 C 初稿的可比工作流费用分列于 `shared_workflows`；可比费用不能再次累加到实际支出。

## 证据与限制

[完整结构化结果](results.json) SHA-256：`15c8c5d31ead3a60e6da945c7e7cf868415199433d7f6923a00a6706a98dcdfa`。

原始 summary SHA-256：`c4d8399fd2855f2b124335b03a30f25102f9877f5ed477d9c3b734b727319d9a`。导出登记 2801 个证据文件的原始字节 SHA-256；保留 run、receipt、事件、侧车、产物、冻结输入和数据库文件哈希。本机绝对路径已转换为仓库相对路径或删除。原始提示、日志和数据库留在被忽略的 runs 中。

- 四个合成场景的探索性描述；正式风险界值与样本量仍未设定。
- 有效评审返回、判断完整性和模型判定的语义通过是三件事；模型意见不是准确率或人工验收。
- 固定事实分歧只对齐同一产物及预先声明的事实 ID；不对齐自由声明，不生成多数票真值。
- FSP 取决于各评委自行提取的声明集合；各模型的数值不构成共同金标准上的准确率。
- 语义使用最新尝试的有效评审；执行和触发保留原始分配尝试；失败与重试均计入成本。
- 语义宏平均先在场景内平均，再对已测场景等权平均；缺失覆盖单列。
- 未决上下界是缺失敏感性范围，不是统计置信区间。
- 触发意图标签来自冻结合成设计；PPV 的基率是假设，不能当真实部署 precision。
- CLI 调用次数不等于内部模型请求数；agy 输入总量、模型请求数及美元成本保持未知。
- Pi 美元值为目录估算，不是已核验账单；未知费用不补零，共用初稿可比成本不可再次累加。
- 哈希对应保存在本机的原始证据；去路径导出不等于可独立复现的原始数据发布。
- 独立人工评审、读者试验及科学验收均未运行。

导出一致性检查 **Passed** 只表示上述证据与当前汇总相符，不代表模型语义判断通过、真实读者理解提高或独立科学验收通过。
