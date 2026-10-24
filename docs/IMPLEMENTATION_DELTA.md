# v0.3 六评委流程与后续边界

日期：2026-10-25。新增 agy 四个系列的 High 评委与 AI-only 工作台，取消本轮人工门禁；运行记录仍兼容 v0.2。旧实验及人工记录保留。原始文档补丁的历史说明在 [DOCS_PATCH.md](../DOCS_PATCH.md)，不作为当前实现状态。

| 范围 | 当前实现 | 验收入口 |
|---|---|---|
| Skill 与机械检查 | 六类 profile、中英文路由；规则元数据；JSON 溢出、TeX 保护修复 | `tests/test_checker.py`、`tests/test_skill_metadata.py` |
| 安装器 | Codex、Claude、Pi 项目级复制；拒绝覆盖和链接父目录 | `tests/test_install_skill.py` |
| 版本契约 | v0.2 run/task/AI/human schema；v0.1 兼容读取 | `eval/contracts.py`、`tests/test_eval_contracts.py` |
| Pi 采集 | JSONL、真实终态、usage 去重、持久预算、限定读写 | `eval/pi_adapter.py`、`eval/tool_boundary.mjs` |
| agy 评委 | 四个 High 型号、独立无工具会话、原始终态与未知用量保留 | `eval/agy_adapter.py` |
| 任务与校准 | 4 个合成场景、12 条材料、私有独立 verifier | `eval/tasks/`、`eval/calibration/` |
| 实验编排 | 原生 A/D、受控 B/C、共享 C 初稿反馈消融、独立执行与触发 | `eval/runner.py` |
| 模型证据工作台 | 六评委即时展示与导出；历史人工模式继续兼容 | `eval/review_store.py`、`eval/web/` |
| 汇总 | 场景等权、缺失范围、首次执行、触发基率、成本分账 | `eval/analysis.py`、`eval/reporting.py` |
| 来源 | 旧来源 ID 与 R01–R32；五个固定提交子模块 | `sources.json`、[RELATED_WORK](RELATED_WORK.md) |

实际执行与未完成项以 `validation/v0.3/` 和 `runs/ai-six-20261025/SUMMARY.md` 为准。[v0.2 验证记录](../validation/v0.2/README.md)保持历史含义。代码存在、离线测试通过、模型调用成功、语义正确是不同状态。

## 保留的语义边界

机械检查器始终返回 `semantic_status=not_evaluated`。AI 评审是独立侧车，不把数值字面匹配解释为事实正确。自由提取声明未经对齐不计算声明一致率。当前没有人工金标准，报告每模型结果及固定事实 ID 分歧，不宣称准确率或人工验收。

失败和重试留存，未知不补零，未运行分配仍进入对应分母。原生 D 未触发不能删掉。反馈消融共享同一份 C 初稿，实际支出只记一次初稿；可比工作流分别包含初稿成本，两种口径不相加。

## 本轮仍不覆盖

正式风险界值、功效设计、读者实验、Codex/Claude Code 原生采集、长期缓存和全模型交叉保持待做。agy 的 Claude 模型不等于 Claude Code 宿主实测。四场景不用于宣称正式收益。当前试跑以模型冒烟及结构化评审就绪为门槛，不要求人工填写；规则压缩仍等待可核实的问题和实测证据，不根据模型投票删除保护条款。

没有新增 MCP、全局 hooks 或生产常驻组件。评审网页服务仅监听 loopback。第三方子模块只作研究参考，不自动安装、运行 hooks 或进入 Skill 包。

根 `MANIFEST.sha256.json` 和原始 ZIP 保持基线含义。新清单与证据独立版本化，不能用旧哈希声称当前文件已验证。
