import krakenex
import sys
import pprint
import numpy as np
from copy import deepcopy



class PathList():
    __init__(self, assets):
        self.path_list = []
        self.complete_paths = []
        self.initialize(assets)

    def initialize(self,asset_list):
    	for asset in asset_list:
    		new_path = Path( [asset] )  
    		self.path_list.append(new_path)

    
    def step(self):
        for path in self.path_list:

        	starting_nodes = list(path.node)
           	starting_links = list(path.links)
           	next_moves  = path.node[-1].avail_trades
           	next_prices = path.node[-1].avail_prices

           	self.path_list.remove(path)

           	# for move in next_moves:
           	for i in range(0,len(next_moves)):
           		move = next_moves[i]
           		link = next_prices[i]
               	new_path = Path(starting_nodes+[move], starting_links+[link])
               	self.path_list.append(new_path)

        self.remove_complete_paths()

    def remove_complete_paths(self):
    	for path in self.path_list:
    		if path.is_complete():
    			self.complete_paths.append(path)
    			self.path_list.remove(path)
    			if path.value>1:
    				print('maybe we will make some money MN: ',path.value)


class Path(object):
    def __init__(self,init_node, links = []):
        self.nodes = init_node # list of Asset objects
        self.links = links    # list of numbers that link each node
        self.value = product(self.link)  
        self.length = len(self.nodes)



    def is_complete(self):
    	if self.nodes[0]==self.nodes[-1]:
    		return True
    	else:
    		return False

    def print_path(self):
    	print("Nodes: %s  Value: %s" %(','.join(self.nodes), self.value ))
    # def __append__():
    #     check left, check right
    #     update value



if __name__ == '__main__':

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


    all_assets = []

    MasterPathList = PathList(all_assets)




























