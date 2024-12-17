import pytest
import numpy as np

from ev import EVSpec
from optimized_ev import OptimizedEV

@pytest.fixture
def ev():
    ev_spec = EVSpec(
        capacity=40, # kWh
        charge_rate_max=10, # kW
        discharge_rate_max=10, # kW
        initial_energy=20.0, # kWh
        operating_range=(0.2, 0.8), # Percent
    )

    driving_schedule = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0,
                        4.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    mdr = [6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 15.0, 20.0, 20.0, 15.0, 15.0, 15.0,
           15.0, 15.0, 15.0, 15.0, 15.0, 20.0, 15.0, 15.0, 15.0, 10.0, 10.0, 10.0]
    weekday_winter = np.array([7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 15.8, 15.8, 15.8, 15.8, 12.2,
                               12.2, 12.2, 12.2, 12.2, 12.2, 15.8, 15.8, 7.6, 7.6, 7.6, 7.6, 7.6])

    return OptimizedEV(
        spec=ev_spec,
        driving_schedule=driving_schedule,
        mdr=mdr,
        history=weekday_winter.copy(),
    )

# Not a lot we can test here since it's hard to predict what the algorithm will do.
def test_make_bid(ev: OptimizedEV):
    bid = ev.make_bid(0, None)
    if bid.discharge:
        assert bid.amount <= ev.spec.discharge_rate_max
    else:
        assert bid.amount <= ev.spec.charge_rate_max