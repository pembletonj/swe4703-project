# Contains characteristics defining an EV's hardware.
class EVSpec:
    def __init__(self,
                 capacity: float,
                 charge_rate_max: float,
                 discharge_rate_max: float,
                 initial_energy: float,
                 operating_range: tuple[float, float]):
        self.capacity = capacity # kWh
        self.charge_rate_max = charge_rate_max # kW
        self.discharge_rate_max = discharge_rate_max # kW
        self.initial_energy = initial_energy # kWh
        self.operating_range = operating_range # Percent

# Defines an EV with all common functionality between different EV DER algorithms.
class EV:
    def __init__(self,
                 spec: EVSpec,
                 mdr: list[float],
                 driving_schedule: list[float]):
        self.spec = spec
        self.current_energy = spec.initial_energy
        self.mdr = mdr
        self.driving_schedule = driving_schedule

    def max_operating_capacity(self, range=None):
        if range is None:
             range = self.spec.operating_range
        else:
             range = (max(range[0], self.spec.operating_range[0]), min(range[1], self.spec.operating_range[1]))
        return self.spec.capacity * range[1]

    def min_operating_capacity(self, range=None):
        if range is None:
             range = self.spec.operating_range
        else:
             range = (max(range[0], self.spec.operating_range[0]), min(range[1], self.spec.operating_range[1]))
        return self.spec.capacity * range[0]
    
    def left_to_charge(self, range=None):
        return max(0, self.max_operating_capacity(range) - self.current_energy)

    def minimum_charge_amount(self, t: int) -> float:
        skips = 0
        lost_to_driving = 0.0
        min_charge_amount = 0.0
        for i in range(1, 4):
            target = (t + i) % 24
            if self.driving_schedule[target] != 0.0:
                # Driving
                skips += 1
                lost_to_driving += self.driving_schedule[target]
            rem = i - skips
            deficit = self.mdr[target] + lost_to_driving - self.current_energy
            min_charge_amount = max(min_charge_amount, deficit / (rem+1))
        return min_charge_amount

    def current_energy_percent(self):
         return self.current_energy / self.spec.capacity

    def get_current_stats(self, t=None):
        stats = {'current_energy': self.current_energy,}
        if t is not None:
            stats['mdr'] = self.mdr[t]
            stats['driving_schedule'] = self.driving_schedule[t]
            stats['meeting_next_mdr'] = self.current_energy >= self.mdr[(t+1)%24]
        return stats

    def determine_energy_transfer(self, dt, decision, range=None, amount=None):
        proposed_current_energy = self.current_energy

        # Decision structure for what to do at this time instant - do we charge, discharge, or do nothing?
        # If so, how do we use the BESS class characteristics to respect the limits defined?
        if decision == "charge":
            if amount is None:
                amount = dt * self.spec.charge_rate_max
            else:
                amount = min(amount, dt * self.spec.charge_rate_max)

            proposed_current_energy += amount
            # print(f'charging to {proposed_current_energy}')
            proposed_current_energy = min( # Don't charge beyond a set max
                proposed_current_energy,
                max(self.max_operating_capacity(range), self.current_energy) # If we're already past it, don't discharge
            )
            # print(f'adjusted charging to {proposed_current_energy}')
        elif decision == "discharge":
            if amount is None:
                amount = dt * self.spec.discharge_rate_max
            else:
                amount = min(amount, dt * self.spec.discharge_rate_max)

            proposed_current_energy -= amount
            # print(f'discharging to {proposed_current_energy}')
            proposed_current_energy = max( # Don't discharge beyond a set min
                proposed_current_energy,
                min(self.min_operating_capacity(range), self.current_energy) # If we're already below it, don't conjure up new energy
            )
            # print(f'adjusted discharging to {proposed_current_energy}')

        energy_transfer = proposed_current_energy - self.current_energy
        # print(f'energy transfer is {energy_transfer}')
        self.current_energy = proposed_current_energy
        return energy_transfer