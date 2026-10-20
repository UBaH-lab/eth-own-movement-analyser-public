"""Дипломный проект ТА7: анализ собственных движений фьючерса ETHUSDT."""

import asyncio
import logging
from datetime import datetime, timezone

from analyser.beta_model import BetaModel
from analyser.detector import OwnMovementDetector
from analyser.historical_data import aligned_returns
from analyser.market_data import MarketDataStream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("main")

ETH = "ETH-USDT"
BTC = "BTC-USDT"


async def main() -> None:
    logger.info("Считаю бету по истории (500 минутных свечей)...")
    eth_returns, btc_returns = aligned_returns(interval="1m", limit=500)
    model = BetaModel()
    model.fit(eth_returns, btc_returns)
    logger.info("Бета = %.4f. Слежу за рынком.", model.beta)

    detector = OwnMovementDetector(
        model, ETH, BTC, window_minutes=60, threshold_pct=1.0,
    )

    def on_trade(symbol: str, price: float) -> None:
        # обычная функция: поток не обязан знать, async колбэк или нет
        detector.on_price(symbol, price)

    stream = MarketDataStream([ETH, BTC], on_trade)

    async def minute_ticker() -> None:
        """Раз в минуту закрывает минуту в детекторе."""
        while True:
            await asyncio.sleep(60 - datetime.now(timezone.utc).second)
            signal = detector.on_minute_close()
            if signal:
                print("=" * 60)
                print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {signal['message']}")
                print("=" * 60)
                logger.info("Сигнал зафиксирован, продолжаю слежение")

    ticker_task = asyncio.create_task(minute_ticker())
    try:
        await stream.run()
    finally:
        ticker_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановлено пользователем")
