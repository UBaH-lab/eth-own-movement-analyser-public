"""Проверка: получаем цены ETHUSDT с фьючерсного WebSocket BingX в реальном времени."""

import asyncio
import gzip
import json
import websockets

URL = "wss://open-api-ws.bingx.com/market"

SUBSCRIBE_ETH = {
    "id": "sub-eth-trade",
    "reqType": "sub",
    "dataType": "ETH-USDT@trade",   # каждая сделка по фьючерсу ETH-USDT
}


def unpack(message) -> dict | None:
    """BingX шлёт данные gzip-сжатыми: распаковываем и превращаем в JSON."""
    raw = message
    if isinstance(raw, bytes):
        raw = gzip.decompress(raw)          # распаковали gzip
    text = raw.decode("utf-8")
    return json.loads(text)


async def listen() -> None:
    """Подключается к WebSocket и печатает входящие цены ETH."""
    async with websockets.connect(URL) as ws:
        await ws.send(json.dumps(SUBSCRIBE_ETH))
        print("Подключился, ждём сделки ETH...")
        async for message in ws:
            # BingX проверяет, живой ли клиент: присылает "Ping", ждём ответ "Pong"
            if isinstance(message, bytes):
                if b"Ping" in message:
                    await ws.send("Pong")
                    continue
            data = unpack(message)
            trade = data.get("data")
            if isinstance(trade, dict):
                price = trade.get("p")  # p = price
                if price:
                    print(f"ETH-USDT: {price}")
            else:
                # служебные ответы (успех подписки и т.п.) — покажем, чтобы видеть всё
                print(data)


async def main() -> None:
    await listen()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено вручную.")
