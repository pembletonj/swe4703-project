import random

from numpy import ndarray

from market import Bid

def gen_schedule_by_prices_and_mean(prices: ndarray[float], mean: float) -> ndarray[float]:
    return prices * mean / prices.mean()

class Home:
    def __init__(self, schedule: list[float], randomness: float):
        self.schedule = schedule
        self.randomness = randomness
    
    def make_bid(self, t, grid_price):
        offset = self.schedule[t] * self.randomness * random.uniform(-1.0, 1.0)
        amount = self.schedule[t] + offset

        return Bid(
            price_per_kwh=grid_price,
            amount=amount,
            discharge=False,
            creator=self,
        )

    def collect_bid_results(self, t, bid: Bid):
        pass

    def post_bid(self, t, price):
        return {}