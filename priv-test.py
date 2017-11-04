# import krakenex
# import sys
# import pprint
# import numpy as np
# from copy import deepcopy
# import time


# class Trader(object):
#     def __init__(self,nodes,links,directions,pairs):

#         self.nodes = nodes
#         self.links = links
#         self.directions = directions
#         self.asset_pairs= pairs

#         self.k = krakenex.API()
#         self.k.load_key('kraken_key.key')


#     def execute_path(self, volume):

#         start_bal = self.check_balance(self.nodes[0])
#         print('Starting Balance: %s' %(start_bal))

#         for i in range(0,len(self.asset_pairs)):
#             start = self.nodes[i]
#             end = self.nodes[i+1]
#             buyorsell = self.directions[i]
#             conversion = self.links[i]
#             pair = self.asset_pairs[i]
#             #check to make sure we have enough coin
#             # ETHXBT
#             # XBT -> ETH = buy -> backward. pay with END
#             # ETH -> XBT = sell -> forward. pay with START

#             print(buyorsell)

#             if buyorsell=='sell':
#                 volume_currency = start
#                 avail_bal = self.check_balance(start)
#                 volume = avail_bal
#             elif buyorsell=='buy':
#                 volume_currency = end
#                 avail_bal = self.check_balance(start)
#                 volume = avail_bal*conversion

#             print('Volume Currency: %s,  Trading Volume: %s' %(volume_currency, volume))

#             # sys.exit()
#             # if avail_bal<volume:
#             #     print("WARNING: NOT ENOUGH VOLUME in: %s  avail: %s" %(volume,volume_currency))

#             #Execute the fucking trade
#             txid = self.execute_trade(pair,buyorsell,volume)
#             if txid in [-1,False]:
#                 print("Trade errored out. Have fun with your shitcoin: %s" %(volume_currency))
#                 # break

#             if txid==555: #Most likely a timeout. Wait until your currency is gone from the 'start' currency. 
#                 print("Warning 555: Will have to wait to see if the currency arrives for the next trade.")

#                 count=0
#                 while count<50:
#                     after_bal = self.check_balance(volume_currency)
#                     if after_bal<avail_bal:
#                         break
#                     count+=1
#                 if count>49:
#                     print("Your shitcoin (%s) probably didnt leave your shitcoin wallet" %(volume_currency))
#                     break


#         end_bal = self.check_balance(self.nodes[-1])
#         print("Ending Balance: %s   Profit: %s" %(end_bal, (end_bal/start_bal) ))

#         return end_bal>start_bal

#     def execute_trade( self, pair, buyorsell , volume ):
#         trade_info = {  'pair':pair,
#                         'type':buyorsell,
#                         'ordertype':'market',
#                         'volume': volume,
#                         'validate':True
#                     }
#         print('Starting Order %s: %s  vol: %s' %(buyorsell,pair,volume))
#         try:
#             new_order = self.k.query_private('AddOrder', trade_info )
#             pprint.pprint(new_order)
#         except Exception as e:
#             print('ERROR:',e)
#             return 555 # See if it went through...

#         if len(new_order['error'])>0:
#             self.handle_error(new_order['error'])
#             return False

#         txid = -1
#         # txid = 'O435WC-WHEN6-AQX5JT'
#         if 'txid' in new_order['result']:
#             txid = new_order['result']['txid'] 
#             print(txid)
#         return txid

#     def check_balance(self, asset):
#         balance = self.k.query_private('Balance')
#         # pprint.pprint(balance)
#         asset_bal = float(balance['result'][asset])
#         # print('Asset: %s Balance: %s' %(asset,asset_bal))
#         return asset_bal

#     def is_order_closed(self, txid):

#         if txid in [-1,False]:
#             return None

#         order_stat = self.k.query_private('QueryOrders', {'txid':txid})
#         pprint.pprint(order_stat)

#         if 'result' in order_stat:
#             return order_stat['result'][txid]['status']=='closed'
#         else:
#             return None

#     def handle_error(self,error):
#         print('HANDLE ERROR: %s' %(error))




# if __name__ == '__main__':



#     # prepare request
#     # req_data = {'docalcs': 'true'}

#     # querry servers
#     # start = k.query_public('Time')
#     # open_positions = k.query_private('OpenPositions', req_data)
#     # end = k.query_public('Time')
#     # latency = (end['result']['unixtime']-start['result']['unixtime'])
#     # print(open_positions)


# # Nodes: XXBT,XZEC,ZEUR,XXBT  Percent: 99.932204  Dir: ['buy', 'sell', 'buy']  Pairs: ['XZECXXBT', 'XZECZEUR', 'XXBTZEUR'] Links: 


#     Nodes=['XXBT','XZEC','ZEUR','XXBT']  
#     Directions= ['buy', 'sell', 'buy'] 
#     Links = [27.875908328675237, 197.6832, 0.00018134545454545455]
#     Pairs= ['XZECXXBT', 'XZECZEUR', 'XXBTZEUR']

#     t = Trader(Nodes,Links,Directions,Pairs)
#     t.execute_path(0.003)

#     sys.exit()


    asset = 'XETH'
    asset_pair = 'XETHXXBT'
    order_dir = 'buy'  #buy or sell
    order_type = 'market'
    volume = 0.021

    while True:
        check_balance(asset)
    # time.sleep(1)
    print(datetime.datetime.now().isoformat())
    txid = execute_trade(asset_pair,order_dir,volume)
    print(datetime.datetime.now().isoformat())
    # is_order_closed(txid)

    while True:
        m = k.query_private('OpenOrders')
        pprint.pprint(m)
        time.sleep(1)



    time.sleep(1)

    # check_balance(asset)










    sys.exit()





    
    txid = 'O435WC-WHEN6-AQX5JT'
    #txid = new_order['result']['txid']

    #query that order
    order_stat = k.query_private('QueryOrders', {'txid':txid})
    pprint.pprint(order_stat)


    private_options = ['Balance','TradeBalance','OpenOrders','ClosedOrders','QueryOrders','TradesHistory','QueryTrades','OpenPositions','TradeVolume']




    # pprint.pprint(k.query_private('TradeVolume', {'pair':'XICNXETH'} ))
    sys.exit()










    b = 0
    c = 0
    for i in open_positions['result']:
        order = open_positions['result'][i]
        if(order['pair']=='XETHZUSD'):
            b += (float(order['vol']))
        if (order['pair'] == 'XXBTZUSD'):
            c += (float(order['vol']))

    print('error count: ' + str(len(open_positions['error'])))
    print('latency: ' + str(latency))
    print('total open eth: ' + str(b))
    print('total open btc: ' + str(c))
    print('total open positions: ' + str(len(open_positions['result'])))


    # info_dict = {}

    # k.query_private('AddOrder', info_dict)

    # ['BCHEUR', 'BCHUSD', 'BCHXBT', 'DASHEUR', 'DASHUSD', 'DASHXBT', 
    # 'EOSETH', 'EOSXBT', 'GNOETH', 'GNOXBT', 'USDTZUSD', 'XETCXETH', 
    # 'XETCXXBT', 'XETCZEUR', 'XETCZUSD', 'XETHXXBT', 'XETHXXBT.d', 
    # 'XETHZCAD', 'XETHZCAD.d', 'XETHZEUR', 'XETHZEUR.d', 'XETHZGBP', 
    # 'XETHZGBP.d', 'XETHZJPY', 'XETHZJPY.d', 'XETHZUSD', 'XETHZUSD.d', 
    # 'XICNXETH', 'XICNXXBT', 'XLTCXXBT', 'XLTCZEUR', 'XLTCZUSD', 
    # 'XMLNXETH', 'XMLNXXBT', 'XREPXETH', 'XREPXXBT', 'XREPZEUR', 
    # 'XXBTZCAD', 'XXBTZCAD.d', 'XXBTZEUR', 'XXBTZEUR.d', 'XXBTZGBP', 
    # 'XXBTZGBP.d', 'XXBTZJPY', 'XXBTZJPY.d', 'XXBTZUSD', 'XXBTZUSD.d', 
    # 'XXDGXXBT', 'XXLMXXBT', 'XXMRXXBT', 'XXMRZEUR', 'XXMRZUSD', 
    # 'XXRPXXBT', 'XXRPZEUR', 'XXRPZUSD', 'XZECXXBT', 'XZECZEUR', 'XZECZUSD']
