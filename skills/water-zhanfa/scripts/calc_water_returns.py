#!/usr/bin/env python3
"""Calculate Water strategy trade records and current return rate from CSV files."""

from __future__ import annotations

import argparse
import bisect
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PriceBar:
    d: date
    close: float


@dataclass
class Signal:
    d: date
    action: str
    price: Optional[float]
    pct: Optional[float]
    amount: Optional[float]
    shares: Optional[float]
    reason: str


@dataclass
class TradeRow:
    d: date
    action: str
    price: float
    shares: float
    amount: float
    cash_after: float
    position_after: float
    pnl_realized: float
    trade_return_pct: Optional[float]
    change_since_prev_trade_pct: Optional[float]
    equity_after: float
    cumulative_return_pct: float
    reason: str


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
    if v is None:
        return None
    t = v.strip()
    if not t:
        return None
    return float(t)


def parse_pct(v: str) -> Optional[float]:
    if v is None:
        return None
    t = v.strip()
    if not t:
        return None
    t = t.replace("％", "%")
    if t.endswith("%"):
        return float(t[:-1]) / 100.0
    x = float(t)
    if x > 1:
        return x / 100.0
    return x


def normalize_action(raw: str) -> str:
    t = raw.strip().upper()
    if t in {"B", "BUY", "买", "买入"}:
        return "B"
    if t in {"S", "SELL", "卖", "卖出"}:
        return "S"
    return t


def action_cn(action: str) -> str:
    return "买入" if action == "B" else "卖出" if action == "S" else action


def load_prices(path: Path) -> Tuple[List[PriceBar], Dict[date, float]]:
    bars: List[PriceBar] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = normalize_row(raw)
            d = parse_date(pick_key(row, ["date", "trade_date", "交易日期", "日期"]))
            close = float(pick_key(row, ["close", "c", "收盘"]))
            bars.append(PriceBar(d=d, close=close))
    bars.sort(key=lambda x: x.d)
    if not bars:
        raise ValueError("No price data found.")
    return bars, {b.d: b.close for b in bars}


def load_signals(path: Path) -> List[Signal]:
    signals: List[Signal] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = normalize_row(raw)
            d = parse_date(pick_key(row, ["date", "trade_date", "交易日期", "日期"]))
            action = normalize_action(pick_key(row, ["action", "side", "signal", "动作"]))

            price = parse_optional_float(row.get("price", ""))
            if price is None:
                price = parse_optional_float(row.get("成交价", ""))
            if price is None:
                price = parse_optional_float(row.get("价格", ""))

            pct = parse_pct(row.get("position_pct", ""))
            if pct is None:
                pct = parse_pct(row.get("仓位比例", ""))
            if pct is None:
                pct = parse_pct(row.get("仓位", ""))

            amount = parse_optional_float(row.get("amount", ""))
            if amount is None:
                amount = parse_optional_float(row.get("成交金额", ""))
            if amount is None:
                amount = parse_optional_float(row.get("金额", ""))

            shares = parse_optional_float(row.get("shares", ""))
            if shares is None:
                shares = parse_optional_float(row.get("成交股数", ""))
            if shares is None:
                shares = parse_optional_float(row.get("数量", ""))

            reason = row.get("reason", "") or row.get("交易原因", "") or row.get("原因", "")

            signals.append(Signal(d=d, action=action, price=price, pct=pct, amount=amount, shares=shares, reason=reason))
    signals.sort(key=lambda x: x.d)
    return signals


def resolve_trade_date(sig_date: date, trading_days: List[date]) -> date:
    i = bisect.bisect_left(trading_days, sig_date)
    if i < len(trading_days):
        return trading_days[i]
    return trading_days[-1]


def floor_to_lot(shares: float, lot_size: int) -> float:
    if lot_size <= 0:
        return max(0.0, shares)
    lots = int(shares // lot_size)
    return float(lots * lot_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate realized/unrealized return for Water strategy.")
    parser.add_argument("--prices", required=True, help="Path to daily close CSV.")
    parser.add_argument("--signals", required=True, help="Path to signal CSV.")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital in CNY.")
    parser.add_argument("--lot-size", type=int, default=100, help="A-share lot size. Use 0 to disable lot rounding.")
    parser.add_argument("--trades-out", default="交易明细.csv", help="Path to trade records CSV (Chinese headers).")
    parser.add_argument("--summary-out", default="收益汇总.csv", help="Path to summary CSV (Chinese headers).")
    args = parser.parse_args()

    bars, close_map = load_prices(Path(args.prices))
    signals = load_signals(Path(args.signals))

    trading_days = [b.d for b in bars]
    capital = float(args.capital)
    cash = capital
    position = 0.0
    avg_cost = 0.0
    realized_pnl = 0.0
    prev_trade_price: Optional[float] = None
    rows: List[TradeRow] = []

    for s in signals:
        d_exec = resolve_trade_date(s.d, trading_days)
        px = s.price if s.price is not None else close_map[d_exec]
        action = s.action
        change_since_prev = ((px - prev_trade_price) / prev_trade_price * 100.0) if prev_trade_price else None

        if action == "B":
            target_amt = s.amount if s.amount is not None else capital * (s.pct if s.pct is not None else 0.2)
            if target_amt <= 0:
                continue

            max_affordable = floor_to_lot(cash / px, args.lot_size)
            plan_shares = floor_to_lot(target_amt / px, args.lot_size)
            qty = min(plan_shares, max_affordable)
            if qty <= 0:
                continue

            amt = qty * px
            new_position = position + qty
            avg_cost = ((avg_cost * position) + amt) / new_position if new_position > 0 else 0.0
            cash -= amt
            position = new_position
            equity_after = cash + position * px

            rows.append(
                TradeRow(
                    d=d_exec,
                    action="B",
                    price=px,
                    shares=qty,
                    amount=amt,
                    cash_after=cash,
                    position_after=position,
                    pnl_realized=0.0,
                    trade_return_pct=None,
                    change_since_prev_trade_pct=change_since_prev,
                    equity_after=equity_after,
                    cumulative_return_pct=((equity_after - capital) / capital * 100.0) if capital else 0.0,
                    reason=s.reason,
                )
            )
            prev_trade_price = px

        elif action == "S":
            if position <= 0:
                continue

            if s.shares is not None and s.shares > 0:
                qty = min(position, floor_to_lot(s.shares, args.lot_size))
            elif s.pct is not None and s.pct > 0:
                qty = min(position, floor_to_lot(position * s.pct, args.lot_size))
            else:
                qty = position

            if qty <= 0:
                continue

            cost_basis = avg_cost
            amt = qty * px
            pnl = (px - cost_basis) * qty
            realized_pnl += pnl
            cash += amt
            position -= qty
            if position <= 0:
                position = 0.0
                avg_cost = 0.0
            equity_after = cash + position * px

            rows.append(
                TradeRow(
                    d=d_exec,
                    action="S",
                    price=px,
                    shares=qty,
                    amount=amt,
                    cash_after=cash,
                    position_after=position,
                    pnl_realized=pnl,
                    trade_return_pct=((px - cost_basis) / cost_basis * 100.0) if cost_basis > 0 else None,
                    change_since_prev_trade_pct=change_since_prev,
                    equity_after=equity_after,
                    cumulative_return_pct=((equity_after - capital) / capital * 100.0) if capital else 0.0,
                    reason=s.reason,
                )
            )
            prev_trade_price = px

    latest = bars[-1]
    market_value = position * latest.close
    equity = cash + market_value
    unrealized_pnl = (latest.close - avg_cost) * position if position > 0 else 0.0
    total_return = (equity - capital) / capital if capital else 0.0

    print("=== Water Strategy Return Summary ===")
    print(f"Initial Capital: {capital:,.2f} CNY")
    print(f"Latest Price Date: {latest.d.isoformat()}")
    print(f"Latest Close: {latest.close:,.3f}")
    print(f"Cash: {cash:,.2f}")
    print(f"Position Shares: {position:,.0f}")
    print(f"Market Value: {market_value:,.2f}")
    print(f"Total Equity: {equity:,.2f}")
    print(f"Realized PnL: {realized_pnl:,.2f}")
    print(f"Unrealized PnL: {unrealized_pnl:,.2f}")
    print(f"Total Return: {total_return * 100:.2f}%")

    if args.trades_out:
        out_path = Path(args.trades_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "交易日期",
                "动作",
                "成交价",
                "成交股数",
                "成交金额",
                "本次交易收益率",
                "距上次交易涨跌幅",
                "交易后现金",
                "交易后持仓股数",
                "交易后总资产",
                "交易后累计收益率",
                "已实现盈亏",
                "交易原因",
            ])
            for r in rows:
                writer.writerow([
                    r.d.isoformat(),
                    action_cn(r.action),
                    f"{r.price:.6f}",
                    f"{r.shares:.0f}",
                    f"{r.amount:.2f}",
                    "" if r.trade_return_pct is None else f"{r.trade_return_pct:.2f}%",
                    "" if r.change_since_prev_trade_pct is None else f"{r.change_since_prev_trade_pct:.2f}%",
                    f"{r.cash_after:.2f}",
                    f"{r.position_after:.0f}",
                    f"{r.equity_after:.2f}",
                    f"{r.cumulative_return_pct:.2f}%",
                    f"{r.pnl_realized:.2f}",
                    r.reason,
                ])
        print(f"Trade records saved to: {out_path.resolve()}")

    if args.summary_out:
        out_sum = Path(args.summary_out)
        out_sum.parent.mkdir(parents=True, exist_ok=True)
        with out_sum.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "初始本金",
                "估值日期",
                "最新收盘价",
                "现金",
                "持仓股数",
                "持仓市值",
                "总资产",
                "已实现盈亏",
                "未实现盈亏",
                "收益率",
            ])
            writer.writerow([
                f"{capital:.2f}",
                latest.d.isoformat(),
                f"{latest.close:.6f}",
                f"{cash:.2f}",
                f"{position:.0f}",
                f"{market_value:.2f}",
                f"{equity:.2f}",
                f"{realized_pnl:.2f}",
                f"{unrealized_pnl:.2f}",
                f"{total_return * 100:.2f}%",
            ])
        print(f"Summary saved to: {out_sum.resolve()}")


if __name__ == "__main__":
    main()
