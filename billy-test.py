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
    for pair_name, data in price_dict.items():
        prices.append(float(data['a'][0])) # Append the ask price (this is how you access it...)

    # Now we have lists of one-way exchanges
    # Complete the exchange lists by adding the other direction

    # Append the "quotes" list to the end of the "bases" list, and vice versa
    new_bases  = deepcopy(quotes)
    new_quotes = deepcopy(bases)
    new_prices = [1./price for price in prices] # New prices are the inverse prices

    bases.extend(new_bases)
    quotes.extend(new_quotes)
    prices.extend(new_prices)

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

    # Get the data from Kraken
    kraken_data = get_prices()

    # Loop over the assets and make a list
    asset_list = []
    for asset in kraken_data['unique']:
        # Make an instance of the Asset class with that asset's name
        exec(asset + '= Asset(kraken_data,\'' + asset + '\')')

        # Append the Asset instance to the list
        asset_list.append(eval(asset))
