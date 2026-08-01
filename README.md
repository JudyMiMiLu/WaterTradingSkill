# WaterTradingSkill ｜ 水战法投资技能集

面向 A 股投资者的 **AI Agent 技能集**（Hermes / WorkBuddy / 豆包 等），一套从"交易战法"到"量化打分"再到"行情数据自动化"的完整投资工作流。

> 版本：v2.0.2 ｜ 更新：2026-08-01 ｜ 仓库：[JudyMiMiLu/WaterTradingSkill](https://github.com/JudyMiMiLu/WaterTradingSkill) ｜ 协议：MIT

---

## 📦 包含技能

| 技能 | 版本 | 定位 | 回答什么 |
|------|------|------|----------|
| [investment-advisor](skills/investment-advisor/) | v2.0 | 投资方法论 | 五步框架：趋势-位置-打分-角色-仓位，调仓纪律 |
| [a-share-market-data](skills/a-share-market-data/) | v2.0 | 数据与自动化 | 新浪行情 API、飞书多维表格读写、每日自动更新 |

### 技能关系

```
investment-advisor（方法论层：WATER 打分 + 233 年线 + 角色仓位 + 调仓纪律）
    ↓ 落地执行
a-share-market-data（工具层：行情拉取 + 飞书表格 + cron 监控）
```

> **历史**：v1.x 曾含 water-zhanfa（水战法经验版）。v2.0 起 water-zhanfa 精华已并入 investment-advisor（龙头参考期、逐笔明细、节奏模板案例），不再单独维护。

---

## 🌿 分支结构与两种形式

本项目 **只维护一份 README**（本文件）。所有方法升级、bug 修复都在 **main** 提交；`adapt-other-agents` 分支**只做个性化适配**，不单独维护文档。

| | `main`（默认分支） | `adapt-other-agents`（适配分支） |
|---|---|---|
| 定位 | **Hermes Agent 原生版** | **通用 Agent 适配版**（WorkBuddy / 豆包 / Kimi 等） |
| 维护策略 | ✅ 主维护分支：方法升级、修复都在这里 | ⚙️ 只改格式外壳（个性化适配），内核随 main 同步（`git merge main`） |
| 适用用户 | Hermes Agent 用户 | 使用其他 AI Agent 的用户 |

### 两种形式差异对照

| 差异点 | Hermes 原生版（`main`） | 通用适配版（`adapt-other-agents`） |
|---|---|---|
| SKILL.md frontmatter | 含 Hermes 特有字段（`agent_created: true`） | 移除该字段（其他 Agent 可能不识别） |
| 技能安装路径 | `~/.hermes/skills/` | `<skill_dir>`（Agent 自定义技能目录） |
| 定时任务 | `hermes cron create` | 通用方案（Linux crontab / macOS launchd / Windows 任务计划），Hermes 命令降级为可选 |
| Agent 自带工具表述 | "Hermes 自带 stocks skill" | "Agent 自带 stocks skill（如 Hermes）" |

**方法内核两分支完全一致**：WATER 打分、233 年线、五步框架、角色仓位、新浪行情 API 等投资逻辑零差异，只改格式外壳。

### 我该用哪个？

- 用 **Hermes Agent** → 直接使用默认分支（main），无需切换
- 用 **WorkBuddy / 豆包 / Kimi / 其他 Agent** → clone 后 `git checkout adapt-other-agents`

---

## 🚀 快速开始

### 前置条件

- AI Agent 客户端（支持技能/提示词注入即可）
- [lark-cli](https://open.feishu.cn)（如需飞书多维表格）：`npm install -g @larksuite/cli` + `npx -y skills add https://open.feishu.cn --skill -y`
- Python 3.10+（运行数据脚本）

### 安装技能

```bash
# Hermes 用户（默认分支）：
git clone git@github.com:JudyMiMiLu/WaterTradingSkill.git
cp -r WaterTradingSkill/skills/* ~/.hermes/skills/

# 其他 Agent 用户：
git clone git@github.com:JudyMiMiLu/WaterTradingSkill.git
cd WaterTradingSkill && git checkout adapt-other-agents
# 然后把 skills/ 下的目录复制到你的 Agent 技能目录
```

重启 Agent 会话后，向 agent 说：
- "分析我的持仓组合" / "XX 能不能买" → investment-advisor
- "更新持仓行情" → a-share-market-data

---

## 📖 各技能使用说明

### 1. investment-advisor（投资方法论）

五步框架：`先看趋势 → 再看位置 → 买点评分 → 决定底仓 → 配组合控风险`。

- 提供持仓 CSV（模板：`skills/investment-advisor/references/holdings_template.csv`）或直接对话说明
- 产出：组合体检 / 标的买点卖点准入 / 调仓纪律核对 / 逐笔买卖明细 / 复盘
- 核心规则：WATER 打分 + 233 年线打分，两项均 ≥10 才有底仓资格；守多攻少（防守仓 ≥ 前锋仓）；龙头参考期 21/63 交易日（见 scoring_rules.md）

### 2. a-share-market-data（行情数据自动化）

```bash
# 实时行情
python3 scripts/fetch_quotes.py sh600030 sz000858 sh601888

# 飞书多维表格每日自动更新（模板，填配置即用）
python3 scripts/update_holdings_template.py
```

- 新浪财经 API（免费、无需 key、带 Referer 即可）
- 飞书多维表格推荐表结构 + 建表命令 + 公式字段说明见 SKILL.md
- 定时更新：Hermes 用户用 `hermes cron create`；其他 Agent 用户用系统 cron（`30 15 * * 1-5` 交易日收盘自动更新，见适配分支 SKILL.md）

---

## 🗂 版本管理

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07 | water-zhanfa 初版（GBK 编码） |
| v1.1 | 2026-08-01 | 编码修复；新增 investment-advisor v1.4、a-share-market-data v2.0 |
| v2.0 | 2026-08-01 | water-zhanfa 并入 investment-advisor（龙头参考期/逐笔明细/节奏模板），删 water-zhanfa |
| v2.0.1 | 2026-08-01 | 开源发布：MIT License + NOTICE 署名保护 |
| v2.0.2 | 2026-08-01 | README 统一为单份（两种形式差异并入），main 主维护，适配分支只做个性化适配 |

## 📝 贡献规范

- **方法升级**：提交到 `main`，然后 `git checkout adapt-other-agents && git merge main` 同步
- **适配改动**：只在 `adapt-other-agents` 改格式外壳（路径 / cron / frontmatter），不动方法内核
- README 只维护 main 一份，不按分支拆分
- 技能文件结构遵循 AI Agent skill 规范（SKILL.md frontmatter + scripts/ + references/）
- 中文内容统一 UTF-8 编码
- 禁止提交个人持仓、API token、手机号等敏感数据（模板用 `<your_xxx>` 占位）
- 版本变更记录在对应 SKILL.md 头部 + 本 README 版本表

## 📄 开源协议

本项目采用 **MIT License**（见 [LICENSE](LICENSE)），署名与版权保护条款见 [NOTICE.md](NOTICE.md)。

**使用前提：**
- 使用、修改、分发本项目或其衍生作品时，**必须保留版权声明与作者署名**（Copyright © 2026 JudyMiMiLu），不得删除、遮盖或篡改
- 衍生作品应注明"基于 WaterTradingSkill 修改"并保留原始仓库引用
- 删除/篡改署名属于对著作权人署名权的侵犯，作者保留依法追责的权利
- 本项目为投资**分析方法与工具**，按 MIT 协议"AS IS"提供，不构成任何投资建议，作者不对使用后果承担责任

## ⚠️ 免责声明

本仓库技能为投资**分析方法与工具**，不构成任何投资建议。股市有风险，决策需谨慎。
