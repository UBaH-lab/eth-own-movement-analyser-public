"""Тесты обработки истории: доходности и выравнивание — без сети."""

from analyser import historical_data as hd


def test_returns_from_closes():
    """[100, 102, 101] -> [+2.0%, -0.98%] — ручной расчёт."""
    result = hd.returns_from_closes([100, 102, 101])
    assert result[0] == 102 / 100 * 100 - 100  # +2.0
    assert abs(result[1] - (101 - 102) / 102 * 100) < 1e-9  # -0.980...
    assert len(result) == 2


def test_returns_empty():
    assert hd.returns_from_closes([]) == []
    assert hd.returns_from_closes([100]) == []


def test_fetch_klines_parses_ohlcv(monkeypatch):
    """fetch_klines превращает строки CCXT [time, o, h, l, close, v] в наши dict."""
    fake_rows = [
        [1700000000000, "100", "101", "99", "100.5", "10"],
        [1700000060000, "100.5", "102", "100", "101.0", "5"],
    ]
    monkeypatch.setattr(hd.exchange, "fetch_ohlcv", lambda *a, **k: fake_rows)
    candles = hd.fetch_klines("ETH/USDT:USDT")
    assert candles == [
        {"timestamp": 1700000000000, "close": 100.5},
        {"timestamp": 1700000060000, "close": 101.0},
    ]


def test_aligned_returns_syncs_by_time(monkeypatch):
    """Свечи с разными наборами минут выравниваются по времени."""
    eth = [
        {"timestamp": 1, "close": 100},
        {"timestamp": 2, "close": 101},
        {"timestamp": 3, "close": 102},   # минуты 3 нет у BTC — вылетит
    ]
    btc = [
        {"timestamp": 1, "close": 50},
        {"timestamp": 2, "close": 50},
        {"timestamp": 4, "close": 51},    # минуты 4 нет у ETH — вылетит
    ]
    monkeypatch.setattr(hd, "fetch_klines", lambda symbol, i, l: eth if "ETH" in symbol else btc)
    eth_r, btc_r = hd.aligned_returns()
    assert len(eth_r) == 1 and len(btc_r) == 1  # осталась одна общая минута
    assert eth_r[0] == 1.0                     # 100 -> 101 = +1%
    assert btc_r[0] == 0.0                     # 50 -> 50 = 0%
