"""Тесты бета-модели: математика на выдуманных данных, без сети."""

import pytest

from analyser.beta_model import BetaModel


def test_fit_perfect_relation():
    """Если ETH всегда движется ровно вдвое сильнее BTC, бета = 2."""
    btc = [1.0, 2.0, -1.0, 0.5, -0.5, 1.5, 0.0, 1.0]
    eth = [x * 2 for x in btc]
    model = BetaModel()
    beta = model.fit(eth, btc)
    assert beta == pytest.approx(2.0)


def test_fit_no_relation():
    """Если ETH никак не связан с BTC (зеркалит его), бета около -1... или 0.

    Берём независимые ряды с нулевой ковариацией: бета должна быть ~0.
    """
    btc = [1.0, 1.0, -1.0, -1.0]
    eth = [1.0, -1.0, 1.0, -1.0]  # ковариация с btc = 0
    model = BetaModel()
    beta = model.fit(eth, btc)
    assert beta == pytest.approx(0.0, abs=0.01)


def test_own_move_subtracts_beta():
    """Собственное движение = реальное − β·BTC (проверка на числах)."""
    model = BetaModel()
    model.beta = 1.25
    assert model.own_move(eth_move=1.4, btc_move=1.0) == pytest.approx(0.15)


def test_own_move_without_fit_fails():
    """own_move до fit() должен упасть с понятной ошибкой."""
    model = BetaModel()
    with pytest.raises(RuntimeError):
        model.own_move(1.0, 1.0)


def test_fit_needs_two_points():
    """Одной точки мало — ждём ValueError."""
    model = BetaModel()
    with pytest.raises(ValueError):
        model.fit([1.0], [1.0])


def test_fit_zero_variance_fails():
    """Если BTC неподвижен, бету считать нельзя — ValueError."""
    model = BetaModel()
    with pytest.raises(ValueError):
        model.fit([1.0, 2.0, 3.0], [0.0, 0.0, 0.0])
