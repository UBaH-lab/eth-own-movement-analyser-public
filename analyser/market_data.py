"""Приём цен фьючерсов ETH-USDT и BTC-USDT с WebSocket BingX в реальном времени."""

import asyncio
import gzip
import json
import logging

import websockets

logger = logging.getLogger(__name__)

BINGX_WS_URL = "wss://open-api-ws.bingx.com/market"


class MarketDataStream:
    """Слушает сделки по нескольким парам на одном WebSocket-соединении.

    Каждый трейд передаётся в callback: callback(symbol, price).
    Это позволяет модулю не знать, что дальше делать с ценой, —
    анализатор подключим отдельно (принцип разделения ответственности).
    """

    def __init__(self, symbols: list[str], on_trade):
        """
        symbols  — список пар, например ["ETH-USDT", "BTC-USDT"]
        on_trade — функция вида def on_trade(symbol: str, price: float)
        """
        self.symbols = symbols
        self.on_trade = on_trade
        self._prices: dict[str, float] = {}   # последние цены по парам
        self._ws = None
        self._running = False

    @property
    def last_prices(self) -> dict[str, float]:
        """Снимок последних цен: {"ETH-USDT": 3122.45, "BTC-USDT": 68234.1}"""
        return dict(self._prices)

    def _subscription(self, symbol: str) -> dict:
        """Сообщение-подписка на канал сделок по конкретной паре."""
        return {
            "id": f"sub-{symbol}",
            "reqType": "sub",
            "dataType": f"{symbol}@trade",
        }

    @staticmethod
    def _unpack(message) -> dict | None:
        """BingX шлёт gzip-сжатые данные: распаковываем и парсим JSON."""
        if isinstance(message, bytes):
            # служебный пульс биржи — на него надо ответить, иначе разорвёт связь
            if b"Ping" in message:
                return {"ping": True}
            message = gzip.decompress(message)
        text = message.decode("utf-8")
        return json.loads(text)

    async def run(self) -> None:
        """Бесконечный цикл: подключение, подписки, приём сделок."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(BINGX_WS_URL) as ws:
                    self._ws = ws
                    for symbol in self.symbols:
                        await ws.send(json.dumps(self._subscription(symbol)))
                        logger.info("Подписался на %s", symbol)
                    async for message in ws:
                        data = self._unpack(message)
                        if data is None:
                            continue
                        if data.get("ping"):
                            await ws.send("Pong")
                            continue
                        trade = data.get("data")
                        if not isinstance(trade, dict):
                            continue
                        symbol = trade.get("s")        # s = symbol в ответе
                        price = trade.get("p")         # p = price
                        if symbol in self.symbols and price:
                            price = float(price)
                            self._prices[symbol] = price
                            self.on_trade(symbol, price)
            except websockets.ConnectionClosed as error:
                logger.warning("Соединение закрыто (%s), переподключаюсь...", error)
                await asyncio.sleep(3)   # подождать 3 секунды и заново
            except Exception as error:
                logger.error("Ошибка потока: %s, переподключаюсь через 3 с...", error)
                await asyncio.sleep(3)

    def stop(self) -> None:
        """Останавливает поток снаружи."""
        self._running = False
        
