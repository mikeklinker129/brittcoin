import krakenex
import sys
import pprint
import numpy as np
from copy import deepcopy

class Asset():
    '''
    This is the main asset type that the tree system will use.
    It does not matter which exchange this asset came from, as long as the price information is correct.
    '''
    def __init__(self, kraken_data, name):

        self.name = name # String of currency name
        self.avail_trades = [] # Currencies this coin can be converted to
        self.conversions  = [] # Parallel list to coin conversion
        self.pair_names   = [] # Names of the currency pair you will actually trade on the exchange
        self.actions      = [] # 'BUY' or 'SELL'
        self.max_amounts  = [] # Max amount you can trade (the bid/ask size), in denomination of the asset
        self.exchange = 'Kraken'

        # Find the trades involving "name"
        for i in range(kraken_data['N']): # Loop over the list of trades
            if kraken_data['haves'][i] == name: # If the base is "name"
                self.avail_trades.append(kraken_data['wants'][i])
                self.conversions.append(kraken_data['conversions'][i])

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
    for pair_name, data in asset_pairs_dict.items():
        if not pair_name[-2:] == '.d': # Dont search "dark pool pairs" - only 50 BTC or more!
            pairs.append(pair_name)      # Append the name of the pair
            haves.append(data['base'])   # Append the currency that you have (referred to as the base in Kraken)
            wants.append(data['quote'])  # Append the curreny that you want (referred to as the quote in Kraken)

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

    # Create the actions (buy/sell) list
    # Going from a have to a want is a SELL in the Kraken nomenclature
    # Example: Asset pair XXBTZUSD, if you have XBT and want USD, you are selling XBT for USD
    actions = ['SELL' for bid in bids]
    actions.extend(['BUY' for bid in bids])

    # Create a conversions list
    # From wants to haves you convert with the bid and the maker fee (0.16%)
    # From haves to wants you convert with 1/ask and the taker fee (0.26%)
    # Example: Asset pair XXBTZUSD, base=have XBT, quote=want USD, conversion: 1 XBT -> 5000 USD, "selling" XBT for USD, so you are the "maker"

    conversions = [bid * (1. - 0.0016) for bid in bids]
    conversions.extend([(1. - 0.0026)/ask for ask in asks])



    # Compile into a dictionary and return
    kraken_data = {
        'unique'     : list(set(haves)), # Unique currencies you have
        'haves'      : haves,
        'wants'      : wants,
        'conversions': conversions,
        'actions'    : actions,
        'N'          : len(haves)
    }

    return kraken_data


if __name__ == '__main__':

    # Get the data from Kraken
    kraken_data = get_prices()

    # Loop over the assets and make a list
    asset_list = []
    for asset in kraken_data['unique']:
        # Make an instance of the Asset class with that asset's name
        exec(asset + '= Asset(kraken_data,\'' + asset + '\')')

        # Append the Asset instance to the list
        asset_list.append(eval(asset))

