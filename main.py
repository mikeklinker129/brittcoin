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

        self.assets_response = self.k.query_public('Assets')
        self.asset_pairs_response = self.k.query_public('AssetPairs')

        self.asset_pairs_list = [] # List of asset pair objects
        self.asset_list = []
        self.trees_list = []


        self.generate_asset_pair_objects()
        self.generate_asset_objects()


    def generate_asset_pair_objects(self):


        #First make the asset parts response into asset pairs objects to make them easier to manipulate
        name_list = list(self.asset_pairs_response['result'].keys())
        for ap in name_list:
            if '.d' in ap:
                continue #I DONT KNOW WHY THE .d IS INCLUDED YET!
            # print(ap)    
            ap_object = AssetPair(ap,self.asset_pairs_response['result'][ap])
            self.asset_pairs_list.append(ap_object)

        #Now lets request the prices. 
        query_str = ''
        for ap in self.asset_pairs_list:
            query_str+=ap.pair_name+','
        #remove the comma at the end of the string
        query_str = query_str[0:len(query_str)-1]
        # print(query_str)

        r_price_data = self.k.query_public('Ticker', {'pair': query_str} )

        for ap in self.asset_pairs_list:

            try:
                last_trade = r_price_data['result'][ap.pair_name]['c'][0]
                # print(ap.pair_name,last_trade)
                ap.from_base = float(last_trade)
                ap.to_base = 1.0/float(last_trade)

            except Exception as e:
                print('removing: ',ap.pair_name,' because ',e)
                self.asset_pairs_list.remove(ap) #hope this works... if the asset pair doesnt show up in the ticker, get rid of it. 

        #Now all of the asset pair objects have price information
        # We can return now. 

    def generate_asset_objects(self):
        #Loop through the asset pairs list. 
        for ap in self.asset_pairs_list:
            #check to see if this asset already exists. 
            asset_exists = False
            for asset in self.asset_list:
                if asset.name==ap.base or asset.name==ap.quote:
                    asset_exists = True
                    break

            # If the asset does not exist, make a shell asset object. Will be filled in later. 
            if not asset_exists:
                





    def initialize_trees(self):

        for ap in self.asset_list:

            at = AssetTree(self,ap)
            self.trees_list.append(at)

        #done. 









class AssetTree(object):
    def __init__(self,parent_class,first_node):
        self.parent = parent_class      #This is BrittCoinMiner, so this object can add trees to the master list. 

        self.tree_node = [first_node]   #list of the nodes in this specific tree
        self.tree_link = []             #price information for each transition from node to node.



    def is_finished(self): 
        if self.tree_node[0]==self.tree_node[-1]: #if the start equals the end...
            return True
        else:
            return False

    def calc_profit(self):
        unit_profitability = 1 #if you send one unit through this tree, what comes out.
        for link in self.tree_link:
            unit_profitability=unit_profitability*link

        return unit_profitability




class Asset(object):
    ''' 
    This is the main asset type that the tree system will use. 
    It does not matter which exchange this asset came from, as long as the price information is correct.
    '''
    def __init__(self):

        self.name = '' #string of currency name
        self.avail_trades = [] #currencies this coin can be converted to
        self.avail_prices = [] #Parallel list to coin conversion
        self.exchange = ''


class AssetPair(object):
    def __init__(self,name,input_json):
        self.input_json = input_json

        self.base  = input_json['base']   #From currency
        self.quote = input_json['quote']  #To currency
        self.pair_name = name #Asset pair name from Kraken. These can include X's and other crap. 

        self.from_base = None
        self.to_base = None






if __name__ == '__main__':

    brittcoin = BrittCoinMiner()
    






