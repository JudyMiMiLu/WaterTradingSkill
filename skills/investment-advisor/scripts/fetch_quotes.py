#!/usr/bin/env python3
"""
A 股实时行情批量查询脚本
用法:
  python3 fetch_quotes.py sh600030 sz000858 sh601888
  python3 fetch_quotes.py sh600030 sz000858 --format json

数据源: 新浪财经 hq.sinajs.cn
无需 API Key，无需安装额外依赖（仅 requests）
"""
import sys
import json
import requests

SINA_URL = "https://hq.sinajs.cn/list={codes}"
HEADERS = {"Referer": "https://finance.sina.com.cn"}


def fetch_quotes(codes: list[str]) -> list[dict]:
    """批量获取实时行情"""
    url = SINA_URL.format(codes=",".join(codes))
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "gbk"
    results = []
    for line in r.text.strip().split("\n"):
        try:
            code = line.split("=")[0].split("_")[-1]
            data = line.split('"')[1]
            if not data:
                results.append({"code": code, "name": None, "error": "no data"})
                continue
            f = data.split(",")
            name = f[0].strip()
            prev_close = float(f[2])
            curr = float(f[3])
            chg = curr - prev_close
            chg_pct = (chg / prev_close * 100) if prev_close else 0
            results.append({
                "code": code,
                "name": name,
                "price": curr,
                "prev_close": prev_close,
                "open": float(f[1]),
                "high": float(f[4]),
                "low": float(f[5]),
                "volume": int(float(f[8])),
                "amount": float(f[9]),
                "change": round(chg, 4),
                "change_pct": round(chg_pct, 2),
            })
        except Exception as e:
            results.append({"code": code if "code" in dir() else "?", "error": str(e)})
    return results


def print_table(results: list[dict]):
    """表格输出"""
    print(f"{'名称':12s} {'代码':10s} {'现价':>8s} {'涨跌':>7s} {'涨跌幅':>7s} {'今开':>8s} {'最高':>8s} {'最低':>8s}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: -x.get("change_pct", -999)):
        if "error" in r:
            print(f"  {r['code']:10s} ERROR: {r['error']}")
            continue
        arrow = "🔴" if r["change_pct"] < 0 else ("🟢" if r["change_pct"] > 0 else "⚪")
        print(f"{r['name']:12s} {r['code']:10s} {r['price']:>8.2f} {r['change']:>+7.2f} {r['change_pct']:>+6.2f}% {r['open']:>8.2f} {r['high']:>8.2f} {r['low']:>8.2f} {arrow}")


def main():
    args = sys.argv[1:]
    fmt = "table"
    codes = []
    for a in args:
        if a == "--format" or a == "-f":
            fmt = None  # set by next arg
        elif fmt is None:
            fmt = a
        else:
            codes.append(a)

    if not codes:
        print("用法: python3 fetch_quotes.py sh600030 sz000858 [--format table|json]")
        sys.exit(1)

    # 代码前缀校验
    for i, c in enumerate(codes):
        if not c.startswith(("sh", "sz")):
            # 尝试自动补前缀
            if c.startswith("6"):
                codes[i] = "sh" + c
            elif c.startswith(("0", "3")):
                codes[i] = "sz" + c
            elif c.startswith("1") and len(c) == 6:
                codes[i] = "sz" + c

    results = fetch_quotes(codes)

    if fmt == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_table(results)


if __name__ == "__main__":
    main()
