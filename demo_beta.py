"""Проверка бета-модели на реальной истории BingX."""

import logging

from analyser.beta_model import BetaModel
from analyser.historical_data import aligned_returns

logging.basicConfig(level=logging.INFO)

eth, btc = aligned_returns(interval="1m", limit=500)

model = BetaModel()
beta = model.fit(eth, btc)
print(f"Бета ETH к BTC: {beta:.4f}")

own = model.own_move(eth_move=1.4, btc_move=1.0)
print(f"Если BTC +1.0% и ETH +1.4%: собственное движение ETH = {own:+.2f}%")
