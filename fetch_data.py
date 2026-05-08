"""
Daily Market Pulse - 数据抓取脚本
每天由 GitHub Actions 自动运行
抓取: 标普500、纳指100、VIX、VXN、黄金、10Y美债、Fear&Greed
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta, timezone

# ============== 配置 ==============
TICKERS = {
    "SPX":  "^GSPC",   # 标普500
    "NDX":  "^NDX",    # 纳指100
    "VIX":  "^VIX",    # 标普500波动率
    "VXN":  "^VXN",    # 纳指100波动率
    "GOLD": "GC=F",    # 黄金期货
    "TNX":  "^TNX",    # 10年期美债收益率
}

CNN_FG_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# ============== 工具函数 ==============
def calc_rsi(series, period=14):
    """计算 14 日 RSI"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def vix_zone(v):
    if v < 12:  return ("极度乐观", "NORMAL", "green", 0)
    if v < 20:  return ("正常波动", "NORMAL", "green", 1)
    if v < 30:  return ("恐惧上升", "ELEVATED", "purple", 2)
    if v < 50:  return ("市场恐慌", "FEAR", "amber", 3)
    return ("极度恐慌", "PANIC", "red", 4)

def vxn_zone(v):
    if v < 15:  return ("极度乐观", "NORMAL", "green", 0)
    if v < 22:  return ("正常波动", "NORMAL", "green", 1)
    if v < 32:  return ("略升", "ELEVATED", "purple", 2)
    if v < 55:  return ("市场恐慌", "FEAR", "amber", 3)
    return ("极度恐慌", "PANIC", "red", 4)

def rsi_zone(v):
    if v < 30:  return ("超卖", "OVERSOLD", "green", 0)
    if v < 50:  return ("偏弱", "WEAK", "green", 1)
    if v < 70:  return ("中性", "NEUTRAL", "green", 2)
    if v < 80:  return ("偏强", "OVERBOUGHT", "amber", 3)
    return ("超买", "EXTREME", "red", 4)

def fg_zone(v):
    if v < 25:  return ("极度恐惧", "EXTREME FEAR", "red", 0)
    if v < 45:  return ("恐惧", "FEAR", "amber", 1)
    if v < 56:  return ("中性", "NEUTRAL", "green", 2)
    if v < 76:  return ("贪婪", "GREED", "amber", 3)
    return ("极度贪婪", "EXTREME GREED", "red", 4)

# ============== 抓取函数 ==============
def fetch_ticker(name, ticker):
    """抓取单个标的的最新行情和历史数据"""
    print(f"  → {name} ({ticker})...", end=" ")
    end = datetime.now()
    start = end - timedelta(days=400)
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=start, end=end, interval="1d", auto_adjust=False)
        if len(hist) < 2:
            print("数据不足")
            return None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        change_abs = last - prev
        change_pct = (change_abs / prev) * 100
        result = {
            "ticker": ticker,
            "last": round(last, 2),
            "prev": round(prev, 2),
            "change_abs": round(change_abs, 2),
            "change_pct": round(change_pct, 2),
            "date": str(hist.index[-1].date()),
        }
        # 计算 RSI（仅 SPX/NDX 需要）
        if name in ["SPX", "NDX"]:
            rsi = calc_rsi(hist["Close"])
            result["rsi"] = round(float(rsi.iloc[-1]), 1)
            result["rsi_change"] = round(float(rsi.iloc[-1] - rsi.iloc[-2]), 1)
        # 10年趋势线（按月采样 30 个点）
        hist10 = t.history(period="10y", interval="1mo", auto_adjust=False)
        closes = hist10["Close"].dropna().tolist()
        step = max(1, len(closes) // 30)
        result["trend"] = [round(float(x), 2) for x in closes[::step]]
        print(f"{last:.2f} ({change_pct:+.2f}%)")
        return result
    except Exception as e:
        print(f"错误: {e}")
        return None

def fetch_fear_greed():
    """抓取 CNN Fear & Greed 指数"""
    print("  → Fear & Greed...", end=" ")
    try:
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        url = f"{CNN_FG_URL}/{start_date}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        current = data["fear_and_greed"]
        score = round(float(current["score"]))
        prev_close = round(float(current.get("previous_close", current["score"])))
        rating = current.get("rating", "")
        # 历史值（取近 10 个交易日）
        hist = data["fear_and_greed_historical"]["data"][-10:]
        history = [{"date": datetime.fromtimestamp(d["x"]/1000).strftime("%Y-%m-%d"),
                    "value": round(float(d["y"]))} for d in hist]
        print(f"{score} ({rating})")
        return {
            "score": score,
            "previous_close": prev_close,
            "change": score - prev_close,
            "rating": rating,
            "history": history,
        }
    except Exception as e:
        print(f"错误: {e}")
        return None

# ============== 策略生成 ==============
def generate_strategy(data):
    """根据多信号交叉生成今日策略"""
    spx_rsi = data["SPX"]["rsi"]
    vix = data["VIX"]["last"]
    fg = data["FG"]["score"] if data.get("FG") else 50

    strats = []

    # 信号1：定投节奏
    if vix < 20 and 30 < spx_rsi < 70:
        strats.append({"top": "定投不停", "bot": "节奏继续保持"})
    elif vix < 12:
        strats.append({"top": "保持警觉", "bot": "市场过于乐观"})
    elif vix > 30:
        strats.append({"top": "加倍定投", "bot": "恐慌出现机会"})
    else:
        strats.append({"top": "定投不停", "bot": "节奏继续保持"})

    # 信号2：仓位提醒
    if spx_rsi > 70:
        strats.append({"top": "谨慎追高", "bot": "RSI 已偏强"})
    elif spx_rsi < 30:
        strats.append({"top": "重点加仓", "bot": "RSI 已超卖"})
    elif fg > 75:
        strats.append({"top": "适度止盈", "bot": "贪婪区间"})
    elif fg < 25:
        strats.append({"top": "勇敢买入", "bot": "极度恐惧"})
    else:
        strats.append({"top": "保持均衡", "bot": "信号未明朗"})

    # 信号3：备弹建议
    if spx_rsi > 70 and fg > 60:
        strats.append({"top": "留好子弹", "bot": "等更深回调点"})
    elif spx_rsi < 40 or fg < 30:
        strats.append({"top": "动用储备", "bot": "良机难得"})
    elif vix > 25:
        strats.append({"top": "分批买入", "bot": "波动加大"})
    else:
        strats.append({"top": "持续观察", "bot": "等待信号"})

    return strats

# ============== 主流程 ==============
def main():
    print(f"\n{'='*50}\n抓取时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n{'='*50}\n")

    data = {}
    for name, ticker in TICKERS.items():
        result = fetch_ticker(name, ticker)
        if result:
            data[name] = result

    fg = fetch_fear_greed()
    if fg:
        data["FG"] = fg

    # 生成策略
    if "SPX" in data and "VIX" in data:
        data["strategy"] = generate_strategy(data)

    # 加入 zone 分类信息
    if "VIX" in data:
        z = vix_zone(data["VIX"]["last"])
        data["VIX"]["zone"] = {"label_cn": z[0], "label_en": z[1], "color": z[2], "idx": z[3]}
    if "VXN" in data:
        z = vxn_zone(data["VXN"]["last"])
        data["VXN"]["zone"] = {"label_cn": z[0], "label_en": z[1], "color": z[2], "idx": z[3]}
    if "SPX" in data and "rsi" in data["SPX"]:
        z = rsi_zone(data["SPX"]["rsi"])
        data["SPX"]["rsi_zone"] = {"label_cn": z[0], "label_en": z[1], "color": z[2], "idx": z[3]}
    if "NDX" in data and "rsi" in data["NDX"]:
        z = rsi_zone(data["NDX"]["rsi"])
        data["NDX"]["rsi_zone"] = {"label_cn": z[0], "label_en": z[1], "color": z[2], "idx": z[3]}
    if "FG" in data:
        z = fg_zone(data["FG"]["score"])
        data["FG"]["zone"] = {"label_cn": z[0], "label_en": z[1], "color": z[2], "idx": z[3]}

    # 时间戳（北美东部时间）
    now_et = datetime.now(timezone.utc) - timedelta(hours=4)  # EDT
    weekday_cn = ["周一","周二","周三","周四","周五","周六","周日"][now_et.weekday()]
    data["meta"] = {
        "updated_at": now_et.strftime("%Y-%m-%d %H:%M ET"),
        "date_str": f"{now_et.year} · {now_et.month:02d} · {now_et.day:02d}",
        "weekday": weekday_cn,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存至 data.json")
    return data

if __name__ == "__main__":
    main()
