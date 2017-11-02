import krakenex
import sys
import pprint
import numpy as np
from copy import deepcopy
import time


class Trader(object):
    def __init__(self,nodes,links,directions,pairs, vol_currency_list):

        self.nodes = nodes
        self.links = links
        self.directions = directions
        self.asset_pairs= pairs
        self.vol_currency_list = vol_currency_list

        self.k = krakenex.API()
        self.k.load_key('kraken_key.key')

        self.avail_bal = 0


    def get_volume(self, volume_to_trade, i , vol_currency):
        

        for k in range(0,i):
            volume_to_trade*=self.links[k]
        currency = self.nodes[i]

        if vol_currency!=currency:
            volume_to_trade*=self.links[i]

        return float(volume_to_trade)

    def adjust_balance(self, volume_i, volume_currency):
        avail_bal = self.check_balance(volume_currency)
        self.avail_bal =avail_bal
        diff = abs(1-avail_bal/volume_i)

        #If we are close but low, sell it all. 
        if volume_i<=avail_bal and diff<0.07:
            return avail_bal
        #close but too high, sell what we have.
        if volume_i>avail_bal and diff<0.06:    
            return avail_bal

        #avail balance too low. Maybe the old order hasnt gone through yet??
        if volume_i>avail_bal:
            return False

        #Hopefully this is a valid number...
        return volume_i



    def execute_path(self, volume_to_trade):

        start_bal = self.check_balance(self.vol_currency_list[0])
        print('Starting Balance: %s' %(start_bal))

        if volume_to_trade>start_bal:
            print('Not Enough Initial Currency')
            return False

        # current_trade_spec = {'vtt':volume_to_trade, 'curr':self.vol_currency[0]} #use this to track the current volume (vtt) of currency (curr)

        for i in range(0,len(self.asset_pairs)):

            start = self.nodes[i]
            end = self.nodes[i+1]
            buyorsell = self.directions[i]
            conversion = self.links[i]
            pair = self.asset_pairs[i]
            vol_currency = self.vol_currency_list[i]

                        #check to make sure we have enough coin

            #convert the currency to what we need.
            volume_required = self.get_volume(volume_to_trade,i,start)

            print(volume_required)
            #try to validate the volume. 
            volume_required = self.adjust_balance(volume_required, vol_currency)

            #if volume_i is false, we need to wait for more balance or fuck off. 
            count = 0
            while volume_required==False:
                print("Waiting for balance to arrive...")
                volume_required = self.adjust_balance(volume_required, vol_currency)
                count+=1
                if count>15:
                    return False

            volume_execute = self.get_volume(volume_required,0,vol_currency)



            print('Volume Currency: %s,  Trading Volume: %s  direction: %s' %(vol_currency, volume_execute, buyorsell))

            #Execute the fucking trade
            txid = self.execute_trade(pair,buyorsell,volume_execute)

            #Now error check... 
            if txid in [-1,False]:
                print("Trade errored out. Have fun with your shitcoin: %s" %(vol_currency))
                break

            if txid==555: #Most likely a timeout. Wait until your currency is gone from the 'start' currency. 
                print("Warning 555: Will have to wait to see if the currency arrives for the next trade.")

                count=0
                while count<50:
                    after_bal = self.check_balance(vol_currency)
                    if after_bal<self.avail_bal:
                        break
                    count+=1
                if count>49:
                    print("Your shitcoin (%s) probably didnt leave your shitcoin wallet" %(vol_currency))
                    break


        end_bal = self.check_balance(self.vol_currency_list[-1])
        print("Ending Balance: %s   Profit: %s" %(end_bal, (end_bal/start_bal) ))

        return end_bal>start_bal







    def execute_trade( self, pair, buyorsell , volume ):
        trade_info = {  'pair':pair,
                        'type':buyorsell,
                        'ordertype':'market',
                        'volume': volume,
                        'validate':True
                    }
        print('Starting Order %s: %s  vol: %s' %(buyorsell,pair,volume))
        try:
            new_order = self.k.query_private('AddOrder', trade_info )
            pprint.pprint(new_order)
        except Exception as e:
            print('ERROR:',e)
            return 555 # See if it went through...

        if len(new_order['error'])>0:
            self.handle_error(new_order['error'])
            return False

        txid = -1
        # txid = 'O435WC-WHEN6-AQX5JT'
        if 'txid' in new_order['result']:
            txid = new_order['result']['txid'] 
            print(txid)
        return txid



    def check_balance(self, asset):
        # print(asset)
        balance = self.k.query_private('Balance')
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


    Nodes=['XXBT','ZUSD','XXRP','XXBT']  
    Directions= ['sell','buy', 'sell'] 
    Links = [1/6000.0, 2.0, 1.0/100, 6.0]
    Pairs= ['XXBTZUSD', 'XXRPZUSD', 'XXRPXXBT']
    VolC = ['XXBT', 'XXRP' , 'XXRP']

    t = Trader(Nodes,Links,Directions,Pairs, VolC)
    t.execute_path(0.003)

    sys.exit()