from market import Bid

class RecordingWrapper:
    def __init__(self, der):
        self.der = der
        self.post_bid_stats = {}
    
    def make_bid(self, t, grid_price) -> Bid:
        bid: Bid = self.der.make_bid(t, grid_price)
        if bid is not None:
            bid.creator = self
        self.post_bid_stats = {
            'cost': 0.0,
        }
        return bid

    def collect_bid_results(self, t, bid: Bid):
        # print(f'==> Bid got t={t}, p={bid.price_per_kwh}, a={bid.amount}')
        if bid.discharge:
            self.post_bid_stats['cost'] = bid.amount * bid.price_per_kwh * -1
        else:
            self.post_bid_stats['cost'] = bid.amount * bid.price_per_kwh
        self.post_bid_stats['granted_amount'] = bid.amount
        return self.der.collect_bid_results(t, bid)
    
    def post_bid(self, t: int, price: float) -> dict:
        der_stats: dict = self.der.post_bid(t, price)
        self.post_bid_stats = self.post_bid_stats | der_stats
        return self.post_bid_stats