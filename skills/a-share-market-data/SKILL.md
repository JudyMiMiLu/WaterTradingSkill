---
name: a-share-market-data
description: >
  Fetch real-time A-share stock/ETF quotes and historical data from a Linux server.
  Covers the Sina Finance HTTP API (verified working), akshare pitfalls, and Yahoo Finance
  limitations. Use when the user needs current stock prices, intraday quotes, or market data
  for A-share (沪深) securities. Pairs with the investment-advisor skill for portfolio analysis.
---

# A 股实时行情数据获取

> 版本：v2.0 ｜ 日期：2026-08-01 ｜ 新增：飞书多维表格推荐表结构（序号主字段+角色父记录分组+¥/百分比格式）、建表流程、字段 ID 动态解析模板 v2；v1.0 验证新浪 API 与 lark-cli 链路

## 何时使用

- 用户需要 A 股实时/最新股价
- investment-advisor 做组合体检时需要更新现价
- 用户问「某只票现在多少钱」
- 需要批量拉多只股票的实时行情

## 方案优先级

| 优先级 | 方案 | 状态 | 适用场景 |
|---|---|---|---|
| 1 | **新浪财经 HTTP API** | ✅ 可用 | 实时行情，批量拉取，无需安装 |
| 2 | akshare（东财接口） | ❌ 不可用 | 非大陆 IP 被拒（RemoteDisconnected） |
| 3 | akshare（新浪全市场） | ⚠️ 慢 | `stock_zh_a_spot()` 需分 70 页，>30s |
| 4 | Agent 自带 stocks skill（如 Hermes） | ⚠️ 视环境 | 多走 Yahoo Finance，服务器访问常超时 |

## 新浪财经 API（首选）

### 基本用法

```python
import requests

# 股票代码前缀：沪市 sh，深市 sz
codes = ['sh600030', 'sz000858', 'sh601888']
url = f"https://hq.sinajs.cn/list={','.join(codes)}"
headers = {"Referer": "https://finance.sina.com.cn"}  # 必须带 Referer！
r = requests.get(url, headers=headers, timeout=10)
```

### 返回格式

```
var hq_str_sh600030="中信证券,今开,昨收,最新价,最高,最低,买一,卖一,成交量(股),成交额,..."
```

字段索引（0-based）：
- `[0]` 名称
- `[1]` 今开
- `[2]` 昨收
- `[3]` 最新价
- `[4]` 最高
- `[5]` 最低
- `[8]` 成交量（股）
- `[9]` 成交额

涨跌幅 = `(最新价 - 昨收) / 昨收 * 100`

### 批量拉取脚本

见 `scripts/fetch_quotes.py`，可直接运行：

```bash
python3 <skill_dir>/scripts/fetch_quotes.py sh600030 sz000858 sh601888
```

支持任意数量股票代码，输出表格。

## 注意事项

- **必须带 `Referer: https://finance.sina.com.cn`**，否则返回 403。
- ETF 代码前缀同股票：沪市 `sh`（如 sh512890 红利低波）、深市 `sz`（如 sz159647 中药ETF）。
- **部分 ETF 可能无数据**（如 sh159992 创新药曾返回空字符串），需换源或让用户手动补充。
- 盘外时间返回上一交易日收盘数据。
- 涨跌幅需自己计算，API 不直接返回。
- 新浪接口无频率限制（合理使用即可），无需 API Key。

## akshare 安装（备用）

```bash
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装成功，但东财接口从非大陆 IP 直连被拒。如未来服务器迁至大陆或加代理，可重测 `stock_zh_a_spot_em()`。

## 历史日线数据（2026-07-31 已验证可用）

### 腾讯 K 线 API（首选，已验证 250 根）

```python
import requests, json
r = requests.get(
    "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600438,day,,,250,qfq",
    headers={"Referer": "https://gu.qq.com/"}, timeout=10)
data = r.json()
klines = data['data']['sh600438'].get('day') or data['data']['sh600438'].get('qfqday')
# 每根: [日期, 开, 收, 高, 低, 成交量]  ← 注意顺序是 开/收/高/低！
# klines[-1] 是最新一根，列表按时间升序，需 reversed() 得到 P[0]=最新
```

关键点：
- 返回顺序按时间升序（最旧在前），计算 MA233/回撤前要 `list(reversed(...))`
- 每根 bar 格式 `[date, open, close, high, low, volume]`——**收在 index 2**
- `qfq` = 前复权；`day` 键有值时优先用，否则回退 `qfqday`
- 已验证：250 根日线可一次拉全，非大陆 IP 可用

### 新浪 K 线 API（备选，已验证）

```python
r = requests.get(
    "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
    "?symbol=sh600438&scale=240&ma=no&datalen=250",
    headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
# 返回 JSON 数组: [{"day":"2025-07-08","open":"18.350","high":"20.020","low":"18.180","close":"20.020","volume":"145148665"}, ...]
# 键是字符串，需 float() 转换；同样按时间升序
```

### 计算 MA233 等指标

```python
closes = [float(k[2]) for k in klines]      # 腾讯格式
P = list(reversed(closes))                   # P[0] = 最新
ma233 = sum(P[:233]) / min(233, len(P))      # 数据不足 233 时用可用长度并标注
H = max(P[:250]); r = (H - P[0]) / H         # 一年高点回撤
vol20 = statistics.pstdev(P[:20]) / (sum(P[:20])/20)  # 波动率
```

完整的 WATER/233 打分计算见 investment-advisor 的 `references/scoring_rules.md`。

> 注：实时行情用 hq.sinajs.cn，历史 K 线用 web.ifzq.gtimg.cn（腾讯）或 quotes.sina.cn（新浪）——两者是不同接口，不要混用。

## 与 investment-advisor skill 配合

investment-advisor 的「扩展点」提到行情接入和定时提醒。本 skill 是这两个扩展点的实现：

- 用 `scripts/fetch_quotes.py` 拉实时价
- 替换持仓 CSV 中的 `现价` 列
- 重新计算市值、浮盈亏、占比

### 飞书多维表格持仓监控（已实现）

完整链路：`新浪API -> Python脚本 -> lark-cli -> 飞书多维表格 -> 调仓触发线检查 -> 飞书推送`

**推荐表结构（2026-08-01 实战验证）：**

```
序号(主字段) → 名称 → 代码 → 角色 → 父记录 → 现价¥ → 今日涨跌幅% → 成本价¥ → 数量
→ 持仓市值¥ → 持仓成本¥ → 浮盈亏¥ → 浮盈亏比% → 占总资产% → 建仓日期 → 昨收价¥ → 更新时间
```

关键设计决策：
- **主字段 = 序号**：主字段（索引列）不能移动/隐藏/删除，用序号避免代码列锁死在第一列
- **角色做父记录**：建 5 条角色父记录（中锋/控球后卫/前锋/第六人/现金），个股通过「父记录」link 字段（自关联，`link_table` 指向本表）关联，视图按父记录分组 = 父子层级
- **金额字段**：`style: {"type":"currency","precision":2,"currency_code":"CNY"}` + 表头加 ¥
- **比率字段**（今日涨跌幅/浮盈亏比/占总资产）：`style: {"type":"plain","precision":2,"percentage":true,"thousands_separator":true}`
- **涨跌颜色**：飞书 UI 条件格式（`<0` 绿、`>0` 红），API 不支持，手动配一次
- 冗余字段不做：如「今日涨跌」（单股涨跌金额）可由涨跌幅% 替代

**建表流程（角色父记录 + 自关联）：**

```bash
# 1. 先建表（link 字段需要 table_id，必须第二步加）
lark-cli base +table-create --base-token <B> --name "持仓明细" \
  --fields '[{"name":"序号","type":"text"},{"name":"名称","type":"text"},{"name":"代码","type":"text"},{"name":"角色","type":"select","options":[{"name":"中锋"},{"name":"控球后卫"},{"name":"前锋"},{"name":"第六人"},{"name":"现金"}]},...]' --as user
# 2. 加自关联父记录字段
lark-cli base +field-create --base-token <B> --table-id <T> \
  --json '{"name":"父记录","type":"link","link_table":"<T>"}' --as user
# 3. 建角色父记录（序号20-24）
# 4. 个股记录「父记录」= [{"id": <父记录record_id>}]
# 5. 视图分组
lark-cli base +view-set-group --base-token <B> --table-id <T> --view-id <V> \
  --json '{"group_config":[{"field":"父记录","desc":false}]}' --as user
```

### 交易明细表结构（2026-08-01 更新）

```
日期 → 名称 → 代码 → 动作(建仓/买入/卖出/分红/初始持仓) → 价格¥ → 数量 → 手动金额¥ → 金额¥(公式) → 备注
```

**金额公式字段**（自动计算，无需手填）：
```
IFS(CONTAIN(LIST("建仓","买入","卖出"), 动作), ROUND(价格*数量,0),
    动作="分红", 手动金额,
    TRUE, 0)
```
- 建仓/买入/卖出 → 价格 × 数量（四舍五入）
- 分红 → 手动金额（分红无价格×数量，手动填）
- 其他 → 0

创建公式字段时用 `+field-create` 传 `type: formula` + `expression`（需先读 lark-base 的 formula-field-guide.md）。字段 ID 用 `bitable::$table[<table_id>].$field[<field_id>]` 引用。

**lark-cli record-list 返回格式（重要坑）：**

`lark-cli base +record-list --format json` 返回的是**矩阵格式**，不是对象数组：

```json
{
  "data": {
    "fields": ["代码", "今日涨跌", "成本价", ...],
    "data": [["002352", 0.38, 34.87, ...], ...],
    "record_id_list": ["recvqUiROtXt2O", ...],
    "field_id_list": ["fldT8nbqhy", ...]
  }
}
```

**不要假设返回 `items[].fields.代码`**。要用 `fields.index("代码")` 找到列索引，再到 `data[i][col_idx]` 取值，`record_id_list[i]` 是对应记录ID。

**lark-cli record-upsert 更新记录：**

```bash
lark-cli base +record-upsert \
  --base-token <token> --table-id <table_id> \
  --record-id <record_id> \
  --json '{"现价¥": 78.56, "浮盈亏¥": -1011}' \
  --as user
```

坑点：
- `--json` 是**顶层 field map**，不要包在 `{"fields": {...}}` 里
- **没有 `+record-update` 命令**，更新统一走 `+record-upsert --record-id`
- 百分比字段传小数（0.0451 = 4.51%）
- `--json @file` 要求文件在当前目录下（相对路径），`/tmp/` 路径被拒绝
- `+record-batch-create` 的 `--json` 结构是 `{"fields":["列1","列2"], "rows":[["v1","v2"]]}`，rows 按 fields 顺序对齐
- **字段顺序**：`+view-set-visible-fields` 的 visible_fields 数组控制顺序，但**主字段被 API 强制排第一**，无法移动
- **字段更新**：`+field-update` 是 PUT 全量语义（不是 patch），需带完整字段 JSON + `--yes`（高风险）
- **脚本用字段 ID 而非字段名**：字段名可能改（如 现价→现价¥），用 `+field-list` 动态解析 `名称->ID` 映射，改名不炸脚本（见模板 v2）

**cron job 定时更新（通用方案）：**

```bash
# 任意 cron 工具（Linux crontab / macOS launchd / Windows 任务计划 / Hermes cron）均可
# 脚本放在任意目录，cron 创建时指向脚本绝对路径
30 15 * * 1-5  python3 /path/to/update_holdings.py
```

Hermes 用户可用内置 cron：
```bash
hermes cron create \
  --schedule "30 15 * * 1-5" \
  --script update_holdings.py \
  --name "持仓行情每日收盘更新" \
  --deliver origin
```

**完整更新脚本**见 `scripts/update_holdings.py`（实战版，含个人数据）和 `scripts/update_holdings_template.py`（v2 通用模板，动态字段 ID 解析，填配置即用）。
1. 建 link 字段「父记录」（type=link，关联本表）
2. 建父记录：`+record-batch-create` 插入角色行（如 中锋/控球后卫/前锋/第六人/现金，数量为空）
3. 子记录 link：`+record-upsert --record-id <子id> --json '{"父记录":[{"id":"<父id>"}]}'`（link 字段 CellValue 是 `[{"id":"recxxx"}]`）
4. 视图分组：`+view-set-group --json '{"group_config":[{"field":"父记录","desc":false}]}'`
5. 结果验证：`+record-list` 看每个子记录「父记录」非空；视图 `+view-get` 的 `_meta.group` 显示 link 字段 id

**⚠️ 主字段（primary field）坑：** visible_fields 里主字段被 API 强制排第一列，无法通过 `+view-set-visible-fields` 挪走。本表主字段是「代码」，用户要求「名称」放代码左侧只能：a) UI 手动拖列；b) 重建表以「名称」为主字段。其他非主字段顺序可自由调整。

**重建表方案（2026-07-31 实测，用户选此路）：**
- `+table-create --fields` 数组**第一个元素 = 主字段**（如 `[{"name":"序号","type":"text"},{"name":"名称",...}]` → 序号成为主字段，不再霸占第一列）
- 建表时字段里**不能直接放自关联 link**（`link_table` 用表名报 `800030104 not_found`）→ 必须分两步：先建表拿 table_id，再 `+field-create --json '{"name":"父记录","type":"link","link_table":"<table_id>"}'`
- 迁移数据：`+record-list` 拉旧表 → 转 `{"fields":[...],"rows":[[...]]}` → `+record-batch-create` 写入新表 → 建父记录 → 子记录 upsert link → `+view-set-group` 按父记录分组 → `+view-set-visible-fields` 排新顺序
- **迁移后必须同步改 cron 更新脚本里的 table_id**，否则每日行情更新仍写旧表（用户表重建后 cron b33d1dc43148 指向 tbl0drlIz4pBQXhq，需改到新表）

**字段格式 + 更多坑（2026-08-01 实测）：**
- 百分比：`{"type":"number","style":{"type":"plain","precision":2,"percentage":true,"thousands_separator":true}}`（数据仍存小数，0.0324 显示 3.24%）
- 货币：`{"type":"number","style":{"type":"currency","precision":2,"currency_code":"CNY"}}`；表头加 ¥ = 字段名直接带 ¥
- **`+field-update` 是 FULL PUT 不是 patch**，需 `--yes`；会偶发瞬时失败（exit 0 但 ok=false），重试一次即过
- **批量建表会静默丢字段**：一次传 17 字段返回 ok，实际少建 1 个 → 建表后必须 `+field-list` 对照核对，缺了补 `+field-create` 再迁移数据
- **脚本写字段 ID 而非字段名**：字段改名（现价→现价¥）后按名写全挂；用 fldXXX 则改名不影响
- 完整命令模板见 [references/bitable-table-rebuild.md](references/bitable-table-rebuild.md)

**完整更新脚本**见 `scripts/update_holdings.py`，功能包括：拉新浪行情 -> 计算 -> 逐条更新飞书记录 -> 检查调仓触发线。

可复制的模板版本见 `scripts/update_holdings_template.py`（已去除个人持仓数据，填入自己的配置即可使用）。

## 已知不工作的方案

- **Yahoo Finance**（包括部分 Agent 自带的 stocks skill）：从国内服务器访问常超时
- **akshare 东财接口**（`stock_zh_a_spot_em`、`stock_zh_a_hist`、`stock_bid_ask_em`）：RemoteDisconnected
- **akshare 新浪全市场**（`stock_zh_a_spot`）：可工作但需 30s+ 拉全市场 70 页
