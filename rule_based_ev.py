from ev import EV, EVSpec
from market import Bid

class RuleBasedEV(EV):
    def __init__(self, spec: EVSpec, mdr: list[float], driving_schedule: list[float], max_charge_price: float, min_discharge_price: float):
        super().__init__(spec, mdr, driving_schedule)
        self.min_discharge_price = min_discharge_price
        self.max_charge_price = max_charge_price
        self.last_action = None

    def make_bid(self, t, grid_price):
        if self.driving_schedule[t] != 0.0:
            self.last_action = 'drive'
            # Not plugged in, can't bid.
            return None
        
        next = (t + 1) % 24
        min_charge_amount = self.minimum_charge_amount(t)
        
        if grid_price < self.max_charge_price:
            # We want to charge now.
            self.last_action = 'voluntary_charge'
            return Bid(
                price_per_kwh=grid_price,
                amount=min(self.spec.charge_rate_max, self.left_to_charge()),
                discharge=False,
                creator=self,
            )
        elif min_charge_amount > 0.0:
            # The EV needs to meet its charging goals.
            self.last_action = 'required_charge'
            return Bid(
                price_per_kwh=grid_price,
                amount=min(self.spec.charge_rate_max, min_charge_amount),
                discharge=False,
                creator=self,
            )
        elif grid_price > self.min_discharge_price:
            self.last_action = 'discharge'
            return Bid(
                price_per_kwh=0.0,
                amount=min(self.spec.discharge_rate_max, self.current_energy - self.mdr[next]),
                discharge=True,
                creator=self,
            )
    
    def collect_bid_results(self, t, bid: Bid):
        if bid.discharge:
            self.determine_energy_transfer(1, "discharge", amount=bid.amount)
        else:
            self.determine_energy_transfer(1, "charge", amount=bid.amount)

    def post_bid(self, t, price):
        self.determine_energy_transfer(1, 'discharge', amount=self.driving_schedule[t])
        return self.get_current_stats(t) | {
            'last_action': self.last_action,
        }