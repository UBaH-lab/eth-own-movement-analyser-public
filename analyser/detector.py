"""Детектор собственных движений ETH в скользящем окне 60 минут.

Каждую минуту принимает текущие цены ETH и BTC, считает их минутные
доходности, выделяет собственное движение ETH (через бету) и копит его
в окне. При накопленном движении >= threshold (1%) за окно печатает сигнал.

Сумма окна обновляется за O(1): прибавляем новое значение, вычитаем
выпавшее — без пересчёта всего окна.
"""

import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class OwnMovementDetector:
    """Выделяет собственные движения ETH и следит за окном в 60 минут."""

    def __init__(self, beta_model, eth_symbol: str, btc_symbol: str,
                 window_minutes: int = 60, threshold_pct: float = 1.0):
        self.beta_model = beta_model
        self.eth_symbol = eth_symbol
        self.btc_symbol = btc_symbol
        self.window_minutes = window_minutes
        self.threshold_pct = threshold_pct

        self._window = deque()          # собственные движения последних минут
        self._window_sum = 0.0          # сумма окна — держим отдельно для O(1)
        self._last_prices = {eth_symbol: None, btc_symbol: None}
        self._minute_timestamp = None   # метка текущей минуты

    # ---------- приём данных ----------

    def on_price(self, symbol: str, price: float, timestamp_ms: int = None) -> None:
        """Запоминает последнюю цену пары (вызывается потоком на каждую сделку).

        На закрытии минуты (on_minute_close) берётся именно последняя
        известная цена — цена последней сделки в минуте.
        """
        if symbol not in self._last_prices:
            return
        self._last_prices[symbol] = price
        if timestamp_ms is not None:
            self._minute_timestamp = timestamp_ms

    def on_minute_close(self) -> dict | None:
        """Обрабатывает закрытие очередной минуты.

        Берёт последние известные цены ETH и BTC, считает их минутные
        доходности, выделяет собственное движение ETH и обновляет окно.
        Возвращает информацию о сигнале или None.
        """
        eth_price = self._last_prices[self.eth_symbol]
        btc_price = self._last_prices[self.btc_symbol]
        if eth_price is None or btc_price is None:
            return None  # ещё не видел обе пары — копим дальше

        if not hasattr(self, "_prev_prices") or self._prev_prices is None:
            # первая минута: просто запоминаем цены, движения ещё нет
            self._prev_prices = {self.eth_symbol: eth_price, self.btc_symbol: btc_price}
            return None

        eth_prev = self._prev_prices[self.eth_symbol]
        btc_prev = self._prev_prices[self.btc_symbol]

        eth_return = (eth_price - eth_prev) / eth_prev * 100
        btc_return = (btc_price - btc_prev) / btc_prev * 100

        own = self.beta_model.own_move(eth_return, btc_return)
        self._push(own)

        self._prev_prices = {self.eth_symbol: eth_price, self.btc_symbol: btc_price}

        logger.debug("минута: ETH %+.3f%%, BTC %+.3f%%, собственное %+.3f%%, окно %+.3f%%",
                     eth_return, btc_return, own, self._window_sum)

        return self.check_signal()

    # ---------- окно и сигналы ----------

    def _push(self, own_move: float) -> None:
        """Добавляет значение в окно, держит сумму актуальной за O(1)."""
        self._window.append(own_move)
        self._window_sum += own_move
        if len(self._window) > self.window_minutes:
            dropped = self._window.popleft()   # самая старая минута уезжает
            self._window_sum -= dropped

    def check_signal(self) -> dict | None:
        """Если |накопленное собственное движение| >= порога — сигнал."""
        if abs(self._window_sum) >= self.threshold_pct:
            return {
                "own_move_pct": self._window_sum,
                "threshold_pct": self.threshold_pct,
                "window_minutes": self.window_minutes,
                "message": (f"СИГНАЛ: собственное движение ETH за последние "
                            f"{self.window_minutes} мин = "
                            f"{self._window_sum:+.2f}% (порог ±{self.threshold_pct}%)"),
            }
        return None
