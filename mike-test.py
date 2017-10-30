import krakenex
import sys
import pprint
import numpy as np
from copy import deepcopy
import time

# https://cryptocoincharts.info/markets/show/kraken


class PathList():
    def __init__(self, all_assets, start_points):
        self.path_list = []
        self.complete_paths = []
        self.initialize(start_points)
        self.asset_list = all_assets

    def initialize(self,asset_list):
        for asset in asset_list:
            new_path = Path( [asset] )  
            self.path_list.append(new_path)

    
    def step(self):
        new_path_list = []

        for path in self.path_list:

            next_moves  = path.nodes[-1].avail_trades
            # print('Next Moves: ',next_moves)

            for i in range(0,len(next_moves)):
                move = next_moves[i]
                # print("Move: ",move)
                link = path.nodes[-1].avail_prices[i]
            # for move in next_moves:
                #move is a string
                for asset in self.asset_list:

                    if asset.name==move:
                        move_asset = asset
                new_nodes = (path.nodes+[move_asset])
                new_links = (path.links+[ link ])
                new_path = Path(new_nodes, new_links)
                new_path_list.append(new_path)

        self.path_list = new_path_list

        self.remove_complete_paths()

    def remove_complete_paths(self):
        for path in self.path_list:
            if path.is_complete():
                self.complete_paths.append(path)
                self.path_list.remove(path)
                # if path.value>1:
                # print('maybe we will make some money MN: ',path.value)

    def show_paths(self):

        self.complete_paths.sort(key=lambda r: -r.value)
        for i in range(0,1):
        # for i in range(0,len(self.complete_paths)):
            try:
                self.complete_paths[i].print_path()
            except:
                continue

class Path(object):
    def __init__(self,init_node, links = []):
        self.nodes = init_node # list of Asset objects
        self.links = links    # list of numbers that link each node
        self.value = self.compute_val()  
        self.length = len(self.nodes)

    def compute_val(self):
        product = 1
        for l in self.links:
            product*=l
        return product

    def is_complete(self):
        if self.nodes[0]==self.nodes[-1]:
            return True
        else:
            return False

    def print_path(self):
        node_names = []
        for node in self.nodes:
            node_names.append(node.name)
        est_fee = .9974**len(self.links)


        if self.value>1.0:
            print("Nodes: %s  Full Percentage: %.6f Est Percentage With Fees: %.6f" %(','.join(node_names), self.value*100, self.value*est_fee*100 ))
            
            if self.value*est_fee>1:
                print("FUCK YEHHHHHHHHHHHHHH BUY THT SHIT")

            # print("Price Info:")
            # list_links = []
            # for i in range(0,len(node_names)-1):
            #     list_links.append(node_names[i]+node_names[i+1])
            # kk = krakenex.API()
            # for link in list_links:
            #     r = kk.query_public('Ticker', {'pair': link} )
            #     pprint.pprint(r)

    # def __append__():
    #     check left, check right
    #     update value



class Asset():
    '''
    This is the main asset type that the tree system will use.
    It does not matter which exchange this asset came from, as long as the price information is correct.
    '''
    def __init__(self, kraken_data, name):

        self.name = name # String of currency name
        self.avail_trades = [] # Currencies this coin can be converted to
        self.avail_prices = [] # Parallel list to coin conversion
        self.exchange = 'Kraken'

        # Find the trades involving "name"
        for i in range(kraken_data['N']): # Loop over the list of trades
            if kraken_data['bases'][i] == name: # If the base is "name"
                self.avail_trades.append(kraken_data['quotes'][i])
                self.avail_prices.append(kraken_data['prices'][i])


def get_prices():
    '''
    Get prices from Kraken API
    '''

    k = krakenex.API() # Start the API
    asset_pairs_dict = k.query_public('AssetPairs')['result'] # Get lists of available asset pairs

    # Loop over the asset pairs to get the pair, base, and quote strings
    pairs = []
    bases = []
    quotes = []
    for pair_name, data in asset_pairs_dict.items():
        if not pair_name[-2:] == '.d': # Dont search "dark pool pairs" - only 50 BTC or more!
            pairs.append(pair_name)      # Append the name of the pair
            bases.append(data['base'])   # Append the base currency (quote denomination)
            quotes.append(data['quote']) # Append the quote

    # Make a comma-separated string from the list of pair names
    pair_string = ','.join(pairs)

    # Call the Kraken API to get all the prices
    price_dict = k.query_public('Ticker', {'pair': pair_string} )['result']

    # Loop over the prices to make a list like pairs, bases, quotes
    prices = []
    prices_ask = []
    prices_bid = []

    for pair_name, data in price_dict.items():
        prices_ask.append(float(data['a'][0])) # Append the ask price (this is how you access it...)
        prices_bid.append(float(data['b'][0])) # List of the bid prices
    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction

    prices = prices_bid 
    inv_prices = [1./p for p in prices_ask] # New prices are the inverse prices

    # Append the "quotes" list to the end of the "bases" list, and vice versa
    new_bases  = deepcopy(quotes)
    new_quotes = deepcopy(bases)


    bases.extend(new_bases)
    quotes.extend(new_quotes)
    prices.extend(inv_prices)

    # Compile into a dictionary and return
    kraken_data = {
        'unique': list(set(bases)), # Unique bases
        'bases' : bases,
        'quotes': quotes,
        'prices': prices,
        'N'     : len(prices)
    }

    return kraken_data


if __name__ == '__main__':

    while True:
    # Get the data from Kraken
        kraken_data = get_prices()

        # Loop over the assets and make a list
        asset_list = []
        for asset in kraken_data['unique']:
            # Make an instance of the Asset class with that asset's name
            exec(asset + '= Asset(kraken_data,\'' + asset + '\')')

            # Append the Asset instance to the list
            asset_list.append(eval(asset))

        trial_list = []

        for asset in asset_list:
            if asset.name in ['XXBT','XETH','XMLN']:
                # print(asset.name, asset.avail_trades)
                trial_list.append(asset)
            # if asset.name=='XETH':
            #     trial_list.append(asset)

        
        trial_list = asset_list
        master_path = PathList(asset_list,trial_list)
        # print("god help us")
        for i in range(0,4):
            # print(i)
            master_path.step()

        master_path.show_paths()

        time.sleep(1)










