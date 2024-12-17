import pytest

from ev import EVSpec
from rule_based_ev import RuleBasedEV

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

    return RuleBasedEV(
        spec=ev_spec,
        mdr=mdr,
        driving_schedule=driving_schedule,
        max_charge_price=50.0,
        min_discharge_price=100.0,
    )

def test_no_bid(ev: RuleBasedEV):
    bid = ev.make_bid(0, 75.0)
    assert bid is None
    stats = ev.post_bid(0, None)
    assert stats['last_action'] is None

def test_discharge_bid(ev: RuleBasedEV):
    bid = ev.make_bid(0, 110.0)
    assert bid.discharge
    stats = ev.post_bid(0, None)
    assert stats['last_action'] == 'discharge'

def test_charge_bid(ev: RuleBasedEV):
    bid = ev.make_bid(0, 40.0)
    assert not bid.discharge
    stats = ev.post_bid(0, None)
    assert stats['last_action'] == 'voluntary_charge'