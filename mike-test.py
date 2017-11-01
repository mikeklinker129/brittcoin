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
                link = path.nodes[-1].conversions[i]
                direction = path.nodes[-1].actions[i]
                asset_pair = path.nodes[-1].pair_name[i]

                #move is a string
                for asset in self.asset_list:
                    if asset.name==move:
                        move_asset = asset

                new_nodes = (path.nodes+[move_asset])
                new_links = (path.links+[ link ])
                new_directions = (path.directions+ [ direction ])
                new_asset_pair = (path.asset_pairs+ [ asset_pair ])

                new_path = Path(new_nodes, new_links, new_directions, new_asset_pair)
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
    def __init__(self,init_node, links = [], directions = [], asset_pairs = [] ):
        self.nodes = init_node # list of Asset objects
        self.links = links    # list of numbers that link each node
        self.directions = directions
        self.asset_pairs = asset_pairs

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
        # est_fee = .9974**len(self.links)


        if self.value > .999:
            print("Nodes: %s  Percent: %.6f  Links: %s  Pairs: %s" %(','.join(node_names), self.value*100, self.directions, self.asset_pairs))
            
            if self.value>1.0:
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
        self.conversions  = [] # Parallel list to coin conversion
        self.pair_name = []    # The pair name that is used to go from this asset to avail_trades
        self.actions = []      # The direction (buy or sell) that you use to go from this asset to avail_trades
        self.exchange = 'Kraken'



        # Find the trades involving "name"
        for i in range(kraken_data['N']): # Loop over the list of trades
            if kraken_data['haves'][i] == name: # If the base is "name"
                self.avail_trades.append(kraken_data['wants'][i])
                self.conversions.append(kraken_data['conversions'][i])
                self.pair_name.append(kraken_data['pairs'][i])
                self.actions.append(kraken_data['buy_dir'][i])


def get_prices():
    '''
    Get prices from Kraken API
    '''

    k = krakenex.API() # Start the API
    asset_pairs_dict = k.query_public('AssetPairs')['result'] # Get lists of available asset pairs

    # Loop over the asset pairs to get the pair, base, and quote strings
    pairs = []
    haves = []
    wants = []
    buy_direction = []
    rev_direction = []

    for pair_name, data in asset_pairs_dict.items():
        if not pair_name[-2:] == '.d': # Dont search "dark pool pairs" - only 50 BTC or more!
            pairs.append(pair_name)      # Append the name of the pair
            haves.append(data['base'])   # Append the currency that you have (referred to as the base in Kraken)
            wants.append(data['quote'])  # Append the curreny that you want (referred to as the quote in Kraken)
            buy_direction.append('sell') # To go from have to want, you have to use a 'sell' operation.
            rev_direction.append('buy')  # To go from want to have, you have to use a 'buy' operation.


    # Make a comma-separated string from the list of pair names
    pair_string = ','.join(pairs)

    # Call the Kraken API to get all the conversion factors
    conversion_dict = k.query_public('Ticker', {'pair': pair_string} )['result']

    # Get the asks and bids for each asset pair
    asks = []
    bids = []
    for pair_name, data in conversion_dict.items():
        asks.append(float(data['a'][0]))
        bids.append(float(data['b'][0]))

    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction

    # Append the "wants" list to the end of the "haves" list, and vice versa
    new_wants = deepcopy(haves)
    new_haves = deepcopy(wants)
    wants.extend(new_wants)
    haves.extend(new_haves)

    # You will need the pairs to place the order later. Just repeat it 
    pairs.extend(pairs)
    # For a given index, you need to know the pair and the direction (buy or sell) to go from your have to want. 
    buy_direction.extend(rev_direction)

    # Create a conversions list
    # From wants to haves you convert with the bid and the maker fee (0.16%)
    # From haves to wants you convert with 1/ask and the taker fee (0.26%)
    # Example: Asset pair XBTUSD, base = have XBT, quote = want USD, conversion: 1 XBT -> 5000 USD, "selling" XBT for USD, so you are the "maker"

    conversions = [bid * (1. - 0.0016) for bid in bids]
    conversions.extend([(1. - 0.0026)/ask for ask in asks])
    # conversions = [bid*1.0  for bid in bids]
    # conversions.extend([(1.0)/ask for ask in asks])

    # Compile into a dictionary and return
    kraken_data = {
        'unique'     : list(set(haves)), # Unique currencies you have
        'pairs'      : pairs,
        'haves'      : haves,
        'wants'      : wants,
        'conversions': conversions,
        'buy_dir'    : buy_direction,
        'N'          : len(haves)
    }

    return kraken_data


if __name__ == '__main__':

    while True:
    # Get the data from Kraken
    # Get the data from Kraken

        try:
            kraken_data = get_prices()
        except Exception as e:
            time.sleep(5)
            continue    

        # Loop over the assets and make a list
        asset_list = []
        for asset in kraken_data['unique']:
            # Make an instance of the Asset class with that asset's name
            exec(asset + '= Asset(kraken_data,\'' + asset + '\')')

            # Append the Asset instance to the list
            asset_list.append(eval(asset))

        trial_list = []

        for asset in asset_list:
            if asset.name in ['XXBT','XETH']:
                # print(asset.name, asset.avail_trades)
                trial_list.append(asset)
            # if asset.name=='XETH':
            #     trial_list.append(asset)

        
        # trial_list = asset_list
        master_path = PathList(asset_list,trial_list)
        # print("god help us")
        for i in range(0,4):
            master_path.step()

        master_path.show_paths()

        time.sleep(0)










