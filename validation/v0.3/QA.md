# AI-only 浏览器只读验收

- DOM 检查时间：2026-10-25 00:40:51（Asia/Shanghai）；原始 UTC 时间见 `dom-checks.json`。
- 地址：`http://127.0.0.1:8765/`；批次 `ai-six-20261025-calibration`。
- 环境：真实 Edge 浏览器，通过 CUA 操作。截图为浏览器实际 JPEG；文件和界面源码 SHA-256 见 `manifest.json`。
- 范围：刷新当前批次、查看候选 01 与 12、展开原始 JSON、滚动。没有创建或改写评审，没有调用模型，没有点击导出下载或停止服务。

| 检查 | 结果 | 实际证据 |
|---|---|---|
| AI-only 直接显示 | Passed | 标题为 AI 评审证据工作台；标识 AI-only、无人工评审阶段；刷新成功 |
| 批次进度 | Passed | 12 个候选，24/72 份记录已完成，48 份未运行 |
| 六模型独立状态 | Passed | deepseek、gpt 已完成；gemini_argon、gemini_flash、claude_opus、claude_sonnet 未运行；两份候选均显示六模型 |
| 人工入口隐藏 | Passed | 页面没有人工表单；冻结按钮不可见；独立初判与最终裁决提交按钮数量均为 0 |
| 原始记录展开 | Passed | 已完成模型可展开完整评审 JSON；未运行模型 JSON 明确 `status: not_run`、`review: null` |
| 只读候选切换 | Passed | 候选 01 与 12 内容可切换，模式与六模型状态保留 |
| 浏览器错误 | Passed | 检查时浏览器捕获的 error 级日志为空 |
| 下载、人工写入、停止服务 | Not Run | 本次明确不执行这些操作 |
| 模型判断的语义正确性 | Not Run | 本次只验收界面，不替代独立语义或科学评价 |

截图：

- `01-ai-only-overview.jpg`：顶部模式、批次进度和已完成模型。
- `02-completed-raw-json.jpg`：已完成模型的原始记录展开。
- `03-not-run-models.jpg`：未运行模型状态及 `review: null` 原始记录。
- `04-last-candidate-no-human-form.jpg`：候选 12 页面底部，无人工表单。

本次未发现阻塞上述行为的界面问题，未修改应用源码。模型调用由主 agent 并行管理；以上进度是验收时的可见快照，后续可随新结果导入而变化。
