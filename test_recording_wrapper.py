import pytest

from market import Bid
from recording_wrapper import RecordingWrapper

class MockDER:
    do_bid = True
    discharge = False
    multiplier = 3.0

    def make_bid(self, t, grid_price) -> Bid:
        if self.do_bid:
            return Bid(
                price_per_kwh=self.multiplier * (t+1),
                amount=self.multiplier * (t+2),
                discharge=self.discharge,
                creator=self,
            )
        return None

    def collect_bid_results(self, t, bid: Bid):
        pass

    def post_bid(self, t: int, price: float) -> dict:
        return {
            'multiplier': self.multiplier,
        }

@pytest.fixture
def rw():
    return RecordingWrapper(MockDER())

def test_with_charge(rw: RecordingWrapper):
    bid = rw.make_bid(0, None)
    assert bid.creator == rw
    bid.price_per_kwh = 2.0
    bid.amount = 1.2
    rw.collect_bid_results(0, bid)
    assert rw.post_bid(0, None) == {
        'multiplier': 3.0,
        'cost': 2.4,
        'granted_amount': 1.2,
    }

def test_with_discharge(rw: RecordingWrapper):
    rw.der.discharge = True
    bid = rw.make_bid(0, None)
    assert bid.creator == rw
    bid.price_per_kwh = 2.0
    bid.amount = 1.2
    rw.collect_bid_results(0, bid)
    assert rw.post_bid(0, None) == {
        'multiplier': 3.0,
        'cost': -2.4,
        'granted_amount': 1.2,
    }

def test_no_bid(rw: RecordingWrapper):
    rw.der.do_bid = False
    assert rw.make_bid(0, None) == None
    assert rw.post_bid(0, None) == {
        'multiplier': 3.0,
        'cost': 0.0,
    }