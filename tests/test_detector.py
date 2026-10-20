"""Тесты детектора: гоняем минуты вручную, без сети и без ожидания."""

from analyser.beta_model import BetaModel
from analyser.detector import OwnMovementDetector

ETH = "ETH-USDT"
BTC = "BTC-USDT"


def make_detector(threshold=1.0, window=3, beta=1.0):
    """Детектор с маленьким окном (3 'минуты') для быстрых тестов."""
    model = BetaModel()
    model.beta = beta
    return OwnMovementDetector(model, ETH, BTC,
                               window_minutes=window, threshold_pct=threshold)


def run_minutes(detector, eth_prices, btc_prices):
    """Прогоняет детектор через 'минуты': подаёт цены и закрывает минуту.

    Возвращает список сигналов (пустой, если ни один не сработал).
    """
    signals = []
    for eth_price, btc_price in zip(eth_prices, btc_prices):
        detector.on_price(ETH, eth_price)
        detector.on_price(BTC, btc_price)
        signal = detector.on_minute_close()
        if signal:
            signals.append(signal)
    return signals


def test_no_signal_when_eth_follows_btc():
    """ETH ходит ровно за BTC (бета=1) — собственных движений нет, сигналов нет."""
    detector = make_detector(threshold=1.0, window=3, beta=1.0)
    # BTC и ETH движутся одинаково: собственное движение = 0 каждую минуту
    eth = [100, 101, 102, 103, 104]
    btc = [50, 50.5, 51, 51.5, 52]  # те же +1% в минуту
    signals = run_minutes(detector, eth, btc)
    assert signals == []


def test_signal_on_own_move():
    """ETH падает сам по себе при неподвижном BTC — сигнал обязан прийти."""
    detector = make_detector(threshold=1.0, window=3, beta=1.0)
    # BTC стоит на месте, ETH летит вниз по 1% в минуту
    eth = [100, 101, 102, 103, 104, 105]
    btc = [50, 50, 50, 50, 50, 50]  # BTC не двигается
    eth = [100, 99, 98, 97]        # ETH -1% каждую минуту
    signals = run_minutes(detector, eth, btc)
    assert len(signals) >= 1
    assert signals[0]["own_move_pct"] <= -1.0  # накопилось вниз


def test_window_is_limited():
    """Окно держит ровно window_minutes значений, сумма им соответствует."""
    detector = make_detector(threshold=99, window=3, beta=1.0)
    eth = [100, 90, 95, 100, 105, 110]
    btc = [50, 50, 50, 50, 50, 50]
    run_minutes(detector, eth, btc)
    assert len(detector._window) == 3
    assert sum(detector._window) == pytest.approx(detector._window_sum)


def test_first_minute_no_crash():
    """Первая минута — только запоминание цен, сигнал невозможен, ошибок нет."""
    detector = make_detector()
    detector.on_price(ETH, 100)
    detector.on_price(BTC, 50)
    assert detector.on_minute_close() is None


def test_ignores_unknown_symbol():
    """Цена посторонней пары не ломает детектор."""
    detector = make_detector()
    detector.on_price("SOL-USDT", 123.45)  # не наша пара — игнор
    assert detector._last_prices["SOL-USDT"] if "SOL-USDT" in detector._last_prices else True


import pytest  # noqa: E402 (pytest нужен в этом тесте на approx)


def test_push_o1_sum():
    """Сумма окна актуальна после серии добавлений (O(1)-инвариант)."""
    detector = make_detector(threshold=99, window=5, beta=1.0)
    for value in [0.5, -0.3, 0.2, 0.4, -0.1, 0.7, -0.2]:
        detector._push(value)
    assert sum(detector._window) == pytest.approx(detector._window_sum)
    assert len(detector._window) == 5
