import numpy as np
from pulp import LpProblem, lpSum, LpVariable, PULP_CBC_CMD

from ev import EV, EVSpec
from market import Bid

class OptimizedEV(EV):
    def __init__(self,
                 spec: EVSpec,
                 mdr: list[float],
                 driving_schedule: list[float],
                 history: list[int]):
        super().__init__(spec, mdr, driving_schedule)
        self.schedule = np.zeros(24)
        self.history = history
    
    def update_model(self):
        model = LpProblem('ChargeSchedule')

        # Adding charge rate (c) and current energy (E) variables
        charge_vars = []
        for i in range(24):
            charge_vars.append(LpVariable(f'c_{i}', -10, 10))
        energy_vars = []
        for i in range(25):
            energy_vars.append(LpVariable(f'E_{i}', self.min_operating_capacity(), self.max_operating_capacity()))
        
        # Adding an objective
        model += lpSum(charge_vars[i] * self.history[i] for i in range(24)) # TODO is this minimizing or maximizing?

        # Start condition
        model += (energy_vars[0] == self.current_energy, 'start_energy')

        # MDR conditions
        for i in range(24):
            model += (energy_vars[i+1] >= self.mdr[i], f'mdr_{i}')

        # Constraints on energy logic
        for i in range(24):
            if self.driving_schedule[i] == 0.0:
                # Car is plugged in, let it charge/discharge.
                model += (energy_vars[i+1] == energy_vars[i] + charge_vars[i], f'energy_logic_{i}')
            else:
                # Car is not plugged in, simulate driving.
                model += (energy_vars[i+1] == energy_vars[i] - self.driving_schedule[i], f'energy_logic_{i}')
                model += (charge_vars[i] == 0)

        model.solve(PULP_CBC_CMD(msg=0)) # Argument is to disable logging to stdout.
        solution = {v.name: v.value() for v in model.variables()}
        self.schedule = [solution[f'c_{i}'] for i in range(24)]

    def make_bid(self, t, grid_price):
        if t == 0:
            self.update_model()

        next = (t + 1) % 24
        min_charge_amount = self.minimum_charge_amount(t)
        
        if self.schedule[t] > 0.0:
            # Charging
            # We bid at grid price because we want to charge regardless of the price.
            # The bid gets clamped up so that it always hits MDR. Should we clamp up to E[t+1] instead?
            # Notably not E[next] because an E[25] exists.
            return Bid(
                price_per_kwh=grid_price,
                amount=min(self.schedule[t], self.spec.charge_rate_max, self.left_to_charge()),
                discharge=False,
                creator=self,
            )
        elif min_charge_amount > 0.0:
            # The EV needs to meet its charging goals.
            return Bid(
                price_per_kwh=grid_price,
                amount=min(self.spec.charge_rate_max, min_charge_amount),
                discharge=False,
                creator=self,
            )
        elif self.schedule[t] < 0.0:
            # Discharging
            # We bid at 0 because we want to discharge regardless of the price.
            # Would it be better to bid at some minimum? Like 80% of the on-peak rate? Or some percentile of the history?
            return Bid(
                price_per_kwh=0.0,
                amount=min(self.schedule[t] * -1, self.current_energy - self.mdr[next]),
                discharge=True,
                creator=self,
            )
        return None
    
    def collect_bid_results(self, t, bid: Bid):
        if bid.discharge:
            self.determine_energy_transfer(1, "discharge", amount=bid.amount)
        else:
            self.determine_energy_transfer(1, "charge", amount=bid.amount)

    def post_bid(self, t, price):
        old_hist = self.history[t]
        self.history[t] = (self.history[t] + price) / 2
        self.determine_energy_transfer(1, 'discharge', amount=self.driving_schedule[t])
        stats = {
            'history': old_hist,
            'schedule': self.schedule[t]
        }
        return stats | self.get_current_stats(t)