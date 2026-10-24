# 实验目录

`PROTOCOL.md` 是预注册草案；`run.schema.json` 定义记录结构；`prompts/semantic-review.md` 是独立语义审查模板。

本起步包没有生成 96 个正式基准任务，没有调用模型，没有招募读者，没有原生宿主 runner，也没有测得可读性、成功率或 Token 改善值。
后续先编写开发集与独立验收，再固定宿主适配器及 usage 解析测试。不要将 examples/ 中的合成反例当成正式 A/B 数据。
