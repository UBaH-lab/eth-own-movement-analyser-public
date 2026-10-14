"""Демонстрация: печатаем сделки ETH и BTC в реальном времени."""

import asyncio
import logging

from analyser.market_data import MarketDataStream

logging.basicConfig(level=logging.INFO)


def print_trade(symbol: str, price: float) -> None:
    print(f"{symbol}: {price}")


async def demo() -> None:
    stream = MarketDataStream(
        symbols=["ETH-USDT", "BTC-USDT"],
        on_trade=print_trade,
    )
    await stream.run()


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nОстановлено вручную.")
