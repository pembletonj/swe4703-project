import numpy as np
import pytest

from grid import TimeOfUseGrid

@pytest.fixture
def grid():
    # Source: https://www.hydroone.com/rates-and-billing/rates-and-charges/electricity-pricing-and-costs
    weekday_winter = np.array([7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 15.8, 15.8, 15.8, 15.8, 12.2,
                               12.2, 12.2, 12.2, 12.2, 12.2, 15.8, 15.8, 7.6, 7.6, 7.6, 7.6, 7.6])
    return TimeOfUseGrid(weekday_winter)

def test_make_bid(grid: TimeOfUseGrid):
    for t in range(24):
        bid = grid.make_bid(t, None)
        assert bid.price_per_kwh == grid.prices[t]
        assert bid.amount == None
        assert bid.discharge == True
        assert bid.creator == grid

def test_post_bid(grid: TimeOfUseGrid):
    assert grid.post_bid(0, grid.prices[0]) == {}