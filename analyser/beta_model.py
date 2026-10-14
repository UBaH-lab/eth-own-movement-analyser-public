"""Бета-модель: выделяем собственное движение ETH из его общего движения."""

import logging

logger = logging.getLogger(__name__)


class BetaModel:
    """Считает бету (чувствительность ETH к BTC) по историческим доходностям
    и умеет отделять «рыночную» часть движения ETH от собственной.
    """

    def __init__(self):
        self.beta = None  # станет числом после fit()

    def fit(self, eth_returns: list[float], btc_returns: list[float]) -> float:
        """Вычисляет бету: β = Cov(ETH, BTC) / Var(BTC)."""
        n = min(len(eth_returns), len(btc_returns))
        if n < 2:
            raise ValueError("Нужно минимум 2 пары доходностей для расчёта беты")

        eth = eth_returns[-n:]
        btc = btc_returns[-n:]

        mean_eth = sum(eth) / n
        mean_btc = sum(btc) / n

        covariance = sum((e - mean_eth) * (b - mean_btc) for e, b in zip(eth, btc))
        variance_btc = sum((b - mean_btc) ** 2 for b in btc)

        if variance_btc == 0:
            raise ValueError("BTC неподвижен на выборке — бету посчитать нельзя")

        self.beta = covariance / variance_btc
        logger.info("Бета рассчитана: %.4f (по %d свечам)", self.beta, n)
        return self.beta

    def own_move(self, eth_move: float, btc_move: float) -> float:
        """Собственное движение ETH = реальное − ожидаемое (β × движение BTC)."""
        if self.beta is None:
            raise RuntimeError("Сначала нужно вызвать fit()")
        return eth_move - self.beta * btc_move
