from market import Bid

class TimeOfUseGrid:
    def __init__(self, prices):
        self.prices = prices
    
    def make_bid(self, t, grid_price) -> Bid:
        return Bid(
            price_per_kwh=self.prices[t],
            amount=None,
            discharge=True,
            creator=self,
        )

    def collect_bid_results(self, t, bid: Bid):
        pass

    def post_bid(self, t: int, price: float) -> dict:
        return {}