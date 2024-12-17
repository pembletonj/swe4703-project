from functools import cmp_to_key

class Bid:
    def __init__(self, price_per_kwh, amount, discharge, creator):
        self.price_per_kwh = price_per_kwh
        self.amount = amount
        self.discharge = discharge
        self.creator = creator
    
    def compare_to(self, other):
        # Sorting by type
        if self.discharge != other.discharge:
            if self.discharge:
                return 1
            return -1
        
        # Sorting by price
        price_diff = self.price_per_kwh - other.price_per_kwh
        if price_diff != 0:
            if self.discharge:
                return -1 * price_diff
            return price_diff
        
        # Sorting by amount where None = Infinity
        if self.amount is None and other.amount is not None:
            return 1
        elif self.amount is not None and other.amount is None:
            return -1
        return other.amount - self.amount

class PassiveMarketController:
    def __init__(self, grid_prices, td):
        self.grid_prices = grid_prices
        self.td = td
        self.ders = []
        self.t = 0
    
    def add_der(self, der):
        self.ders.append(der)
    
    def run_tick(self):
        source_bids = []
        sink_bids = []
        for d in self.ders:
            bid: Bid = d.make_bid(self.t, self.grid_prices[self.t])
            if bid is None:
                continue
            if bid.discharge:
                source_bids.append(bid)
            else:
                sink_bids.append(bid)
        
        for b in source_bids:
            b.price_per_kwh = 0
            b.amount = 0
            b.creator.collect_bid_results(self.t, bid)
        for b in sink_bids:
            if b.price_per_kwh >= self.grid_prices[self.t]:
                b.price_per_kwh = self.grid_prices[self.t]
                b.creator.collect_bid_results(self.t, b)
            else:
                b.price_per_kwh = 0
                b.amount = 0
                b.creator.collect_bid_results(self.t, b)
        
        for d in self.ders:
            d.post_bid(self.t)

        self.t = (self.t + 1) % 24

class DoubleAuctionMarketController:
    def __init__(self, dso, td):
        self.dso = dso
        self.td = td
        self.ders = {}
        self.t = 0
    
    def add_der(self, der, name):
        self.ders[name] = der
    
    def collect_bid_results(self, t, bid: Bid):
        # We're not currently doing anything with grid bids.
        # Should we be recording these?
        # We could make the grid a separate DER if so.
        pass
    
    def add_bid(self, source_bids: list[Bid], sink_bids: list[Bid], bid: Bid, grid_price: int) -> int:
        if bid is None:
            return None
        if bid.discharge:
            # Reject any source bids greater than grid price.
            source_bids.append(bid)
            if bid.amount is None and (grid_price is None or bid.price_per_kwh < grid_price):
                return bid.price_per_kwh
        else:
            # Clamp the max sink bid to grid price.
            # In a real-world application, DERs could abuse the system to get priority if we don't do this.
            if bid.price_per_kwh > grid_price:
                bid.price_per_kwh = grid_price
            sink_bids.append(bid)
        return grid_price

    def run_tick(self) -> dict:
        source_bids: list[Bid] = []
        sink_bids: list[Bid] = []

        if self.dso is not None:
            dso_bid = self.dso.make_bid(self.t, None)
            grid_price = self.add_bid(source_bids, sink_bids, dso_bid, None)

        for d in self.ders.values():
            bid: Bid = d.make_bid(self.t, grid_price)
            self.add_bid(source_bids, sink_bids, bid, grid_price)

        # Double-Auction logic from Wikipedia (average mechanism):
        # https://en.wikipedia.org/wiki/Double_auction
        # Below is a modified version of that algorithm with the following changes:
        # 1. Bids are weighted by the amount of energy the bid calls for. Fractional fulfillment is allowed.
        # 2. All sink (load) bids are fulfilled - the grid compensates for the extra load by supplying power at grid price.
        #    This grid-priced power is factored into the average price.

        price = None
        if len(sink_bids) == 0:
            # This breaks the double-auction logic, just manually deny all bids.
            price = min(b.price_per_kwh for b in source_bids)
            for b in source_bids:
                b.price_per_kwh = price
                b.amount = 0.0
                b.creator.collect_bid_results(self.t, b)
        elif len(source_bids) == 0:
            # This breaks the double-auction logic, just manually deny all bids.
            price = max(b.price_per_kwh for b in sink_bids)
            for b in source_bids:
                b.price_per_kwh = price
                b.amount = 0.0
                b.creator.collect_bid_results(self.t, b)
        else:
            sink_bids.sort(key=cmp_to_key(lambda a, b: a.compare_to(b))) # TODO does this need to be reversed?
            source_bids.sort(key=cmp_to_key(lambda a, b: a.compare_to(b)), reverse=True)

            # print("SINKS:")
            # for b in sink_bids:
            #     print(b.price_per_kwh)
            # print('SOURCES:')
            # for b in source_bids:
            #     print(b.price_per_kwh)

            source_index = 0
            source_taken = 0.0
            sink_index = 0
            sink_taken = 0.0
            # print(f'> RUNNING TICK WITH {len(sink_bids)} sinks and {len(source_bids)} bids:')
            while sink_index < len(sink_bids) and source_index < len(source_bids) and sink_bids[sink_index].price_per_kwh >= source_bids[source_index].price_per_kwh:
                # print(f'=> With sink {sink_index} ({sink_taken}) and source {source_index} ({source_taken})')
                source_rem = None
                sink_rem = None
                if source_bids[source_index].amount is not None:
                    source_rem = source_bids[source_index].amount - source_taken
                if sink_bids[sink_index].amount is not None:
                    sink_rem = sink_bids[sink_index].amount - sink_taken
                
                if sink_rem == source_rem:
                    # print('==> BOTH INC')
                    # Sink and source balance out - increment both.
                    source_taken = 0.0
                    source_index += 1
                    sink_taken = 0.0
                    sink_index += 1
                elif source_rem is None or sink_rem < source_rem:
                    # print('==> SINK INC')
                    # Sink is full, source is partially full.
                    source_taken += sink_rem
                    sink_taken = 0.0
                    sink_index += 1
                else:
                    # print('==> SOURCE INC')
                    # Source is full, sink is partially full.
                    source_taken = 0.0
                    source_index += 1
                    sink_taken += source_rem

            # print(f'{sink_index} {source_index}')
            price = (sink_bids[sink_index-1].price_per_kwh + source_bids[source_index-1].price_per_kwh) / 2

            # Notifying the DERs of their bid results

            for i, b in enumerate(source_bids):
                if i == source_index and source_taken > 0:
                    # The final bid is partially full.
                    b.price_per_kwh = price
                    b.amount = source_taken
                elif i < source_index:
                    # All less than index are guaranteed to be full.
                    b.price_per_kwh = price
                else:
                    # The rest are not fulfilled.
                    b.price_per_kwh = price
                    b.amount = 0.0
                b.creator.collect_bid_results(self.t, b)

            for i, b in enumerate(sink_bids):
                if i == sink_index and sink_taken > 0:
                    # The final bid is partially full.
                    b.price_per_kwh = price
                    b.amount = source_taken
                elif i < sink_index:
                    # All less than index are guaranteed to be full.
                    b.price_per_kwh = price
                else:
                    # The rest are not fulfilled.
                    b.price_per_kwh = price
                    b.amount = 0.0
                b.creator.collect_bid_results(self.t, b)

        for d in self.ders.values():
            d.post_bid(self.t, price)
        self.dso.post_bid(self.t, price)

        self.t = (self.t + 1) % 24

        return {
            'price': price,
            'grid_price': grid_price,
            'sources_total': len(source_bids),
            'sinks_total': len(sink_bids),
        }