# WaterTradingSkill ｜ 水战法投资技能集

面向 A 股投资者的 **Hermes Agent 技能集**，一套从"交易战法"到"量化打分"再到"行情数据自动化"的完整投资工作流。

> 版本：v1.1 ｜ 更新：2026-08-01 ｜ 仓库：[JudyMiMiLu/WaterTradingSkill](https://github.com/JudyMiMiLu/WaterTradingSkill)

---

## 📦 包含技能

| 技能 | 版本 | 定位 | 回答什么 |
|------|------|------|----------|
| [water-zhanfa](skills/water-zhanfa/) | v1.0 | 原始交易战法 | 水战法：冲刺波/A杀/碗底蓄水，逐笔买卖与收益计算 |
| [investment-advisor](skills/investment-advisor/) | v1.4 | 投资方法论 | 五步框架：趋势-位置-打分-角色-仓位，调仓纪律 |
| [a-share-market-data](skills/a-share-market-data/) | v2.0 | 数据与自动化 | 新浪行情 API、飞书多维表格读写、每日自动更新 |

### 三者关系

```
water-zhanfa（战法，经验层）
    ↓ 升级量化
investment-advisor（方法论层：WATER 打分 + 233 年线 + 角色仓位）
    ↓ 落地执行
a-share-market-data（工具层：行情拉取 + 飞书表格 + cron 监控）
```

water-zhanfa 是经验版水战法；investment-advisor 把它量化成可判定规则（WATER 打分、动作纪律）；a-share-market-data 把持仓监控自动化。

---

## 🚀 快速开始

### 前置条件

- [Hermes Agent](https://hermes-agent.nousresearch.com)（CLI 或桌面版）
- [lark-cli](https://open.feishu.cn)（如需飞书多维表格）：`npm install -g @larksuite/cli` + `npx -y skills add https://open.feishu.cn --skill -y`

### 安装技能

把 `skills/` 下的三个目录复制到 `~/.hermes/skills/`：

```bash
git clone git@github.com:JudyMiMiLu/WaterTradingSkill.git
cp -r WaterTradingSkill/skills/* ~/.hermes/skills/
```

重启 Hermes 会话后，向 agent 说：
- "用 water 战法分析 600900" → water-zhanfa
- "分析我的持仓组合" / "XX 能不能买" → investment-advisor
- "更新持仓行情" → a-share-market-data

---

## 📖 各技能使用说明

### 1. water-zhanfa（水战法）

分析沪深 A 股的水战法形态，输出买卖节奏。

```powershell
# 收益计算
python scripts/calc_water_returns.py --prices data/000001_daily.csv --signals data/000001_signals.csv --capital 100000 --lot-size 100

# K线图（红B绿S标注）
python scripts/plot_kline_bs.py --prices data/000001_daily.csv --signals data/000001_signals.csv --start 2024-09-24 --end <today> --out outputs/000001_kline_bs.svg
```

CSV 格式见 `skills/water-zhanfa/references/water_csv_schema.md`。

### 2. investment-advisor（投资方法论）

五步框架：`先看趋势 → 再看位置 → 买点评分 → 决定底仓 → 配组合控风险`。

- 提供持仓 CSV（模板：`skills/investment-advisor/references/holdings_template.csv`）或直接对话说明
- 产出：组合体检 / 标的买点卖点准入 / 调仓纪律核对 / 复盘
- 核心规则：WATER 打分 + 233 年线打分，两项均 ≥10 才有底仓资格；守多攻少（防守仓 ≥ 前锋仓）

### 3. a-share-market-data（行情数据自动化）

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
| v1.1 | 2026-08-01 | 编码修复（GBK→UTF-8）；新增 investment-advisor v1.4、a-share-market-data v2.0；README |

## 📝 贡献规范

- 技能文件结构遵循 Hermes skill 规范（SKILL.md frontmatter + scripts/ + references/）
- 中文内容统一 UTF-8 编码
- 禁止提交个人持仓、API token、手机号等敏感数据（模板用 `<your_xxx>` 占位）
- 版本变更记录在对应 SKILL.md 头部 + 本 README 版本表

## ⚠️ 免责声明

本仓库技能为投资**分析方法与工具**，不构成任何投资建议。股市有风险，决策需谨慎。
