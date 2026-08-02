# WaterTradingSkill ｜ 水战法投资技能集

面向 A 股投资者的 **AI Agent 技能**，一套"量化打分 + 行情数据自动化"完整投资工作流。

> 版本：v3.1 ｜ 更新：2026-08-01 ｜ 仓库：[JudyMiMiLu/WaterTradingSkill](https://github.com/JudyMiMiLu/WaterTradingSkill)

---

## 📦 包含技能

| 技能 | 版本 | 定位 | 回答什么 |
|------|------|------|----------|
| [investment-advisor](skills/investment-advisor/) | v3.1 | 投资方法论 + 数据工具 | 五步框架分析、WATER/233 打分、调仓纪律、行情查询、飞书表格自动更新 |

### 技能说明

```
investment-advisor v3.1
├── 方法论层：五步框架（趋势-位置-打分-角色-仓位）+ 量化打分 + 调仓纪律 + 复盘
└── 数据层：新浪实时行情 + 腾讯历史K线 + 飞书多维表格自动化 + cron 定时更新
```

> **历史**：v1.x 含 water-zhanfa（水战法经验版）与 a-share-market-data（数据工具）。v2.0 将 water-zhanfa 精华并入；v3.0 将 a-share-market-data 合并为单一 skill，方法 + 数据一体化。

---

## 🚀 快速开始

### 前置条件

- 任意 AI Agent 客户端（支持技能/提示词注入即可）
- [lark-cli](https://open.feishu.cn)（如需飞书多维表格）：`npm install -g @larksuite/cli` + `npx -y skills add https://open.feishu.cn --skill -y`
- Python 3.10+（运行数据脚本）

### 安装技能

```bash
git clone https://github.com/JudyMiMiLu/WaterTradingSkill.git
cp -r WaterTradingSkill/skills/investment-advisor ~/.hermes/skills/
```

重启 Agent 会话后，向 agent 说：
- "分析我的持仓组合" / "XX 能不能买" → investment-advisor（方法论）
- "更新持仓行情" → investment-advisor（数据工具）

---

## 📖 使用说明

### 投资分析（方法论）

五步框架：`先看趋势 → 再看位置 → 买点评分 → 决定底仓 → 配组合控风险`。

- 提供持仓 CSV（模板：`skills/investment-advisor/references/holdings_template.csv`）或直接对话说明
- 产出：组合体检 / 标的买点卖点准入 / 调仓纪律核对 / 逐笔买卖明细 / 复盘
- 核心规则：WATER 打分 + 233 年线打分，两项均 ≥10 才有底仓资格；守多攻少（防守仓 ≥ 前锋仓）；龙头参考期 21/63 交易日（见 scoring_rules.md）

### 行情数据（数据工具）

```bash
# 实时行情
python3 scripts/fetch_quotes.py sh600030 sz000858 sh601888

# 飞书多维表格每日自动更新（模板，填配置即用）
python3 scripts/update_holdings_template.py
```

- 新浪财经 API（免费、无需 key、带 Referer 即可）
- 腾讯历史 K 线 API（250 根日线，非大陆 IP 可用）
- 飞书多维表格推荐表结构 + 建表命令 + 公式字段说明见 SKILL.md
- cron 定时：`30 15 * * 1-5` 交易日收盘自动更新

---

## 🗂 版本管理

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07 | water-zhanfa 初版（GBK 编码） |
| v1.1 | 2026-08-01 | 编码修复；新增 investment-advisor v1.4、a-share-market-data v2.0 |
| v2.0 | 2026-08-01 | water-zhanfa 并入 investment-advisor |
| v2.0.1 | 2026-08-01 | 添加 MIT License 与署名保护（NOTICE.md） |
| v3.0 | 2026-08-01 | a-share-market-data 合并入 investment-advisor，单一 skill 一体化 |
| v3.1 | 2026-08-01 | 斜率三档碗判定 + 判断权行使补充维度 |

## 📄 开源协议

本项目采用 **MIT License**（见 [LICENSE](LICENSE)），署名与版权保护条款见 [NOTICE.md](NOTICE.md)。

**使用前提：**
- 使用、修改、分发本项目或其衍生作品时，**必须保留版权声明与作者署名**（Copyright © 2026 JudyMiMiLu），不得删除、遮盖或篡改
- 衍生作品应注明"基于 WaterTradingSkill 修改"并保留原始仓库引用
- 删除/篡改署名属于对著作权人署名权的侵犯，作者保留依法追责的权利
- 本项目为投资**分析方法与工具**，按 MIT 协议"AS IS"提供，不构成任何投资建议，作者不对使用后果承担责任

## 📝 贡献规范

- 技能文件结构遵循通用 AI Agent skill 规范（`SKILL.md` frontmatter + scripts/ + references/）
- 中文内容统一 UTF-8 编码
- 禁止提交个人持仓、API token、手机号等敏感数据（模板用 `<your_xxx>` 占位）
- 版本变更记录在对应 SKILL.md 头部 + 本 README 版本表

## ⚠️ 免责声明

本仓库技能为投资**分析方法与工具**，不构成任何投资建议。股市有风险，决策需谨慎。
