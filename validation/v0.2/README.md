# v0.2 工程交付与实测证据

2026-10-24。当前实现已交付；人工校准、产品试跑和证据驱动的规则压缩尚未完成。本目录不替代原始包的历史验证记录。

| 项目 | 状态与证据 |
|---|---|
| 最终集成测试 | **Passed：237；Skipped：5**。五项均因 Windows 无符号链接创建权限；真实 junction 与进程清理检查通过。 |
| 数据与 Skill 结构 | **Passed**：4 场景、12 校准材料、版本化 schema 与系统 Skill validator。 |
| Pi 真实冒烟 | **Passed**：三个模型；写作者实际读取 Skill、保存产物并运行检查器。显式冒烟不证明隐式触发率。 |
| AI 校准响应 | 首次 **23/24** 通过严格格式和引文检查；1 份 **Failed** 已保留，重试有效。目前有 24 份有效侧车，不代表人工语义认可。 |
| 调用预算 | 已用 **28/128** 次，累计 **611.10/14400 秒**。失败与重试都包含在内。 |
| 原始日志回放 | **Passed**：最终适配器回放全部 28 份 JSONL，所有核心 usage 字段与记录一致。 |
| 实际浏览器 | **Passed**：隔离合成批次的保存、刷新恢复、初判提交、冻结、AI 揭示、裁决及历史。 |
| 导出 | [HTTP 导出](export-via-http.json) **Passed**；浏览器下载事件捕获 **Not Run／未确认**，工具等待超时。 |
| 真实人工校准 | **Not Run**：留给用户独立初判与裁决，没有代填。 |
| 产品试跑／规则压缩 | **Not Run**：分别等待人工校准和效果证据。 |
| 正式读者实验／Codex、Claude 原生实测 | **Not Run**：不在本轮试跑范围。 |

当前服务入口：<http://127.0.0.1:8765>。停止、恢复、预算和评审操作见 [eval/README.md](../../eval/README.md)。实际数据与实时进度在 `runs/pilot-20261024/`；原始模型日志和用户评审数据库均被 Git 忽略。

[engineering.json](engineering.json) 记录环境、原始日志哈希和调用用量；[browser.json](browser.json) 标识浏览器证据为自动化合成验收，不是用户人工接受。开发早期 receipt 中的 `adapter_hash` 是调用时磁盘文件哈希，不保证长进程已加载同一版代码；已通过最终版本日志回放核实用量，后续调用另记 `loaded_adapter_hash`。

[token-estimates.json](token-estimates.json) 使用已固定 SHA-256 的 `o200k_base`：完整生成规则 736 Token，按场景路由的规则 205–241 Token。这只是规则文本的离线长度估算，不是模型账单、完整上下文或总体成本改善。

以下截图来自隔离的合成批次：

- [独立初判](01-blind-initial.jpg)
- [最终裁决](02-final-submitted.jpg)
- [保留的修订历史](03-history.jpg)

`source-manifest.json` 标识本次交付的文件内容与子模块提交。原始 `MANIFEST.sha256.json` 仍描述初始化包，未覆盖改写。
