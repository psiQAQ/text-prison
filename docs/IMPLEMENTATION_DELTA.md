# v0.2 实现状态与后续边界

日期：2026-10-24。运行记录和本地评测工具已迁移到 v0.2。原始文档补丁的历史说明在 [DOCS_PATCH.md](../DOCS_PATCH.md)，不作为当前实现状态。

| 范围 | 当前实现 | 验收入口 |
|---|---|---|
| Skill 与机械检查 | 六类 profile、中英文路由；规则元数据；JSON 溢出、TeX 保护修复 | `tests/test_checker.py`、`tests/test_skill_metadata.py` |
| 安装器 | Codex、Claude、Pi 项目级复制；拒绝覆盖和链接父目录 | `tests/test_install_skill.py` |
| 版本契约 | v0.2 run/task/AI/human schema；v0.1 兼容读取 | `eval/contracts.py`、`tests/test_eval_contracts.py` |
| Pi 采集 | JSONL、真实终态、usage 去重、持久预算、限定读写 | `eval/pi_adapter.py`、`eval/tool_boundary.mjs` |
| 任务与校准 | 4 个合成场景、12 条材料、私有独立 verifier | `eval/tasks/`、`eval/calibration/` |
| 实验编排 | 原生 A/D、受控 B/C、共享 C 初稿反馈消融、独立执行与触发 | `eval/runner.py` |
| 人工工作台 | 初判保存/冻结、AI 揭盲、裁决、历史与导出 | `eval/review_store.py`、`eval/web/` |
| 汇总 | 场景等权、缺失范围、首次执行、触发基率、成本分账 | `eval/analysis.py`、`eval/reporting.py` |
| 来源 | 旧来源 ID 与 R01–R32；五个固定提交子模块 | `sources.json`、[RELATED_WORK](RELATED_WORK.md) |

实际执行与未完成项以 [当前验证记录](../validation/v0.2/README.md) 和 `runs/<实验>/SUMMARY.md` 为准。代码存在、离线测试通过、模型调用成功、人工验收完成是不同状态。

## 保留的语义边界

机械检查器始终返回 `semantic_status=not_evaluated`。AI 评审是独立侧车，不把数值字面匹配解释为事实正确。自由提取声明未经对齐不计算声明一致率；评委校准主要对照冻结的人工初判，参考 AI 后的裁决独立保存。

失败和重试留存，未知不补零，未运行分配仍进入对应分母。原生 D 未触发不能删掉。反馈消融共享同一份 C 初稿，实际支出只记一次初稿；可比工作流分别包含初稿成本，两种口径不相加。

## 本轮仍不覆盖

正式风险界值、功效设计、读者实验、Codex/Claude 原生采集、长期缓存和全模型交叉保持待做。四场景不用于宣称正式收益。没有人工校准就不进入产品试跑；规则压缩等待已确认问题和实测证据，不根据 AI 单方意见删除保护条款。

没有新增 MCP、全局 hooks 或生产常驻组件。人工网页服务由用户显式启动，仅监听 loopback。第三方子模块只作研究参考，不自动安装、运行 hooks 或进入 Skill 包。

根 `MANIFEST.sha256.json` 和原始 ZIP 保持基线含义。新清单与证据独立版本化，不能用旧哈希声称当前文件已验证。
