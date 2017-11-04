
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

    
    def step(self):
        new_path_list = []

        for path in self.path_list:

            next_moves  = path.nodes[-1].avail_trades
            # print('Next Moves: ',next_moves)

            for i in range(0,len(next_moves)):
                move = next_moves[i]
                
                # THESE ARE THE PREVIOUS LISTS> TO BE APPENDED.
                link = path.nodes[-1].conversions[i]
                direction = path.nodes[-1].order_actions[i]
                asset_pair = path.nodes[-1].pair_names[i]
                order_vol_denoms = path.nodes[-1].order_vol_denoms[i]

                #move is a string
                for asset in self.asset_list:
                    if asset.name==move:
                        move_asset = asset

                new_nodes = (path.nodes+[move_asset])
                new_links = (path.links+[ link ])
                new_directions = (path.directions+ [ direction ])
                new_asset_pair = (path.asset_pairs+ [ asset_pair ])
                new_order_vol_denoms = (path.order_vol_denoms + [ order_vol_denoms ])

                new_path = Path(new_nodes, new_links, new_directions, new_asset_pair, new_order_vol_denoms)
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
    def __init__(self,init_node, links = [], directions = [], asset_pairs = [], order_vol_denoms = [] ):
        self.nodes = init_node # list of Asset objects
        self.links = links    # list of numbers that link each node
        self.directions = directions
        self.asset_pairs = asset_pairs
        self.order_vol_denoms = order_vol_denoms

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

        if self.value > .99:
            # print("Nodes= %s \nPercent= %.6f \nDirections= %s \nPairs= %s \nLinks= %s \nVolC= %s \n\n\n" %((node_names), self.value*100, self.directions, self.asset_pairs, self.links, self.order_vol_denoms))
            print("Nodes: %s  Percent: %.6f" %(node_names,self.value*100))

            with open('log_file2.csv','a') as w:
                string=''
                for i in range(0,len(node_names)-1):
                    string += node_names[i] + ','
                string+='%.6f \n'%(self.value*100.0)
                print(string)
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
        self.order_volumes      = [] # Volume in terms of the website     (for a digital to fiat trade, this is # digital coins)
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
                # self.order_volumes.append(     kraken_data['order_volumes'     ][i])
                self.order_vol_denoms.append(  kraken_data['order_vol_denoms'  ][i])
                self.order_prices.append(      kraken_data['order_prices'      ][i])
                self.order_price_denoms.append(kraken_data['order_price_denoms'][i])



def get_prices(B, asset_pairs_dict):
    '''
    Get prices from Bittrex API

    Inputs: Bittrex API Object, B. 
            asset_pairs_dict = asset pairs from Bittrex. 
    '''

    # Loop over the asset pairs to get the pair, base, and quote strings
    pairs = []
    haves = []
    wants = []
    N = 0 # Number of pairs
    for pair in asset_pairs_dict:
        #for now lets ignore 1ST and 2GIVE, TODO: deal with their variable names.
        if '1ST' in pair['MarketName'] or '2GIVE' in pair['MarketName']:
            continue



        if pair['IsActive']:
            pairs.append(pair['MarketName'])      # Append the name of the pair
            haves.append(pair['BaseCurrency'])   # Append the currency that you have (referred to as the base in Kraken)
            wants.append(pair['MarketCurrency'])  # Append the curreny that you want (referred to as the quote in Kraken)
            N += 1
            # if pair['MarketName']=="BTC-ETH":
            #     pprint.pprint(pair)



    # Call the Bittrex API to get all the asks and bids
    t0 = datetime.datetime.now()
    price_dict = B.getmarketsummaries()
    t1 = datetime.datetime.now()
    print("Market Summary Response Time: %.4f" %((t1-t0).total_seconds()))

    # We don't know if they are in the correct indexes, so loop through to fill the arrays. 
    asks     = []
    bids     = []
    ask_vols = []
    bid_vols = []
    for pair in pairs:
        for data in price_dict:
            if data['MarketName']==pair:
                # if pair=="BTC-ETH":
                #     pprint.pprint(data)
                asks.append(data['Ask'])
                bids.append(data['Bid'])
                #No volume information yet :(
                break #Move to the outer for loop.


    # Volume denomination is the want (Market) in Bittrex, and stays the same regardless of trade direction
    order_vol_denoms = deepcopy(wants)
    order_vol_denoms.extend(deepcopy(wants))

    # Price denomination is the have (Base) in Bittrex, and stays the same regardless of trade direction
    order_price_denoms = deepcopy(haves)
    order_price_denoms.extend(deepcopy(haves))

    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction
    # Append the "wants" list to the end of the "haves" list, and vice versa
    wants.extend(deepcopy(haves))
    haves.extend(deepcopy(wants))

    # Create the actions (buy/sell) list
    # Going from a have to a want is a BUY in the Bittrex nomenclature
    # Example: Asset pair BTC-ETH, if you have BTC and want ETH, you are BUYing ETH with BTC
    #                              if you have ETH and want BTC, you are SELLing ETH for BTC
    order_actions =      ['BUY' for ask  in asks]
    order_actions.extend(['SELL' for bid in bids])

    # Create a conversions list
    # From wants to haves you convert with the bid and the maker fee (0.16%)
    # From haves to wants you convert with 1/ask and the taker fee (0.26%)
    # Example: Asset pair XXBTZUSD, base=have XBT, quote=want USD, conversion: 1 XBT -> 5000 USD, "selling" XBT for USD, so you are the "maker"
    # conversions = [bid * (1. - 0.0025) for bid in bids]
    # conversions.extend([(1. - 0.0025)/ask for ask in asks])
    conversions = [bid * (1. - 0.0025) for bid in bids]
    conversions.extend([(1. - 0.0025)/ask for ask in asks])

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
        # 'order_volumes'     : order_volumes,
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




    # resp = (B.getbalances())
    # pprint.pprint(resp)
    # for r in resp:
    #     if r['Currency']=='BTC':
    #         volume2 = r['Available']
    #         print("VOLUME btc: ",volume2)

    # assetpair = 'BTC-ETH'
    # M = B.getmarketsummary(assetpair)



    # print('Ask: ',M[0]['Ask'])
    # print('Bid: ',M[0]['Bid'])

    # ask = M[0]['Ask']*(1-0.001)
    # bid = M[0]['Bid']*(1+0.001)

    # print('Ask: ',ask)
    # print('Bid: ',bid)


    # # sys.exit()

    # t0=datetime.datetime.now()

    # volume1 = 15/300.0
    # # volume2 = 13/300.0
    
    # print('buying')
    # resp = B.buylimit(assetpair,volume1,bid)
    # pprint.pprint(resp)

    # uuid = None
    # if 'uuid' in resp:
    #     uuid = resp['uuid']
    # else:
    #     print('No UUID')
    #     sys.exit()

    # # avail = 0.0
    # # while avail==0.0:
    # #     resp = (B.getbalances())
    # #     for r in resp:
    # #         if r['Currency']=='ETH':
    # #             volume2 = r['Available']
    # #             print("VOLUME eth: ",volume2)
    # #             avail = float(volume2)

    # print('selling')

    # resp = 'INSUFFICIENT_FUNDS'
    # count = 0
    # while resp=='INSUFFICIENT_FUNDS':
    #     resp = B.selllimit(assetpair,volume1,ask)
    #     # resp = B.getorder('80210115-0b95-470a-a090-4040213e9f72')
    #     pprint.pprint(resp)
    #     if count>8:
    #         B.cancel(uuid)
    #         print('cancelled')
    #         break
    #     count+=1

    # # avail = 0.0
    # # while avail==0.0:
    # #     resp = (B.getbalances())
    # #     for r in resp:
    # #         if r['Currency']=='BTC':
    # #             volume2 = r['Available']
    # #             print("VOLUME btc: ",volume2)
    # #             avail = float(volume2)



    # t1= datetime.datetime.now()
    # print("Time: %.4f" %((t1-t0).total_seconds()))
    
    # resp = (B.getbalances())
    # print(resp)
    # for r in resp:
    #     if r['Currency']=='BTC':
    #         volume2 = r['Available']
    #         print("VOLUME btc: ",volume2)

    # sys.exit()

    count = 0
    while True:
        
        try:
            if count%100==0:
                t0 = datetime.datetime.now()
                asset_pairs_dict = B.getmarkets()
                t1 = datetime.datetime.now()
                print("Asset Dictionary Response Time: %.4f" %((t1-t0).total_seconds()))
            # try:
            exchange_data = get_prices(B,asset_pairs_dict)
            # except Exception as e:
            #     print(e)
            #     time.sleep(5)
            #     continue    

            # Loop over the assets and make a list
            asset_list = []
            for asset in exchange_data['unique']:

                # Make an instance of the Asset class with that asset's name
                exec(asset + '= Asset(exchange_data,\'' + asset + '\')')

                # Append the Asset instance to the list
                asset_list.append(eval(asset))

            trial_list = []

            for asset in asset_list:
                if asset.name in ['BTC']:
                    # print(asset.name, asset.avail_trades)
                    trial_list.append(asset)
                # if asset.name=='XETH':
                #     trial_list.append(asset)

            
            # trial_list = asset_list
            master_path = PathList(asset_list,trial_list)
            # print("god help us")
            t0 = datetime.datetime.now()
            for i in range(0,3):
                master_path.step()
            t1 = datetime.datetime.now()
            print("Path Build Time: %.4f" %((t1-t0).total_seconds()))

            master_path.show_paths()
            best_path = master_path.return_best()

            count+=1
        except Exception as e:
            time.sleep(5)









