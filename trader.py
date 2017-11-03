import krakenex
import sys
import pprint
import numpy as np
from copy import deepcopy
import time


class TraderEngine(object):
    ''' 
    Main class used to execute a series of orders. 
    Currently specific to Kraken.
    '''
    def __init__(self,nodes,conversions,order_actions,pair_names, order_vol_denoms):

        # 
        self.nodes         = nodes          # Currency nodes that this path will move through
        self.conversions   = conversions    # Conversion ratios between nodes along the length of the trade
        self.order_actions = order_actions  # 'buy' or 'sell'
        self.pair_names    = pair_names     # Names of the currency pair that will actually trade on the exchange
        self.order_vol_denoms = order_vol_denoms # Name of the currency that the volume must be listed in to order on this legs asset pair
        
        #Here is the kraken API with
        self.k = krakenex.API()
        self.k.load_key('kraken_key.key')

        # Parameters
        self.volume_snap_percentage = 7.0/100


        # Storage Variables:
        self.avail_bal = 0 # What the available balance of the current base currency. 


    def get_volume(self, volume_to_trade, i , currency):
        '''
        This function will convert the volume_to_trade variable into the curency to be used for the next trade. 
        volume_to_trade: volume of the original currency that the path started with, node[0]
        i: index along the path (0 is the first trade, 1 is the second)
        currency: Currency that you are converting the volume_to_trade into. 
        '''

        #Step along to the current trade index i, converting the volume along the way. 
        for k in range(0,i):
            volume_to_trade*=self.conversions[k]
        new_currency = self.nodes[i] #What currency is the current volume_to_trade in.

        #The currency you want to output the volume in might be one step futher, depending on the asset-pair and trade direction. 
        # Check this, and move the conversion one step further if necessary. 
        if currency!=new_currency:
            volume_to_trade*=self.conversions[i]

        return float(volume_to_trade)


    def adjust_balance(self, volume_i, volume_currency):
        '''
        This function will adjust the volume of an upcoming trade to mitigate
        residual currency being left behind, or the trade failing becaues there is not quite 
        enough currency available to trade. 
        volume_i: the volume of the currency intended for trade index i in volume_currency
        volume_currency: what currency the volume_i is listed in. This should be node[i]
        '''

        #Check the balance of the intended currency:
        avail_bal = self.check_balance(volume_currency)

        #Store this available balance for access later
        self.avail_bal = avail_bal

        #Calculate the ratio between the volume and balance.
        diff = abs(1-(avail_bal/volume_i))

        #If the volume inteded is close but would leave some residual, sell it all. 
        if volume_i<=avail_bal and diff<self.volume_snap_percentage:
            return avail_bal
        #If the volume is close but too high, sell what we have.
        if volume_i>avail_bal and diff<self.volume_snap_percentage:    
            return avail_bal

        #avail balance too low. Maybe the old order hasnt gone through yet??
        if volume_i>avail_bal:
            return False

        # Else: volume is less than the available balance, so use the intended volume. 
        return volume_i



    def execute_path(self, volume_to_trade):
        '''
        Main function that will execute a path of assets. 
        Input volume_to_trade is the amount of the first/last currency that you want to put through the path. 
        ex: BTC->ETH->USD->BTC, you would input volume in BTC. 
        '''

        # First check if we have enough balance to initiate this path. Also track this to see the profit at the end. 
        start_balance = self.check_balance(self.nodes[0])
        print('Starting Balance of %s:  %s' %(self.nodes[0], start_balance))

        #Kick us out if we dont have enough currency to push through. 
        if volume_to_trade>start_balance:
            print('Not Enough Initial Currency')
            return False

        # Main loop to execute all of the trades. 
        for i in range(0,len(self.pair_names)):

            #Unpack some variables to make life a bit easier:
            start       = self.nodes[i]             # What this order will start with (currency)
            end         = self.nodes[i+1]           # What this order will end with (currency)
            buyorsell   = self.order_actions[i]     # 'buy' or 'sell' 
            conversion  = self.conversions[i]       # The conversion for this step 
            pair        = self.pair_names[i]        # Asset pair that we are going to use
            vol_denom   = self.order_vol_denoms[i]  # Units that the volume has to be input via

            print("\n== STARTING PATH INDEX: %i  Start: %s   End: %s ==" %(i, start, end))

            #Volume required = amount you need to have in your account to complete this trade of 'start' currency. 
            volume_required = self.get_volume(volume_to_trade,i,start)
            print('Requires: ',volume_required,' of Currency: ',vol_denom)

            # Adjust the volume as necessary to prevent errors or extra currency being left behind 
            volume_adjusted = self.adjust_balance(volume_required, start)

            # if volume_adjusted is false, we need to wait for more balance or fuck off. 
            # This will wait to see if balance ever arrives from the last order (this will only be an applicable for i>0)
            count = 0
            while volume_adjusted==False:
                print("Waiting for balance to arrive...")
                time.sleep(1)
                volume_adjusted = self.adjust_balance(volume_required, vol_denom)
                count+=1
                if count>15:
                    return False

            #If we got this far, the volume_adjusted is the amount that you need of the start currency
            volume_required = volume_adjusted

            #volume execute is in denominations of the order_vol_denom, which is used for the order execution. 
            volume_execute = self.get_volume(volume_required,0,vol_denom)
            print('Volume Currency: %s,  Trading Volume: %s,  Oper: %s' %(vol_denom, volume_execute, buyorsell))

            # Time for the magical moment:
            # Execute the fucking trade
            # txid is a unique order ID number.
            txid = self.execute_trade(pair,buyorsell,volume_execute)
            # If the order goes through properly, it will return a long character string that is the order ID. 
            # If the order fails out for some reason, it will return and error code. 

            #Now error check... 
            if txid in [222,333]:
                # Not much else you can do here. 
                print("Trade errored out. Have fun with your shitcoin: %s" %(start))
                break

            if txid==111: #Most likely a timeout. 
                #Try waiting until your currency is gone from the 'start' currency. 
                #We dont have a TXID, so we cant check the order status...
                #If you got here, it probably went through though.
                print("Warning 111: Will have to wait to see if the currency arrives for the next trade.")
                count=0
                while count<20:
                    after_bal = self.check_balance(start)
                    time.sleep(1)
                    print("Waiting for balance to leave...")
                    if after_bal<self.avail_bal:
                        break
                    count+=1
                if count>49:
                    print("Your shitcoin (%s) probably didnt leave your shitcoin wallet" %(start))
                    break

            #Time to execute the next one...


        #See what happened after all of the orders went through...
        end_bal = self.check_balance(self.nodes[-1])
        print("Ending Balance: %s   Profit: %s" %(end_bal, (end_bal/start_balance) ))

        #return true or false...
        return end_bal>start_balance







    def execute_trade( self, pair, buyorsell , volume ):
        trade_info = {  'pair':pair,
                        'type':buyorsell,
                        'ordertype':'market',
                        'volume': volume,
                        # 'validate':True
                    }
        print('Starting Order %s: %s  vol: %s' %(buyorsell,pair,volume))
        try:
            new_order = self.k.query_private('AddOrder', trade_info )
            pprint.pprint(new_order)
        except Exception as e:
            print('ERROR:',e)
            return 111 # See if it went through...

        if len(new_order['error'])>0:
            self.handle_error(new_order['error'])
            return 222

        txid = 333
        # txid = 'O435WC-WHEN6-AQX5JT'
        if 'txid' in new_order['result']:
            txid = new_order['result']['txid'] 
            print(txid)
        return txid



    def check_balance(self, asset):
        try:
            balance = self.k.query_private('Balance')
        except Exception as e:
            print('Check Balance Errored Out: ',e)
            return None    
        # pprint.pprint(balance)
        if asset in balance['result']:
            asset_bal = float(balance['result'][asset])
            return asset_bal
        else:
            return 0.0

    def is_order_closed(self, txid):

        if txid in [-1,False]:
            return None

        order_stat = self.k.query_private('QueryOrders', {'txid':txid})
        pprint.pprint(order_stat)

        if 'result' in order_stat:
            return order_stat['result'][txid]['status']=='closed'
        else:
            return None

    def handle_error(self,error):
        print('HANDLE ERROR: %s' %(error))




if __name__ == '__main__':



    # prepare request
    # req_data = {'docalcs': 'true'}

    # querry servers
    # start = k.query_public('Time')
    # open_positions = k.query_private('OpenPositions', req_data)
    # end = k.query_public('Time')
    # latency = (end['result']['unixtime']-start['result']['unixtime'])
    # print(open_positions)


# Nodes: XXBT,XZEC,ZEUR,XXBT  Percent: 99.932204  Dir: ['buy', 'sell', 'buy']  Pairs: ['XZECXXBT', 'XZECZEUR', 'XXBTZEUR'] Links: 


    Nodes= ['XXBT', 'XETH', 'ZUSD', 'XXBT'] 
    Percent= 99.670121 
    Directions= ['buy', 'sell', 'buy'] 
    Pairs= ['XETHXXBT', 'XETHZUSD', 'XXBTZUSD'] 
    Links= [23.380215658696674, 289.7856, 0.00014710914454277286] 
    VolC= ['XETH', 'XETH', 'XXBT'] 

    t = TraderEngine(Nodes,Links,Directions,Pairs, VolC)
    result = t.execute_path(0.003)

    if result:
        print("\nMADE MONEY\n")
    else:
        print("\nLOST MONEY\n")

    sys.exit()