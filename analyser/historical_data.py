"""Загрузка исторических свечей ETH-USDT и BTC-USDT через CCXT (биржа BingX).

CCXT — стандартная библиотека для работы с биржами: единый интерфейс
к свечам/котировкам 100+ бирж, включая фьючерсы BingX.
"""

import logging

import ccxt

logger = logging.getLogger(__name__)

exchange = ccxt.bingx()

# формат пары для фьючерсов CCXT: ETH/USDT:USDT (бессрочный контракт)
SWAP_ETH = "ETH/USDT:USDT"
SWAP_BTC = "BTC/USDT:USDT"


def fetch_klines(symbol: str, interval: str = "1m", limit: int = 500) -> list[dict]:
    """Скачивает последние `limit` свечей по паре `symbol`.

    Возвращает [{"timestamp": <мс>, "close": <цена>}, ...]
    """
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
    candles = [{"timestamp": row[0], "close": float(row[4])} for row in ohlcv]
    logger.info("%s: получено %d свечей", symbol, len(candles))
    return candles


def returns_from_closes(closes: list[float]) -> list[float]:
    """Превращает цены закрытия в проценты изменений (доходности).

    [100, 102, 101] -> [2.0, -0.98]
    """
    result = []
    for previous, current in zip(closes, closes[1:]):
        result.append((current - previous) / previous * 100)
    return result


def aligned_returns(interval: str = "1m", limit: int = 500) -> tuple[list[float], list[float]]:
    """Возвращает пары доходностей ETH и BTC, совпадающие по времени.

    Доходность ETH за минуту N сравнивается с доходностью BTC за ту же
    минуту — без этого бета теряет смысл.
    """
    eth_candles = fetch_klines(SWAP_ETH, interval, limit)
    btc_candles = fetch_klines(SWAP_BTC, interval, limit)

    # выравниваем по меткам времени
    btc_by_time = {c["timestamp"]: c["close"] for c in btc_candles}
    times = [c["timestamp"] for c in eth_candles if c["timestamp"] in btc_by_time]
    eth_closes = [c["close"] for c in eth_candles if c["timestamp"] in btc_by_time]
    btc_closes = [btc_by_time[t] for t in times]

    return returns_from_closes(eth_closes), returns_from_closes(btc_closes)
