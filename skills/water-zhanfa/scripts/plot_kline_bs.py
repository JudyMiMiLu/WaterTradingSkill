#!/usr/bin/env python3
"""Draw an OHLC candlestick SVG with red B and green S markers."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Candle:
    d: date
    o: float
    h: float
    l: float
    c: float


@dataclass
class Signal:
    d: date
    action: str
    price: Optional[float]


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    return {
        str(k).strip().lower().lstrip("\ufeff"): ("" if v is None else str(v).strip())
        for k, v in row.items()
    }


def pick_key(row: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        if k in row and row[k] != "":
            return row[k]
    raise KeyError(f"Missing required keys: {keys}")


def parse_optional_float(v: str) -> Optional[float]:
    t = "" if v is None else str(v).strip()
    if not t:
        return None
    return float(t)


def normalize_action(raw: str) -> str:
    t = raw.strip().upper()
    if t in {"B", "BUY", "买", "买入"}:
        return "B"
    if t in {"S", "SELL", "卖", "卖出"}:
        return "S"
    return t


def load_candles(path: Path, start: date, end: date) -> List[Candle]:
    candles: List[Candle] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = normalize_row(raw)
            d = parse_date(pick_key(row, ["date", "trade_date", "交易日期", "日期"]))
            if d < start or d > end:
                continue
            o = float(pick_key(row, ["open", "o", "开盘"]))
            h = float(pick_key(row, ["high", "h", "最高"]))
            l = float(pick_key(row, ["low", "l", "最低"]))
            c = float(pick_key(row, ["close", "c", "收盘"]))
            candles.append(Candle(d=d, o=o, h=h, l=l, c=c))
    candles.sort(key=lambda x: x.d)
    if not candles:
        raise ValueError("No candle data found in selected date range.")
    return candles


def load_signals(path: Path, start: date, end: date) -> List[Signal]:
    signals: List[Signal] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = normalize_row(raw)
            d = parse_date(pick_key(row, ["date", "trade_date", "交易日期", "日期"]))
            if d < start or d > end:
                continue
            action = normalize_action(pick_key(row, ["action", "side", "signal", "动作"]))
            price = parse_optional_float(row.get("price", ""))
            if price is None:
                price = parse_optional_float(row.get("成交价", ""))
            if price is None:
                price = parse_optional_float(row.get("价格", ""))
            signals.append(Signal(d=d, action=action, price=price))
    signals.sort(key=lambda x: x.d)
    return signals


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))


def render_svg(candles: List[Candle], signals: List[Signal], title: str) -> str:
    n = len(candles)
    width = max(1000, n * 10 + 180)
    height = 640
    left, right, top, bottom = 70, 30, 60, 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    low = min(c.l for c in candles)
    high = max(c.h for c in candles)
    if high <= low:
        high = low + 1.0
    pad = (high - low) * 0.05
    y_min, y_max = low - pad, high + pad

    def y(price: float) -> float:
        return top + (y_max - price) / (y_max - y_min) * plot_h

    x_step = plot_w / max(n, 1)
    body_w = clamp(x_step * 0.62, 2.0, 11.0)

    date_to_idx = {c.d: i for i, c in enumerate(candles)}
    date_to_close = {c.d: c.c for c in candles}
    date_to_low = {c.d: c.l for c in candles}
    date_to_high = {c.d: c.h for c in candles}

    lines: List[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
    lines.append(f'<text x="{left}" y="35" fill="#111" font-size="20" font-family="Arial" font-weight="700">{esc(title)}</text>')

    for i in range(7):
        py = top + plot_h * i / 6
        pval = y_max - (y_max - y_min) * i / 6
        lines.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_w}" y2="{py:.2f}" stroke="#e9ecef" stroke-width="1"/>')
        lines.append(f'<text x="{left - 8}" y="{py + 4:.2f}" text-anchor="end" fill="#666" font-size="11" font-family="Arial">{pval:.2f}</text>')

    lines.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#d0d7de" stroke-width="1"/>')

    for i, c in enumerate(candles):
        cx = left + (i + 0.5) * x_step
        yo, yh, yl, yc = y(c.o), y(c.h), y(c.l), y(c.c)
        up = c.c >= c.o
        color = "#d7191c" if up else "#1a9641"

        lines.append(f'<line x1="{cx:.2f}" y1="{yh:.2f}" x2="{cx:.2f}" y2="{yl:.2f}" stroke="#333" stroke-width="1"/>')
        ry = min(yo, yc)
        rh = max(abs(yc - yo), 1.0)
        rx = cx - body_w / 2
        lines.append(
            f'<rect x="{rx:.2f}" y="{ry:.2f}" width="{body_w:.2f}" height="{rh:.2f}" '
            f'fill="{color}" stroke="{color}" stroke-width="1"/>'
        )

    tick = max(1, n // 10)
    for i, c in enumerate(candles):
        if i % tick == 0 or i == n - 1:
            cx = left + (i + 0.5) * x_step
            lines.append(f'<line x1="{cx:.2f}" y1="{top + plot_h}" x2="{cx:.2f}" y2="{top + plot_h + 5}" stroke="#999" stroke-width="1"/>')
            lines.append(
                f'<text x="{cx:.2f}" y="{top + plot_h + 20}" text-anchor="middle" '
                f'fill="#666" font-size="10" font-family="Arial">{c.d.strftime("%Y-%m-%d")}</text>'
            )

    marker_radius = 12.0
    marker_font_size = 15
    bs_count = 0
    for s in signals:
        if s.d not in date_to_idx:
            continue
        i = date_to_idx[s.d]
        cx = left + (i + 0.5) * x_step
        price = s.price if s.price is not None else date_to_close[s.d]

        if s.action == "B":
            py = y(min(price, date_to_low[s.d])) + 16
            py = clamp(py, top + 12, top + plot_h - 8)
            lines.append(
                f'<circle cx="{cx:.2f}" cy="{py - 5:.2f}" r="{marker_radius:.1f}" fill="#d7191c" fill-opacity="0.95" stroke="#8f1113" stroke-width="1.2"/>'
            )
            lines.append(
                f'<text x="{cx:.2f}" y="{py:.2f}" text-anchor="middle" fill="#ffffff" font-size="{marker_font_size}" font-family="Arial" font-weight="700">B</text>'
            )
            bs_count += 1
        elif s.action == "S":
            py = y(max(price, date_to_high[s.d])) - 8
            py = clamp(py, top + 12, top + plot_h - 8)
            lines.append(
                f'<circle cx="{cx:.2f}" cy="{py - 5:.2f}" r="{marker_radius:.1f}" fill="#1a9641" fill-opacity="0.95" stroke="#10602a" stroke-width="1.2"/>'
            )
            lines.append(
                f'<text x="{cx:.2f}" y="{py:.2f}" text-anchor="middle" fill="#ffffff" font-size="{marker_font_size}" font-family="Arial" font-weight="700">S</text>'
            )
            bs_count += 1

    lx = width - right - 180
    ly = 30
    lines.append(f'<text x="{lx}" y="{ly}" fill="#d7191c" font-size="13" font-family="Arial" font-weight="700">B = Buy</text>')
    lines.append(f'<text x="{lx + 90}" y="{ly}" fill="#1a9641" font-size="13" font-family="Arial" font-weight="700">S = Sell</text>')

    lines.append("</svg>")
    return "\n".join(lines), bs_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw K-line chart and mark buy/sell points (B/S).")
    parser.add_argument("--prices", required=True, help="Path to daily OHLC CSV file.")
    parser.add_argument("--signals", required=True, help="Path to buy/sell signal CSV file.")
    parser.add_argument("--start", default="2024-09-24", help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date (YYYY-MM-DD).")
    parser.add_argument("--title", default="Water Strategy Kline", help="Chart title.")
    parser.add_argument("--out", default="kline_bs.svg", help="Output SVG path.")
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise ValueError("--end must be >= --start")

    prices_path = Path(args.prices)
    signals_path = Path(args.signals)
    out_path = Path(args.out)

    candles = load_candles(prices_path, start, end)
    signals = load_signals(signals_path, start, end)
    svg, marker_count = render_svg(candles, signals, args.title)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Saved chart to: {out_path.resolve()}")
    print(f"Candles in range: {len(candles)} | B/S markers in range: {marker_count}")


if __name__ == "__main__":
    main()
