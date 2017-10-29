#!/usr/bin/env python3

# This file is part of krakenex.
# Licensed under the Simplified BSD license. See `examples/LICENSE.txt`.

# Pretty-print a pair's order book depth.

import krakenex
import sys
import pprint



class BrittCoinMiner(object):

	def __init__(self):

		self.k = krakenex.API()

		self.assets = self.k.query_public('Assets')
		self.asset_pairs = self.k.query_public('AssetPairs')

	def generate_asset_objects(self):

		asset_pair_list = list(self.asset_pairs['result'].keys())
		for asset_pair in asset_pair_list:


class AssetPair(object):
	def __init__(self):

		self.base = '' #From currency
		self.quote = '' #To currency

		self.from_base = 0.0
		self.to_base = 1.0/self.from_base




if __name__ == '__main__':

	brittcoin = BrittCoinMiner()
	brittcoin.generate_asset_objects()



sys.exit()


k = krakenex.API()

# r_assets = k.query_public('Assets')

# pprint.pprint(r_assets)

r_asset_pairs = k.query_public('AssetPairs')

# pprint.pprint(r_asset_pairs)
# sys.exit()

if len(r_asset_pairs['error'])!=0:
	print(r_asset_pairs['error'])
	sys.exit

keys = list(r_asset_pairs['result'].keys())

# for pair in keys:
# 	pprint.pprint(pair)

q_str = ''
N = 10
for i in range(0,N):
	q_str+=keys[i]
	if i<N-1:
		q_str+=','

print(q_str)

# r_price_data = k.query_public('Ticker', {'pair': q_str} )

r_price_data = k.query_public('Ticker', {'pair': 'XBTUSD,ETHXBT'} )



# response = k.query_public('Depth', {'pair': 'XXBTZUSD', 'count': '10'})
pprint.pprint(r_price_data)
