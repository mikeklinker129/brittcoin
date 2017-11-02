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
        self.avail_trades   = [] # Currencies this coin can be converted to
        self.conversions    = [] # Conversion ratios for each of the available trades (how much you will have of the new currency after trading)
        self.pair_names     = [] # Names of the currency pair you will actually trade on the exchange
        self.max_amounts    = [] # Max amount you can trade (the bid/ask size), in denomination of the asset
        self.exchange = 'Kraken'

        # Terms for actually placing the order
        self.order_actions      = [] # 'BUY' or 'SELL'
        self.order_volumes      = [] # Volume in terms of the website (for a digital to fiat trade, this is # digital coins)
        self.order_vol_denoms   = [] # Denominations of the order_volumes (for a digital to fiat trade, this is name of digital coins)
        self.order_prices       = [] # Price in terms of the website (for a digital to fiat trade, this is price in fiat currency)
        self.order_price_denoms = [] # Denominations of the order_prices (for a digital to fiat trade, this is name of fiat currency)

        # Find the trades involving "name"
        for i in range(kraken_data['N']): # Loop over the list of trades
            if kraken_data['haves'][i] == name: # If the base is "name"
                self.avail_trades.append(      kraken_data['wants'             ][i])
                self.conversions.append(       kraken_data['conversions'       ][i])
                self.pair_names.append(        kraken_data['pair_names'        ][i])
                self.max_amounts.append(       kraken_data['max_amounts'       ][i])
                self.order_actions.append(     kraken_data['order_actions'     ][i])
                self.order_volumes.append(     kraken_data['order_volumes'     ][i])
                self.order_vol_denoms.append(  kraken_data['order_vol_denoms'  ][i])
                self.order_prices.append(      kraken_data['order_prices'      ][i])
                self.order_price_denoms.append(kraken_data['order_price_denoms'][i])


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
    N = 0 # Number of pairs
    for pair_name, data in asset_pairs_dict.items():
        if not pair_name[-2:] == '.d': # Dont search "dark pool pairs" - only 50 BTC or more!
            pairs.append(pair_name)      # Append the name of the pair
            haves.append(data['base'])   # Append the currency that you have (referred to as the base in Kraken)
            wants.append(data['quote'])  # Append the curreny that you want (referred to as the quote in Kraken)
            N += 1

    # Dont need this anymore... get all this information from the "Depth" API call
    #
    # # Make a comma-separated string from the list of pair names
    # pair_string = ','.join(pairs)
    #
    # # Call the Kraken API to get all the conversion factors
    # conversion_dict = k.query_public('Ticker', {'pair': pair_string} )['result']
    #
    # # Get the asks and bids for each asset pair
    # asks = []
    # bids = []
    # for pair_name, data in conversion_dict.items():
    #     asks.append(float(data['a'][0]))
    #     bids.append(float(data['b'][0]))

    # Call the Kraken API to get all the asks and bids
    # Can only check "depth" for one pair at a time, loop over the pairs
    asks     = []
    bids     = []
    ask_vols = []
    bid_vols = []
    for i in range(N):
        # API Call
        depth_dict = k.query_public('Depth', {'pair': pairs[i], 'count': 1} )['result']
        # Get the information from the API dictionary
        asks.append(     float( depth_dict[pairs[i]]['asks'][0][0] ))
        bids.append(     float( depth_dict[pairs[i]]['bids'][0][0] ))
        ask_vols.append( float( depth_dict[pairs[i]]['asks'][0][1] ))
        bid_vols.append( float( depth_dict[pairs[i]]['bids'][0][1] ))

    # Volume denomination is the have (base) in Kraken, and stays the same regardless of trade direction
    order_vol_denoms = deepcopy(haves).extend(deepcopy(haves))

    # Price denomination is the want (quote) in Kraken, and stays the same regardless of trade direction
    order_price_denoms = deepcopy(wants).extend(deepcopy(wants))

    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction
    # Append the "wants" list to the end of the "haves" list, and vice versa
    wants.extend(deepcopy(haves))
    haves.extend(deepcopy(wants))

    # Create the actions (buy/sell) list
    # Going from a have to a want is a SELL in the Kraken nomenclature
    # Example: Asset pair XXBTZUSD, if you have XBT and want USD, you are selling XBT for USD
    order_actions =      ['SELL' for bid  in bids]
    order_actions.extend(['BUY' for asks in asks])

    # Create a conversions list
    # From wants to haves you convert with the bid and the maker fee (0.16%)
    # From haves to wants you convert with 1/ask and the taker fee (0.26%)
    # Example: Asset pair XXBTZUSD, base=have XBT, quote=want USD, conversion: 1 XBT -> 5000 USD, "selling" XBT for USD, so you are the "maker"
    conversions = [bid * (1. - 0.0016) for bid in bids]
    conversions.extend([(1. - 0.0026)/ask for ask in asks])

    # Create ask/bid price and volumes list
    # Use the same logic as the conversion list, start with list of bids, then extend by list of asks
    order_prices  = deepcopy(bids    ).extend(deepcopy(asks    ))
    order_volumes = deepcopy(bid_vols).extend(deepcopy(ask_vols))

    # You will need the pairs to place the order later. Just repeat it
    pairs.extend(deepcopy(pairs))

    # Make the max_amounts vector, which will be in the denomination of the Asset
    # Example: Think of XBT -> USD...
    max_amounts = deepcopy(bid_vols) # First half of vector is just the bid volume (e.g. 0.05 XBT)
    max_amounts.extend( [asks[i]*ask_vols[i] for i in range(N)] ) # Second half of the vector is ask*ask_vol
                                                                  # 6000 $/XBT * 0.05 XBT = $300

    # Double the length
    N = 2*N

    # Compile into a dictionary and return
    kraken_data = {
        'unique'            : list(set(haves)), # Unique currencies you have
        'pair_names'        : pairs,
        'haves'             : haves,
        'wants'             : wants,
        'conversions'       : conversions,
        'max_amounts'       : max_amounts,
        'order_actions'     : order_actions,
        'order_volumes'     : order_volumes,
        'order_vol_denoms'  : order_vol_denoms,
        'order_prices'      : order_prices,
        'order_price_denoms': order_price_denoms,
        'N'                 : N
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

