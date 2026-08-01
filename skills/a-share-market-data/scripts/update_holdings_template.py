#!/usr/bin/env python3
"""
持仓行情飞书多维表格每日更新脚本（模板 v2 - 2026-08-01）
- 从新浪财经拉取A股实时行情
- 更新飞书多维表格中的持仓记录
- 检查调仓触发线

特性（v2）：
- 字段名动态解析为字段 ID（不再写死 ID，同学用自己的表名也能跑）
- 适配「序号主字段 + 角色父记录分组 + ¥货币/百分比格式」的表结构
- 已移除冗余字段「今日涨跌」

使用前修改 HOLDINGS 和 BASE_TOKEN/TABLE_ID 为你的配置。
运行：python3 update_holdings.py
"""
import requests
import json
import subprocess
from datetime import datetime, timezone, timedelta

# ===== 配置（修改为你的配置） =====
BASE_TOKEN = "<your_base_token>"
TABLE_ID = "<your_table_id>"

# 持仓标的
HOLDINGS = [
    # {"code":"000858","name":"五粮液","role":"前锋","qty":300,"cost":81.947,"build_date":"2026-04-29","sina_code":"sz000858"},
]

CASH = 0  # 现金余额

# ===== 新浪行情 =====
def fetch_sina_quotes(sina_codes):
    url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"
    headers = {"Referer": "https://finance.sina.com.cn"}  # 必须带 Referer！
    r = requests.get(url, headers=headers, timeout=15)
    result = {}
    for line in r.text.strip().split('\n'):
        try:
            scode = line.split('=')[0].split('_')[-1]
            data = line.split('"')[1]
            fields = data.split(',')
            result[scode] = {
                "name": fields[0].strip(),
                "open": float(fields[1]),
                "prev_close": float(fields[2]),
                "price": float(fields[3]),
                "high": float(fields[4]),
                "low": float(fields[5]),
            }
        except:
            pass
    return result

# ===== 飞书 Base 操作 =====
def get_field_id_map():
    """动态获取 字段名 -> 字段ID 映射（兼容不同用户的自定义表）"""
    cmd = [
        "lark-cli", "base", "+field-list",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLE_ID,
        "--format", "json",
        "--as", "user",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(r.stdout)
    if not data.get("ok"):
        return {}
    return {f["name"]: f["id"] for f in data.get("data", {}).get("fields", [])}

def get_all_records():
    """获取表所有记录的 record_id 和代码的映射。返回 {代码: record_id}"""
    cmd = [
        "lark-cli", "base", "+record-list",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLE_ID,
        "--limit", "100",
        "--format", "json",
        "--as", "user",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if not r.stdout.strip():
        return {}

    data = json.loads(r.stdout)
    if not data.get("ok"):
        return {}

    d = data.get("data", {})
    fields = d.get("fields", [])
    rows = d.get("data", [])
    record_ids = d.get("record_id_list", [])

    # 找到"代码"列的索引
    code_idx = fields.index("代码") if "代码" in fields else 0

    mapping = {}
    for i, row in enumerate(rows):
        if i < len(record_ids):
            code_val = str(row[code_idx]) if row[code_idx] else ""
            if code_val and code_val != "-":
                mapping[code_val] = record_ids[i]
            elif code_val == "-":
                mapping["现金"] = record_ids[i]
    return mapping

def update_record(record_id, fields_data):
    """更新单条记录。注意：--json 是顶层 field map，不包在 fields 里"""
    payload_json = json.dumps(fields_data, ensure_ascii=False)
    cmd = [
        "lark-cli", "base", "+record-upsert",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLE_ID,
        "--record-id", record_id,
        "--json", payload_json,
        "--as", "user",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if not r.stdout.strip():
        return False
    data = json.loads(r.stdout)
    return data.get("ok", False)

# ===== 主流程 =====
def main():
    bj_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(bj_tz)
    update_time = now_bj.strftime("%Y-%m-%d %H:%M")

    # 周末跳过
    if now_bj.weekday() >= 5:
        print(f"今天是周末({now_bj.strftime('%A')})，跳过更新")
        return

    print(f"=== 持仓行情更新 {update_time} ===")

    # 0. 动态解析字段 ID
    field_ids = get_field_id_map()
    if not field_ids:
        print("❌ 无法获取字段列表，请检查 BASE_TOKEN/TABLE_ID")
        return
    F = field_ids  # F["现价¥"] -> "fldxxx"

    # 1. 拉新浪行情
    sina_codes = [h["sina_code"] for h in HOLDINGS]
    print(f"正在拉取 {len(sina_codes)} 只标的新浪行情...")
    realtime = fetch_sina_quotes(sina_codes)
    print(f"获取到 {len(realtime)} 只标的行情")

    # 2. 计算数据
    total_mv = 0
    total_cost = 0
    updates = []

    for h in HOLDINGS:
        rt = realtime.get(h["sina_code"], {})
        price = rt.get("price", h["cost"])
        prev_close = rt.get("prev_close", price)
        mv = h["qty"] * price
        cost_val = h["qty"] * h["cost"]
        pnl = mv - cost_val
        pnl_pct = (pnl / cost_val * 100) if cost_val else 0
        chg = price - prev_close
        chg_pct = (chg / prev_close * 100) if prev_close else 0
        total_mv += mv
        total_cost += cost_val
        updates.append({
            "code": h["code"], "name": h["name"],
            "price": round(price, 3), "prev_close": round(prev_close, 3),
            "chg_pct": round(chg_pct, 2),
            "mv": round(mv, 0), "pnl": round(pnl, 0),
            "pnl_pct": round(pnl_pct, 1), "cost_val": round(cost_val, 0),
        })

    total_assets = total_mv + CASH
    total_pnl = total_mv - total_cost

    print(f"总市值: {total_mv:,.0f}  总成本: {total_cost:,.0f}  浮盈亏: {total_pnl:+,.0f} ({total_pnl/total_cost*100:+.1f}%)")
    print(f"现金: {CASH:,.0f}  总资产: {total_assets:,.0f}")

    # 3. 获取飞书表现有记录 ID
    print("正在获取飞书表记录ID...")
    record_map = get_all_records()
    print(f"找到 {len(record_map)} 条已有记录")

    # 4. 逐条更新（用字段 ID，与字段名解耦）
    success_count = 0
    fail_count = 0
    for u in updates:
        rid = record_map.get(u["code"])
        if not rid:
            print(f"  ⚠️ {u['name']}({u['code']}) 未找到记录，跳过")
            fail_count += 1
            continue

        pct_total = u["mv"] / total_assets * 100
        fields_data = {
            F.get("现价¥", "现价"): u["price"],
            F.get("昨收价¥", "昨收价"): u["prev_close"],
            F.get("今日涨跌幅", ""): u["chg_pct"] / 100,  # 百分比字段传小数
            F.get("持仓市值¥", "持仓市值"): u["mv"],
            F.get("持仓成本¥", "持仓成本"): u["cost_val"],
            F.get("浮盈亏¥", "浮盈亏"): u["pnl"],
            F.get("浮盈亏比", ""): u["pnl_pct"] / 100,
            F.get("占总资产", ""): pct_total / 100,
            F.get("更新时间", ""): update_time,
        }
        # 移除空 key（表里没有的字段）
        fields_data = {k: v for k, v in fields_data.items() if k}

        ok = update_record(rid, fields_data)
        if ok:
            success_count += 1
            arrow = "🟢" if u["chg_pct"] > 0 else ("🔴" if u["chg_pct"] < 0 else "⚪")
            print(f"  ✅ {u['name']:8s} {u['price']:>8.3f} {u['chg_pct']:>+6.2f}% {arrow}")
        else:
            fail_count += 1
            print(f"  ❌ {u['name']} 更新失败")

    # 更新现金行
    cash_rid = record_map.get("现金")
    if cash_rid:
        fields_data = {
            F.get("现价¥", "现价"): 1,
            F.get("昨收价¥", "昨收价"): 1,
            F.get("今日涨跌幅", ""): 0,
            F.get("持仓市值¥", "持仓市值"): CASH,
            F.get("持仓成本¥", "持仓成本"): CASH,
            F.get("浮盈亏¥", "浮盈亏"): 0,
            F.get("浮盈亏比", ""): 0,
            F.get("占总资产", ""): CASH / total_assets,
            F.get("更新时间", ""): update_time,
        }
        fields_data = {k: v for k, v in fields_data.items() if k}
        ok = update_record(cash_rid, fields_data)
        if ok:
            success_count += 1
            print(f"  ✅ 现金 {CASH:>8.0f}")

    print(f"\n=== 更新完成: 成功 {success_count}, 失败 {fail_count} ===")
    print(f"总资产: {total_assets:,.0f}  浮盈亏: {total_pnl:+,.0f} ({total_pnl/total_cost*100:+.1f}%)")

    # 检查触发线
    print("\n=== 调仓触发线检查 ===")
    triggers = [
        # (名称, 代码, 触发下限, 触发上限, 动作描述)
        # ("五粮液", "000858", 78, 80, "第一波减100股"),
    ]
    for u in updates:
        for name, code, low, high, action in triggers:
            if u["code"] == code and u["price"] >= low:
                emoji = "🔥" if u["price"] >= high else "⚠️"
                print(f"  {emoji} {name} 现价 {u['price']} 已进入触发区间 [{low}-{high}] -> {action}")

if __name__ == "__main__":
    main()
