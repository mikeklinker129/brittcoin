#!/usr/bin/env python3

# This file is part of krakenex.
# Licensed under the Simplified BSD license. See `examples/LICENSE.txt`.

# Pretty-print a pair's order book depth.

import krakenex
import sys
import pprint

k = krakenex.API()

r_asset_pairs = k.query_public('AssetPairs')

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

r_price_data = k.query_public('Ticker', {'pair': q_str})



# response = k.query_public('Depth', {'pair': 'XXBTZUSD', 'count': '10'})
pprint.pprint(r_price_data)
