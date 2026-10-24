# 从 v0.1 原型到有证据方案：后续实现差量

日期：2026-10-24。本文件是开发清单，**本次文档补丁没有执行表内代码修改**。先补测量与保护，再扩大写作规则。除明确依赖的事项外，不需要重建原型。

## 1. 保留与禁止误改

保留六类 profile、共用 Skill 源、项目级安装、离线 Markdown/JSON 检查、精确契约与语义状态分离。保留现有反例以及 `not_evaluated` 行为。不得因为新文档描述了语义审查就将检查器的 semantic_status 改为 passed。

本轮不新增全局 hooks、MCP、常驻服务，不替换模型权限，不安装第三方 Skill，不复制官方完整词典。不把评测全文或所有参考文献塞进 SKILL.md。

## 2. 按实际路径拆分工作

| 优先级 | 文件/目录 | 后续修改 | 验收证据 |
|---|---|---|---|
| P0 | `skills/text-prison/assets/rules.json` | 增补来源类型、作用域、例外、hard/advisory、覆盖声明；旧字段做迁移 | 每条规则有阳性、阴性、边界与未覆盖声明 |
| P0 | `sources.json` | 将 RELATED_WORK 的新来源映射为机器可读记录，记录版本/哈希与核验范围 | 不把未取得的 STE/ISO 正文标为已核验；动态基线固定 commit |
| P0 | `tests/test_checker.py` 与计划新增的 `tests/fixtures/` | 增加否定、模态、单位、条件、引用、代码/公式保护的测试；区分机械与语义 | 机械检查不误宣称检出所有语义变异；明确已知盲区 |
| P0 | `eval/run.schema.json` | 设计新版本与兼容读取；新增实验区块、日志和侧车引用 | 旧 v0.1 记录可读；不改写历史原始数据 |
| P0 | 计划新增 `eval/adapters/`、日志 fixtures | Codex/Claude 原生事件、请求级 usage、子 Agent/累计去重 | 显式阳性和阴性被正确采集；缺失返回 unknown/null |
| P1 | 计划新增 `eval/tasks/` 与 `eval/runner/` | 来源/事实/契约/验收任务包；隔离运行；A/B/C/D 与反馈消融 | 人工参考解通过，独立坏例失败，所有组环境一致 |
| P1 | `eval/prompts/semantic-review.md` 的调用适配 | 生成编辑级审查侧车并做人工校准 | FSP、RFR、critical 与 coverage 来自可追溯记录 |
| P1 | 计划新增 `eval/analysis/` | 场景宏平均、成对区间、读者交叉因素、成本与缺失敏感性 | 已知模拟数据回归；零事件不输出零宽风险区间 |
| P2 | `skills/text-prison/SKILL.md` 与 `references/` | 根据已验证规则压缩运行时提示；保持科研模态、局部路由和一次修订上限 | 关键保护不因 Token 预算删除；无关任务不退化 |
| P2 | `skills/text-prison/scripts/check.py` 的可选后端 | 先做规则对应表，再接 Vale；机器契约与语义分开 | 固定 Vale/规则版本，双后端重复问题去重，误报有数据 |

P0/P1/P2 是依赖顺序，不是未来完成时间承诺。没有样本、宿主日志和真实调用记录时，不生成“示例排行榜”冒充实验结果。

## 3. schema 迁移需要特别注意

当前 `eval/run.schema.json` 固定 `schema_version=0.1`，arm 只有 A/B/C/D/C+；`usage` 禁止额外属性。新协议不能直接给这些枚举塞入新的外部基线名称，或向 usage 任意追加字段而仍称符合旧 schema。

下一版至少需要表达以下信息，字段名称在实现时冻结：

| 语义 | 目的 |
|---|---|
| experiment_id、track、condition_variant | 区分真实 D 与“强制一次修订”的反馈消融 |
| assignment_id、attempt_id、retry_of、exclusion_reason | 所有失败/重跑留证，防止择优轨迹 |
| source/required-fact/verifier/prompt manifest | 冻结独立验收与可见信息 |
| semantic_review_ref、human_review_ref | 引用逐项证据，避免只保存一个分数 |
| provider/schema、request ID、aggregation flags | usage 去重和覆盖判断 |
| cost_scope、shared_draft_ref | 写作/执行/评测分账及共用初稿核算 |
| trigger_evidence、observation_coverage、expected_route | 区分 unknown、不触发与错误路由 |
| reader assignment / anonymized reader ID | 处理读者差异，避免同场景重复学习 |

开发阶段可以用独立 JSON 侧车保存新字段，并在旧记录顶层添加引用（旧 schema 顶层允许扩展），但必须说明侧车尚无稳定 schema；不能把新字段塞进旧 usage。正式实验前完成新 schema 与校验器，不依靠口头约定。

## 4. 不需要实现的“大而全”功能

首轮不需要训练自己的 LENS 模型，不需要把所有研究指标都做成线上门禁，不需要引入整套 SkillsBench 任务库存，也不需要对所有宿主/模型全交叉。优先完成一个可复核的主比较和必要的反馈消融。

外部 SimpleEnglish 对照先限于英语共享场景、固定 skill-only 配置；其全面模态限制不是本项目规则。公开的短而聚焦 Skills 相关性也不等于“最多三个模块”已被证明是通用最佳值。

## 5. 本次文档补丁的兼容性

安装命令与运行依赖不变。`validation/` 内 35 项测试通过记录属于原始 v0.1，不是这次新功能的验收；本次没有重新运行产品测试，也没有新增产品实验。

原始 `MANIFEST.sha256.json` 描述的是初始化包。覆盖修改后的 Markdown 后，该旧清单对修改文件自然不再匹配；应保留其基线含义，并在正式发版时重新生成完整发布清单，而不是称补丁后仍符合原包哈希。本补丁另有变更文件哈希记录，见 [DOCS_PATCH.md](../DOCS_PATCH.md)。

`NOTICE.md` 和 `sources.json` 本轮未改。新研究链接的规范记录在 [RELATED_WORK.md](RELATED_WORK.md)，未来机器化时再同步，避免一个未核验的自动脚本现在改写运行时数据。
