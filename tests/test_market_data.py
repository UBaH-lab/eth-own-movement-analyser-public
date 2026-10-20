"""Тесты распаковки сообщений BingX: gzip и Ping — без подключения."""

import gzip
import json

from analyser.market_data import MarketDataStream


def test_unpack_ping():
    assert MarketDataStream._unpack(b"Ping") == {"ping": True}


def test_unpack_gzip_trade():
    """BingX шлёт сделки gzip-сжатыми — проверяем полный путь bytes → dict."""
    trade = {"s": "ETH-USDT", "p": "3122.45"}
    compressed = gzip.compress(json.dumps(trade).encode("utf-8"))
    assert MarketDataStream._unpack(compressed) == trade


def test_subscription_message():
    stream = MarketDataStream(["ETH-USDT"], lambda s, p: None)
    msg = stream._subscription("ETH-USDT")
    assert msg["dataType"] == "ETH-USDT@trade"
    assert msg["reqType"] == "sub"


def test_last_prices_snapshot():
    """Свойство last_prices возвращает словарь последних цен."""
    stream = MarketDataStream(["ETH-USDT"], lambda s, p: None)
    assert stream.last_prices == {}
    stream._prices["ETH-USDT"] = 3122.45
    assert stream.last_prices == {"ETH-USDT": 3122.45}


def test_unpack_two_gzip_messages():
    """Распаковка устойчива: два разных сообщения подряд."""
    for payload in ({"s": "BTC-USDT", "p": "68000"}, {"code": 0}):
        compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
        assert MarketDataStream._unpack(compressed) == payload


def test_init_stores_symbols():
    stream = MarketDataStream(["ETH-USDT", "BTC-USDT"], lambda s, p: None)
    assert stream.symbols == ["ETH-USDT", "BTC-USDT"]
