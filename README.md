# WaterTradingSkill ｜ 水战法投资技能集

面向 A 股投资者的 **AI Agent 技能集**（Hermes / WorkBuddy / 豆包等），一套从"交易战法"到"量化打分"再到"行情数据自动化"的完整投资工作流。

> 版本：v2.0 ｜ 更新：2026-08-01 ｜ 仓库：[JudyMiMiLu/WaterTradingSkill](https://github.com/JudyMiMiLu/WaterTradingSkill)

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

## 🚀 快速开始

### 前置条件

- 任意 AI Agent 客户端（支持技能/提示词注入即可）：
  - **Hermes Agent**（本分支默认）：CLI 或桌面版
  - **WorkBuddy / 豆包 / Kimi / 其他普通产品**：请切换到 `adapt-other-agents` 分支获取通用适配版
- [lark-cli](https://open.feishu.cn)（如需飞书多维表格）：`npm install -g @larksuite/cli` + `npx -y skills add https://open.feishu.cn --skill -y`
- Python 3.10+（运行数据脚本）

### 安装技能（Hermes 版）

把 `skills/` 下的目录复制到 `~/.hermes/skills/`：

```bash
git clone git@github.com:JudyMiMiLu/WaterTradingSkill.git
cd WaterTradingSkill
cp -r skills/investment-advisor ~/.hermes/skills/
cp -r skills/a-share-market-data ~/.hermes/skills/
```

重启 Hermes 会话后，向 agent 说：
- "分析我的持仓组合" / "XX 能不能买" → investment-advisor
- "更新持仓行情" → a-share-market-data

### 其他 Agent 用户（WorkBuddy / 豆包 等）

```bash
git clone git@github.com:JudyMiMiLu/WaterTradingSkill.git
git checkout adapt-other-agents
```

该分支的 `SKILL.md` 与提示词格式已适配通用 Agent（见分支内 README 的适配说明）。

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
- cron 定时：`30 15 * * 1-5` 交易日收盘自动更新

---

## 🗂 版本管理

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07 | water-zhanfa 初版（GBK 编码） |
| v1.1 | 2026-08-01 | 编码修复；新增 investment-advisor v1.4、a-share-market-data v2.0 |
| v2.0 | 2026-08-01 | water-zhanfa 并入 investment-advisor（龙头参考期/逐笔明细/节奏模板），删 water-zhanfa |

## 📝 贡献规范

- 技能文件结构遵循通用 AI Agent skill 规范（`SKILL.md` frontmatter + scripts/ + references/），适配各 Agent 时只改格式外壳，不改方法内核
- 中文内容统一 UTF-8 编码
- 禁止提交个人持仓、API token、手机号等敏感数据（模板用 `<your_xxx>` 占位）
- 版本变更记录在对应 SKILL.md 头部 + 本 README 版本表
- `main` 分支针对 Hermes Agent；其他 Agent（WorkBuddy/豆包等）适配在 `adapt-other-agents` 分支，两分支保持方法内核同步

## 📄 开源协议

本项目采用 **MIT License**（见 [LICENSE](LICENSE)）。

**使用前提：**
- 使用、修改、分发本项目或其衍生作品时，**必须保留版权声明与作者署名**（Copyright © 2026 JudyMiMiLu），不得删除、遮盖或篡改
- 衍生作品应注明"基于 WaterTradingSkill 修改"并保留原始仓库引用
- 删除/篡改署名属于对著作权人署名权的侵犯，作者保留依法追责的权利
- 本项目为投资**分析方法与工具**，按 MIT 协议"AS IS"提供，不构成任何投资建议，作者不对使用后果承担责任

## ⚠️ 免责声明

本仓库技能为投资**分析方法与工具**，不构成任何投资建议。股市有风险，决策需谨慎。
