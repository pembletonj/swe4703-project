#!/usr/bin/env python3

import random
import matplotlib.pyplot as plt
import numpy as np

from ev import EVSpec
from home import Home, gen_schedule_by_prices_and_mean
from rule_based_ev import RuleBasedEV
from optimized_ev import OptimizedEV
from grid import TimeOfUseGrid
from recording_wrapper import RecordingWrapper
from market import DoubleAuctionMarketController

num_rbevs = 4
num_loevs = 4
num_homes = 8
simulation_name = 'Mixed'

def display_day(day_num: int,
                grid_prices: np.ndarray[float],
                market_prices: np.ndarray[float],
                grid_costs: np.ndarray[float],
                rbev_costs: np.ndarray[float],
                loev_costs: np.ndarray[float],
                grid_amounts: np.ndarray[float]):
    hours = np.arange(24)
    nrows = 3
    ncols = 2

    plt.figure(
        figsize=(10, 10),
        num=f'Day: {day_num}; Simulation: {simulation_name}'
    )

    plt.subplot(nrows, ncols, 1)
    plt.plot(hours, grid_prices, label='Price ($/kWh)')
    plt.ylabel('Price ($/kWh)')
    plt.title('Grid Price over 24 Hours')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.legend()

    plt.subplot(nrows, ncols, 2)
    plt.plot(hours, market_prices, label='Price ($/kWh)')
    plt.ylabel('Price ($/kWh)')
    plt.title('Market Price over 24 Hours')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.axhline(y=market_prices.mean(), color='purple', linestyle='--')
    plt.axhline(y=market_prices.max(), color='red', linestyle='--')
    plt.legend()

    print(f'Mean market price: f{market_prices.mean()}')

    plt.subplot(nrows, ncols, 3)
    plt.plot(hours, grid_amounts, label='Energy (kWh)')
    plt.ylabel('Cost ($)')
    plt.title('Grid Energy Dependence over 24 Hours (kWh)')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.axhline(y=grid_amounts.max(), color='purple', linestyle='--')
    plt.axhline(y=grid_amounts.mean(), color='red', linestyle='--')
    plt.legend()

    print(f'Grid total amount: {grid_amounts.sum()}')

    plt.subplot(nrows, ncols, 4)
    plt.plot(hours, grid_costs, label='Cost ($)')
    plt.ylabel('Cost ($)')
    plt.title('Grid Costs over 24 Hours')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.axhline(y=grid_costs.mean(), color='purple', linestyle='--')
    plt.axhline(y=grid_costs.max(), color='red', linestyle='--')
    plt.legend()

    print(f'Grid total cost: {grid_costs.sum()}')

    plt.subplot(nrows, ncols, 5)
    plt.plot(hours, rbev_costs, label='Cost ($)')
    plt.ylabel('Cost ($)')
    plt.title('Average Cost to Rule-Based EVs over 24 Hours')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.axhline(y=rbev_costs.mean(), color='purple', linestyle='--')
    plt.axhline(y=rbev_costs.max(), color='red', linestyle='--')
    plt.legend()

    print(f'RBEV mean cost: {rbev_costs.mean()}')

    plt.subplot(nrows, ncols, 6)
    plt.plot(hours, loev_costs, label='Cost ($)')
    plt.ylabel('Cost ($)')
    plt.title('Average Cost to Optimization-Based EVs over 24 Hours')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.axhline(y=loev_costs.mean(), color='purple', linestyle='--')
    plt.axhline(y=loev_costs.mean(), color='red', linestyle='--')
    plt.legend()

    print(f'LOEV mean cost: {loev_costs.mean()}')

    plt.tight_layout()
    plt.show()

def main():

    # Ensure same results with each test
    random.seed(0)
    
    # Source: https://www.hydroone.com/rates-and-billing/rates-and-charges/electricity-pricing-and-costs
    weekday_winter = np.array([7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 15.8, 15.8, 15.8, 15.8, 12.2,
                               12.2, 12.2, 12.2, 12.2, 12.2, 15.8, 15.8, 7.6, 7.6, 7.6, 7.6, 7.6])
    mean = weekday_winter.mean()
    maximum = weekday_winter.max()
    minimum = weekday_winter.min()

    home_schedule = gen_schedule_by_prices_and_mean(weekday_winter, 2.0)

    driving_schedule = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0,
                        4.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    # MDR is based on the following:
    # User wants a minimum all the time for emergencies.
    # User wants extra throughout the day for unexpected travel needs.
    # User wants a lot during rush hours in case of traffic or accidents etc.
    mdr = [6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 15.0, 20.0, 20.0, 15.0, 15.0, 15.0,
           15.0, 15.0, 15.0, 15.0, 15.0, 20.0, 15.0, 15.0, 15.0, 10.0, 10.0, 10.0]

    dso = RecordingWrapper(TimeOfUseGrid(weekday_winter))
    market = DoubleAuctionMarketController(dso, 1)

    ev_spec = EVSpec(
        capacity=40, # kWh
        charge_rate_max=10, # kW
        discharge_rate_max=10, # kW
        initial_energy=0.0, # kWh
        operating_range=(0.2, 0.8), # Percent
    )

    for i in range(num_rbevs):
        der = RecordingWrapper(RuleBasedEV(
            spec=ev_spec,
            mdr=mdr,
            driving_schedule=driving_schedule,
            max_charge_price=(minimum+mean)/2,
            min_discharge_price=(maximum+mean)/2,
        ))
        market.add_der(der, f'rbev_{i}')

    for i in range(num_loevs):
        der = RecordingWrapper(OptimizedEV(
            spec=ev_spec,
            driving_schedule=driving_schedule,
            mdr=mdr,
            history=weekday_winter.copy(), # It'll be editing this list, may not want to give it the original.
        ))
        market.add_der(der, f'loev_{i}')
    
    for i in range(num_homes):
        der = RecordingWrapper(Home(
            schedule=home_schedule,
            randomness=0.1,
        ))
        market.add_der(der, f'home_{i}')

    for i in range(5):
        print(f'RUNNING DAY {i}:')
        day_stats: list[dict] = []
        dso_stats: list[dict] = []

        day_rbev_costs: list[float] = []
        day_loev_costs: list[float] = []
        day_home_costs: list[float] = []

        for t in range(24):
            stats = market.run_tick()
            day_stats.append(stats)
            dso_stats.append(market.dso.post_bid_stats)

            for j in range(num_rbevs):
                if not market.ders[f'rbev_{j}'].post_bid_stats['meeting_next_mdr']:
                    print(f'ft={t} rbev not meeting next mdr! action={market.ders[f'rbev_{j}'].post_bid_stats['last_action']}')
            for j in range(num_loevs):
                if not market.ders[f'loev_{j}'].post_bid_stats['meeting_next_mdr']:
                    print(f'ft={t} loev not meeting next mdr! action={market.ders[f'loev_{j}'].post_bid_stats['last_action']}')

            # TODO Display these
            rbev_costs = np.array([market.ders[f'rbev_{j}'].post_bid_stats['cost'] for j in range(num_rbevs)])
            # print(rbev_costs)
            day_rbev_costs.append(rbev_costs.mean())
            loev_costs = np.array([market.ders[f'loev_{j}'].post_bid_stats['cost'] for j in range(num_loevs)])
            # print(market.ders['loev_1'].post_bid_stats)
            day_loev_costs.append(loev_costs.mean())
            home_costs = np.array([market.ders[f'home_{j}'].post_bid_stats['cost'] for j in range(num_homes)])
            # print(home_costs)
            day_home_costs.append(home_costs.mean())

        day_market_prices = [s['price'] for s in day_stats]
        day_grid_prices = [s['grid_price'] for s in day_stats]
        day_grid_costs = [s['cost'] for s in dso_stats]

        # TODO display this
        day_grid_amount = [s['granted_amount'] for s in dso_stats]
        
        display_day(
            day_num=i+1,
            grid_prices=np.array(day_grid_prices),
            market_prices=np.array(day_market_prices),
            grid_costs=np.array(day_grid_costs),
            rbev_costs=np.array(day_rbev_costs),
            loev_costs=np.array(day_loev_costs),
            grid_amounts=np.array(day_grid_amount),
        )

if __name__ == '__main__':
    main()