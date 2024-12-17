import pytest
import numpy as np

from home import Home, gen_schedule_by_prices_and_mean

@pytest.fixture
def home():
    weekday_winter = np.array([7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 15.8, 15.8, 15.8, 15.8, 12.2,
                               12.2, 12.2, 12.2, 12.2, 12.2, 15.8, 15.8, 7.6, 7.6, 7.6, 7.6, 7.6])
    home_schedule = gen_schedule_by_prices_and_mean(weekday_winter, 2.0)
    return Home(
        schedule=home_schedule,
        randomness=0.1,
    )

def test_make_bid(home: Home):
    bid = home.make_bid(0, 100.0)
    assert bid.creator == home
    assert bid.price_per_kwh == 100.0
    assert not bid.discharge