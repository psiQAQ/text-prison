# TextPrison / 文字狱

按文档用途选择写作规则，保护技术含义。

## 当前可用范围

2026-10-25：仓库已退出 Agent 实战和评测用途，移除了评测代码、评审网页、测试、运行数据及原 Python 检查器。当前保留一份写作 Skill、按用途和语言拆分的参考规则，以及项目级安装器。

**当前 Skill 仅提供写作指导，不运行机械检查。**“统一 Skill + Vale + 按需规则库”的新工作流仍需用户批准审阅后的实施方案，尚未接入 Vale，也未实现新的优化选项交互。

## 使用当前 Skill

指令使用不需要安装 Python 依赖。项目安装器需要已有 Python，使用标准库；它不会安装依赖或修改目标项目的全局指令、权限、hooks。

在仓库根目录运行以下 PowerShell 命令，将目标路径替换为实际存在的项目目录：

```powershell
python tools/install_skill.py --agent codex --project D:/path/to/project
```

| 宿主 | `--agent` | 项目安装位置 | 显式调用 |
|---|---|---|---|
| Codex | `codex` | `.agents/skills/text-prison/` | `$text-prison` |
| Claude Code | `claude` | `.claude/skills/text-prison/` | `/text-prison` |
| Pi | `pi` | `.pi/skills/text-prison/` | `/skill:text-prison` |

`both` 仍表示同时安装 Codex 和 Claude Code。安装器拒绝覆盖已有目录，并生成 `install-manifest.json`。更新前检查已有副本及用户改动；不要直接删除未知文件。仓库只维护 `skills/text-prison` 这一份源文件。

相关文档请求仍可由宿主自动发现 Skill，是否触发取决于宿主。当前不提供自动触发、理解效果或成本改善的实测保证。

## 保留资料

- [当前设计范围](docs/DESIGN.md)：指令阶段的职责和限制。
- [来源目录](docs/RELATED_WORK.md)及 [机器来源索引](sources.json)：规范、参考实现和此前的来源核验范围。
- [归属说明](NOTICE.md)：第三方资料与许可边界。

五个上游子模块保持固定版本，仅作只读参考，不安装、不执行。原始 ZIP、根 `MANIFEST.sha256.json` 与 `DOCS_PATCH.md` 保留原包的历史含义，不代表当前功能或验证状态。

本仓库不再运行或维护 Agent 实战、模型评委、A/B 实验、测试套件或评审网页。原提交和归档标签保留在 Git 历史中；已删除的忽略目录原始数据没有另行备份。

## 使用边界

保留事实、条件、权限、数字、单位、引用和不确定性。规则借鉴不等于完整 ASD-STE100 认证，也不证明语义正确。代码、命令、标识符和原样引文按用户要求保护，不为文风统一擅自修改。

不做观点审查，不以规避 AI 文本检测为目标，不自动安装工具或修改全局指令。
