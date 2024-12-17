from ev import EV, EVSpec

class TestEV:
    spec = EVSpec(
        capacity=100,
        charge_rate_max=5,
        discharge_rate_max=4,
        initial_energy=22,
        operating_range=(0.1, 0.9)
    )

    driving_schedule = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0,
                    8.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    mdr = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 15.0, 20.0, 20.0, 15.0, 15.0, 15.0,
        15.0, 15.0, 15.0, 15.0, 15.0, 20.0, 15.0, 15.0, 15.0, 10.0, 10.0, 10.0]

    ev = EV(spec, mdr, driving_schedule)
    
    def test_ev_spec_creation(self):
        assert self.spec.capacity == 100
        assert self.spec.charge_rate_max == 5
        assert self.spec.discharge_rate_max == 4
        assert self.spec.initial_energy == 22
        assert self.spec.operating_range == (0.1, 0.9)
    
    def test_ev_creation(self):
        assert self.ev.spec == self.spec
        assert self.ev.mdr == self.mdr
        assert self.ev.driving_schedule == self.driving_schedule
        assert self.ev.current_energy == self.spec.initial_energy
    
    def test_max_operating_capacity(self):
        cap = self.ev.max_operating_capacity()
        assert cap == self.ev.spec.capacity * 0.9

    def test_max_operating_capacity_with_large_range(self):
        cap = self.ev.max_operating_capacity(range=(0.05, 0.95))
        assert cap == self.ev.spec.capacity * 0.9
    
    def test_max_operating_capacity_with_small_range(self):
        cap = self.ev.max_operating_capacity(range=(0.2, 0.7))
        assert cap == self.ev.spec.capacity * 0.7
    
    def test_min_operating_capacity(self):
        cap = self.ev.min_operating_capacity()
        assert cap == self.ev.spec.capacity * 0.1

    def test_min_operating_capacity_with_large_range(self):
        cap = self.ev.min_operating_capacity(range=(0.05, 0.95))
        assert cap == self.ev.spec.capacity * 0.1
    
    def test_min_operating_capacity_with_small_range(self):
        cap = self.ev.min_operating_capacity(range=(0.2, 0.7))
        assert cap == self.ev.spec.capacity * 0.2
    
    def test_left_to_charge(self):
        left = self.ev.left_to_charge()
        assert left == (self.ev.spec.capacity * 0.9) - self.ev.current_energy
    
    def test_left_to_charge_negative(self):
        self.ev.current_energy = 1.5 * self.ev.spec.capacity
        left = self.ev.left_to_charge()
        assert left == 0
    
    def test_minimum_charge_amount_none_needed(self):
        self.ev.current_energy = 1.5 * self.ev.spec.capacity
        amount = self.ev.minimum_charge_amount(0)
        assert amount == 0
    
    def test_minimum_charge_amount_for_next(self):
        self.ev.current_energy = 5.0
        amount = self.ev.minimum_charge_amount(0)
        assert amount == 2.5
    
    def test_minimum_charge_amount_for_later(self):
        self.ev.current_energy = 8.0
        amount = self.ev.minimum_charge_amount(3)
        assert amount == 1.75
    
    def test_current_energy_percent(self):
        self.ev.current_energy = 22
        assert self.ev.current_energy_percent() == 0.22
    
    def test_get_current_stats(self):
        stats = self.ev.get_current_stats()
        assert stats == {
            'current_energy': self.ev.current_energy,
        }
    
    def test_get_current_stats_timed(self):
        stats = self.ev.get_current_stats(t=7)
        assert stats == {
            'current_energy': self.ev.current_energy,
            'mdr': self.mdr[7],
            'driving_schedule': self.driving_schedule[7],
            'meeting_next_mdr': True,
        }
    
    def test_invalid_energy_transfer(self):
        self.ev.current_energy = 22
        self.ev.determine_energy_transfer(1, 'nope')
        assert self.ev.current_energy == 22
    
    def test_charge_max_rate(self):
        self.ev.current_energy = 22
        self.ev.determine_energy_transfer(1, 'charge')
        assert self.ev.current_energy == 27
    
    def test_charge_to_capacity(self):
        self.ev.current_energy = 88
        self.ev.determine_energy_transfer(1, 'charge')
        assert self.ev.current_energy == 90
    
    def test_charge_by_amount(self):
        self.ev.current_energy = 22
        self.ev.determine_energy_transfer(1, 'charge', amount=3)
        assert self.ev.current_energy == 25
    
    def test_charge_in_range(self):
        self.ev.current_energy = 22
        self.ev.determine_energy_transfer(1, 'charge', range=(0.2, 0.26))
        assert self.ev.current_energy == 26
    
    def test_charge_amount_and_capacity(self):
        self.ev.current_energy = 88
        self.ev.determine_energy_transfer(1, 'charge', amount=3)
        assert self.ev.current_energy == 90

    def test_discharge_max_rate(self):
        self.ev.current_energy = 70
        self.ev.determine_energy_transfer(1, 'discharge')
        assert self.ev.current_energy == 66
    
    def test_discharge_to_capacity(self):
        self.ev.current_energy = 12
        self.ev.determine_energy_transfer(1, 'discharge')
        assert self.ev.current_energy == 10
    
    def test_discharge_by_amount(self):
        self.ev.current_energy = 70
        self.ev.determine_energy_transfer(1, 'discharge', amount=3)
        assert self.ev.current_energy == 67
    
    def test_discharge_in_range(self):
        self.ev.current_energy = 70
        self.ev.determine_energy_transfer(1, 'discharge', range=(0.68, 0.9))
        assert self.ev.current_energy == 68
    
    def test_discharge_amount_and_capacity(self):
        self.ev.current_energy = 12
        self.ev.determine_energy_transfer(1, 'discharge', amount=3)
        assert self.ev.current_energy == 10