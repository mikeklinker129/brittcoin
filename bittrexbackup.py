
import sys
import pprint
import numpy as np
from copy import deepcopy
import time
import datetime

from bittrex_api import BittrexAPI

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

    
    def step(self, final_step = False):
        new_path_list = []

        for path in self.path_list:

            next_moves  = path.nodes[-1].avail_trades
            # print('Next Moves: ',next_moves)

            # If we're on the final step, return to the initial asset
            if final_step:
                # Next move returns you to the original asset
                next_moves = [path.nodes[0].name]

                # See if we can get back to the intial coin
                try:
                    # Get the index of the original asset from the list of available trades
                    complete_loop_index = path.nodes[-1].avail_trades.index(next_moves[0])
                # We're in too deep, cant get back to original coin
                except:
                    # Skip this loop
                    continue


            for i in range(0,len(next_moves)):

                move = next_moves[i]

                # If its the last step, correct the index for the particular trade you want
                if final_step:
                    i = complete_loop_index

                # THESE ARE THE PREVIOUS LISTS> TO BE APPENDED.
                link             = path.nodes[-1].conversions[i]
                direction        = path.nodes[-1].order_actions[i]
                asset_pair       = path.nodes[-1].pair_names[i]
                order_vol_denoms = path.nodes[-1].order_vol_denoms[i]
                btc_volumes      = path.nodes[-1].btc_volumes[i]

                #move is a string
                for asset in self.asset_list:
                    if asset.name==move:
                        move_asset = asset

                new_nodes = (path.nodes+[move_asset])
                new_links = (path.links+[ link ])
                new_directions = (path.directions+ [ direction ])
                new_asset_pair = (path.asset_pairs+ [ asset_pair ])
                new_order_vol_denoms = (path.order_vol_denoms + [ order_vol_denoms ])
                new_btc_volumes = (path.btc_volumes + [ btc_volumes ])

                new_path = Path(new_nodes, new_links, new_directions, new_asset_pair, new_order_vol_denoms, new_btc_volumes)
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
        for i in range(0,5):
        # for i in range(0,len(self.complete_paths)):
            try:
                self.complete_paths[i].print_path()
            except:
                continue

        print('\n')


    def return_best(self):
        self.complete_paths.sort(key=lambda r: -r.value)
        return self.complete_paths[0]


class Path(object):
    def __init__(self,init_node, links = [], directions = [], asset_pairs = [], order_vol_denoms = [], btc_volumes = [] ):
        self.nodes = init_node # list of Asset objects
        self.links = links    # list of numbers that link each node
        self.directions = directions
        self.asset_pairs = asset_pairs
        self.order_vol_denoms = order_vol_denoms
        self.btc_volumes = btc_volumes

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

        if self.value > .997:
            # print("Nodes= %s \nPercent= %.6f \nDirections= %s \nPairs= %s \nLinks= %s \nVolC= %s \n\n\n" %((node_names), self.value*100, self.directions, self.asset_pairs, self.links, self.order_vol_denoms))
            print("Nodes: %s  Percent: %.6f. BTC vol: %s" %(node_names,self.value*100, self.btc_volumes))

            if True:
                with open('log_file3.csv','a') as w:
                    string=''
                    for i in range(0,len(node_names)-1):
                        string += node_names[i] + ','

                    string+='%.6f,%s \n'%(self.value*100.0, self.btc_volumes)
                    w.write(string)

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
        self.avail_trades   = [] # Currencies this coin can be converted to
        self.conversions    = [] # Conversion ratios for each of the available trades (how much you will have of the new currency after trading)
        self.pair_names     = [] # Names of the currency pair you will actually trade on the exchange
        self.exchange = 'Bittrex'

        # Terms for actually placing the order
        self.order_actions      = [] # 'BUY' or 'SELL'
        self.btc_volumes        = [] # Volume in terms of  bitcoin.       (for a digital to fiat trade, this is # digital coins)
        self.order_vol_denoms   = [] # Denominations of the order_volumes (for a digital to fiat trade, this is name of digital coins)
        self.order_prices       = [] # Price in terms of the website      (for a digital to fiat trade, this is price in fiat currency)
        self.order_price_denoms = [] # Denominations of the order_prices  (for a digital to fiat trade, this is name of fiat currency)


         # Find the trades involving "name"
        for i in range(kraken_data['N']): # Loop over the list of trades
            if kraken_data['haves'][i] == name: # If the base is "name"
                self.avail_trades.append(      kraken_data['wants'             ][i])
                self.conversions.append(       kraken_data['conversions'       ][i])
                self.pair_names.append(        kraken_data['pair_names'        ][i])
                # self.max_amounts.append(       kraken_data['max_amounts'       ][i])
                self.order_actions.append(     kraken_data['order_actions'     ][i])
                self.btc_volumes.append(       kraken_data['btc_volumes'       ][i])
                self.order_vol_denoms.append(  kraken_data['order_vol_denoms'  ][i])
                self.order_prices.append(      kraken_data['order_prices'      ][i])
                self.order_price_denoms.append(kraken_data['order_price_denoms'][i])



def get_prices(B):
    '''
    Get prices from Bittrex API

    Inputs: Bittrex API Object, B. 
            asset_pairs_dict = asset pairs from Bittrex. 
    '''


    # Call the Bittrex API to get all the asks and bids
    t0 = datetime.datetime.now()
    price_dict = B.getmarketsummaries()
    t1 = datetime.datetime.now()
    print("Market Summary Response Time: %.4f" %((t1-t0).total_seconds()))

    # Loop over the asset pairs to get the pair, base, and quote strings
    pairs       = []
    haves       = []
    wants       = []
    asks        = []
    bids        = []
    btc_volumes = []
    N = 0 # Number of pairs


     # We need the following conversions before we start:
    USDtoBTC = 0
    ETHtoBTC = 0

    # Go through the asset pair dictionary and find the conversions from USD to BTC and ETH to BTC
    # This will be used when getting each markets volume in BTC. 
    for market in price_dict:
        # pprint.pprint(market['MarketName'])
        if market['MarketName']=='USDT-BTC':
            USDtoBTC = 1.0/market['Ask']
        if market['MarketName']=='BTC-ETH':
            ETHtoBTC = 1.0/market['Ask']

    for market in price_dict:
        # protect against shit coin names that cannot be turned into variables
        if '1ST' in market['MarketName'] or '2GIVE' in market['MarketName']:
            continue



        # protect against coins that are currently inactive...
        if market['Ask']==0.0 or market['Bid']==0.0:
            # print('fuck: ',market['MarketName'])
            continue

        pairs.append(market['MarketName'])

        #base is always first, market second. 
        assets = market['MarketName'].split('-')
        base_currency = assets[0]
        market_currency = assets[1]

        haves.append(base_currency)
        wants.append(market_currency)


        asks.append(market['Ask'])
        bids.append(market['Bid'])

        N+=1


        # Volume estimate should always be in BTC. 
        temp_vol = 'SHIT'
        if base_currency=='BTC':
            temp_vol = market['BaseVolume']
        elif market=='BTC':
            temp_vol = market['Volume']
        elif base_currency=='USDT':
            temp_vol = market['BaseVolume']*USDtoBTC
        elif base_currency=='ETH':
            temp_vol = market['BaseVolume']*ETHtoBTC
        else:
            print("Shits Whack")

        btc_volumes.append(temp_vol)



    # Volume denomination is the want (Market) in Bittrex, and stays the same regardless of trade direction
    order_vol_denoms = deepcopy(wants)
    order_vol_denoms.extend(deepcopy(wants))

    # Price denomination is the have (Base) in Bittrex, and stays the same regardless of trade direction
    order_price_denoms = deepcopy(haves)
    order_price_denoms.extend(deepcopy(haves))

    # BTC Volume estimates: Extend it to be the correct length. 
    btc_volumes.extend(deepcopy(btc_volumes))


    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction
    # Append the "wants" list to the end of the "haves" list, and vice versa
    new_wants = deepcopy(haves)
    new_haves = deepcopy(wants)
    wants.extend(new_wants)
    haves.extend(new_haves)

    # Create the actions (buy/sell) list
    # Going from a have to a want is a BUY in the Bittrex nomenclature
    # Example: Asset pair BTC-ETH, if you have BTC and want ETH, you are BUYing ETH with BTC
    #                              if you have ETH and want BTC, you are SELLing ETH for BTC
    order_actions =      ['BUY' for ask  in asks]
    order_actions.extend(['SELL' for bid in bids])

    # Create a conversions list
    # From haves to wants you BUY & convert with 1/ask and the taker fee (0.25% for Bittrex)
    # From wants to haves you SELL & convert with the bid and the maker fee (0.25% for Bittrex)
    # Example: Asset pair XXBTZUSD, base=have XBT, quote=want USD, conversion: 1 XBT -> 5000 USD, "selling" XBT for USD, so you are the "maker"
    # conversions = [bid * (1. - 0.0025) for bid in bids]
    # conversions.extend([(1. - 0.0025)/ask for ask in asks])

    # Start with the BUYs
    conversions = [(1. - 0.0025)/ask for ask in asks]
    conversions.extend([bid * (1. - 0.0025) for bid in bids])

    # Create ask/bid price and volumes list
    # Use the same logic as the conversion list, start with list of bids, then extend by list of asks
    order_prices  = deepcopy(bids)
    order_prices.extend(deepcopy(asks))
    # order_volumes = deepcopy(bid_vols).extend(deepcopy(ask_vols))

    # You will need the pairs to place the order later. Just repeat it
    pairs.extend(deepcopy(pairs))

    # Make the max_amounts vector, which will be in the denomination of the Asset
    # Example: Think of XBT -> USD...
    # max_amounts = deepcopy(bid_vols) # First half of vector is just the bid volume (e.g. 0.05 XBT)
    # max_amounts.extend( [asks[i]*ask_vols[i] for i in range(N)] ) # Second half of the vector is ask*ask_vol
    #                                                               # 6000 $/XBT * 0.05 XBT = $300

    # Double the length
    N = 2*N

    # Compile into a dictionary and return
    bittrex_data = {
        'unique'            : list(set(haves)), # Unique currencies you have
        'pair_names'        : pairs,
        'haves'             : haves,
        'wants'             : wants,
        'conversions'       : conversions,
        # 'max_amounts'       : max_amounts,
        'order_actions'     : order_actions,
        'btc_volumes'       : btc_volumes,
        'order_vol_denoms'  : order_vol_denoms,
        'order_prices'      : order_prices,
        'order_price_denoms': order_price_denoms,
        'N'                 : N
    }

    return bittrex_data


if __name__ == '__main__':



    B = BittrexAPI('bittrex_key.key') # Start the API
    #asset_pairs_dict = k.query_public('AssetPairs')['result'] # Get lists of available asset pairs
    # asset_pairs_dict = B.getmarkets()


    count = 0
    while True:
        


        exchange_data = get_prices(B)



        # Loop over the assets and make a list
        asset_list = []
        for asset in exchange_data['unique']:

            # Make an instance of the Asset class with that asset's name
            exec(asset + '= Asset(exchange_data,\'' + asset + '\')')

            # Append the Asset instance to the list
            asset_list.append(eval(asset))

        trial_list = []

        for asset in asset_list:
            if asset.name in ['USDT']:
                # print(asset.name, asset.avail_trades)
                trial_list.append(asset)
            # if asset.name=='XETH':
            #     trial_list.append(asset)

        
        # trial_list = asset_list
        master_path = PathList(asset_list,trial_list)
        # print("god help us")
        t0 = datetime.datetime.now()
        for i in range(0,3):
            if i<2:
                master_path.step()
            else:
                master_path.step(final_step=True)
        t1 = datetime.datetime.now()
        print("Path Build Time: %.4f" %((t1-t0).total_seconds()))

        master_path.show_paths()
        best_path = master_path.return_best()

        count+=1









