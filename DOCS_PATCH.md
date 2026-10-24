# TextPrison 文档增量补丁 v0.2

日期：2026-10-24。**只包含 Markdown 文档，不包含新代码、依赖、Skill 配置或实验结果。**

适用基线：`text-prison-starter-v0.1.zip`。

```text
SHA256 acf42433ae3720a7f535775c87341048677fdb4fdf9622daf5f9ea89018d4b94
```

## 覆盖方式与范围

补丁 ZIP 内保留 `text-prison-starter/` 前缀。解压到原 `text-prison-starter` 目录的上一级，与原目录合并；仅覆盖下表标记“替换”的 Markdown。若项目已改名，则将补丁内该目录的内容合并到实际项目根目录。不要用补丁目录替换或删除整个旧项目。

若这些文件已经在本地编辑，请先按下文原始哈希检查差异并合并，不要盲目覆盖。没有修改运行时代码、依赖、安装器、SKILL.md、rules.json、sources.json、NOTICE.md 或任何验证记录。

## 文件清单

共 10 份 Markdown：5 份替换、5 份新增，其中本文件为新增。

| 路径 | 操作 | 内容 |
|---|---|---|
| [README.md](README.md) | 替换 | 更新文档导航与能力边界，保留原安装命令 |
| [docs/DESIGN.md](docs/DESIGN.md) | 替换 | 用内容、输出、测量三种契约组织规则；保留六类路由 |
| [docs/IMPLEMENTATION_DELTA.md](docs/IMPLEMENTATION_DELTA.md) | 新增 | 逐路径列出未来代码/配置工作与 schema 兼容性 |
| [docs/RELATED_WORK.md](docs/RELATED_WORK.md) | 新增 | 相关实现、作者自评局限与 30 组原始来源 |
| [eval/METRICS.md](eval/METRICS.md) | 新增 | 明确事实支持/保留、理解、执行、成本、触发与区间公式 |
| [eval/PREREGISTRATION.md](eval/PREREGISTRATION.md) | 新增 | 正式试验前冻结界值、样本、统计及排除政策 |
| [eval/PROTOCOL.md](eval/PROTOCOL.md) | 替换 | 加强独立验收、反馈消融、原生触发和失败留证 |
| [eval/README.md](eval/README.md) | 替换 | 更新评测资料入口和当前未实现范围 |
| [eval/prompts/semantic-review.md](eval/prompts/semantic-review.md) | 替换 | 改为逐事实/逐编辑证据，保留 uncertain 与人工复核 |
| `DOCS_PATCH.md` | 新增 | 基线、覆盖方式、变更说明与文件哈希 |

## 相比初始化方案，真正改变了什么

| 原方案不足 | 本次修订 |
|---|---|
| 指标有名字，但与原始研究的对应不够明确 | 建立“来源—可借鉴机制—本项目适配—外推边界”表 |
| 事实核对可能偏重已写出的内容 | 生成事实支持率与必需事实保留率同时测，定位条件/模态变化 |
| C–D 混入额外修订机会 | 归因检查反馈时强制增加同初稿、同修订机会的 C+ 消融 |
| 10%、30%、3 个百分点等可能被误读为公认标准 | 撤销默认验收地位；通过风险理由、功效/精度和预注册确定 |
| 平衡触发集可能夸大实际 precision | 增加部署基率、TPR/FPR、unknown 和观测覆盖 |
| 低 Token 可能只量文件大小 | 生产写作、下游执行、评测分账；失败和重试计入成本 |
| 相近项目的规则可能被直接导入 | 不导入全局 may/might 禁令；不把已有违规率提升外推成理解提升 |

优先阅读 [相关实现与文献](docs/RELATED_WORK.md)、[新指标](eval/METRICS.md) 和 [实验协议](eval/PROTOCOL.md)。需要安排开发时再读 [实现差量](docs/IMPLEMENTATION_DELTA.md)。这些研究参考不默认加载进生产 Skill。

## 尚未完成的工作

没有运行外部项目，没有复现其提升率，没有进行模型调用、真实读者研究、下游执行或 Token 测量。本次没有重新运行产品测试。初始化包中的 35 项通过记录仍仅属于旧检查器/安装器，不能证明本次规划的新能力。

本次完成的是文档差量、原始资料检索与设计修订。后续正式实验需要独立任务、宿主采集、usage fixtures、评委校准和冻结的预注册；其实现状态在各文档中明确标记。

`eval/run.schema.json` 仍为 0.1，不因文档称为 v0.2 就自动支持新字段。覆盖后原 `MANIFEST.sha256.json` 对修改文档不再匹配；它仍是初始化包的历史清单。本补丁不修改该 JSON。正式发版时另行生成新发布清单。

## 修改文件校验

以下 `before` 是初始化包文件哈希，`after` 是本补丁文件哈希。新增文件没有 before。本文件不列自身哈希，避免自引用。

```text
README.md
  before: d59ce770cdae14184bf89f12b32fad254f49da1e86e4296b41706fe02ff44445
  after:  64947c8cf0a7cc1cc6395b9fa60c7306804b713610f3acb61d9dae4b69e5c39d
docs/DESIGN.md
  before: 28519fa4373d8c26b7134b9ba31ca38070709582eef34d19789a4af1ba38c519
  after:  b26f332a5308fe1cbddac9676d6906cf7e6b8bc4ab74d9abdfbe4eff9d1312ce
docs/IMPLEMENTATION_DELTA.md
  before: NEW
  after:  e7655db61d086c00f9eb143cd5ad778e511b80f8f60d988cf3c1f9188d6c1136
docs/RELATED_WORK.md
  before: NEW
  after:  7b19b07176014c603f174d9ac498b84b3c65df5e13075c17d7589fa8d2c07893
eval/METRICS.md
  before: NEW
  after:  d8f5747be101284fee4278c2757fc7803a6640f47392bd9999b0bc0f6a319f55
eval/PREREGISTRATION.md
  before: NEW
  after:  7f23759390a60680a7d67c6595d6a78abf863aaa83272bdb6c8e24a751230312
eval/PROTOCOL.md
  before: 67b8212a40d8bdf954f14113d9d770cadb0a2f91ff47caaa3b82fd205c8984dc
  after:  7dd2a0cbed18de622a1e4c724529cd8fcaa869f41b48eaf6a63ddc0b50f43751
eval/README.md
  before: 737c6ab48afd3e31aa997a7aabd8d7a16107149702e46a4d5be219971b18fdd3
  after:  3d87746c77cb33188cacf3b536bab05ca97324b53d57bb95e757a8cef850e271
eval/prompts/semantic-review.md
  before: b2f5f76d2ae2d4413923af197ab0848a1da9a4045d5301735a5156e03b8710a3
  after:  7018df4f3b41454f7afc66336c43d62624a1a47a92f4301a845b281a392e4092
```
