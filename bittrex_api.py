#!/usr/bin/env python
#import urllib
#import urllib2
from urllib.parse import urlencode
import urllib.request
import json
import time
import hmac
import hashlib

from io import StringIO, BytesIO
import pycurl

class BittrexAPI(object):
    
    def __init__(self,key_filename):


        self.key = None
        self.secret = None
        self.public = ['getmarkets', 'getcurrencies', 'getticker', 'getmarketsummaries', 'getmarketsummary', 'getorderbook', 'getmarkethistory']
        self.market = ['buylimit', 'buymarket', 'selllimit', 'sellmarket', 'cancel', 'getopenorders']
        self.account = ['getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorder', 'getorderhistory', 'getwithdrawalhistory', 'getdeposithistory']
    
        self.load_key(key_filename)


    def load_key(self, path):
        """ Load key and secret from file.

        Expected file format is key and secret on separate lines.

        :param path: path to keyfile
        :type path: str
        :returns: None

        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
        return

    
    def query(self, method, values={}):
        if method in self.public:
            url = 'https://bittrex.com/api/v1.1/public/'
        elif method in self.market:
            url = 'https://bittrex.com/api/v1.1/market/'
        elif method in self.account: 
            url = 'https://bittrex.com/api/v1.1/account/'
        else:
            return 'Something went wrong, sorry.'
        
        url += method + '?' + urlencode(values)
        
        if method not in self.public:
            url += '&apikey=' + self.key
            url += '&nonce=' + str(int(time.time()))
            signature = hmac.new(self.secret.encode(), url.encode(), hashlib.sha512).hexdigest()
            headers = {'apisign': signature}

            #for curl
            str_h = '%s: %s'%('apisign',headers['apisign'])
            h = [  str_h  ]
        else:
            h = []
            headers = {}
        
        if True:
            req = urllib.request.Request(url, headers=headers)
            response = json.loads(urllib.request.urlopen(req).read())

        else:
            e = BytesIO()
            c = pycurl.Curl()
            c.setopt(pycurl.URL, url)
            # c.setopt(pycurl.GET,1)
            c.setopt(c.HTTPHEADER, h)
            # c.setopt(c.HTTPHEADER, ['Accept: text/html', 'Accept-Charset: UTF-8'])
            # c.setopt(c.WRITEFUNCTION, buffer.write)
            c.setopt(pycurl.WRITEFUNCTION, e.write)
            c.perform()
            c.close()
            response = json.loads(e.getvalue())


        if response["result"]:
            return response["result"]
        else:
            return response["message"]
    
    
    def getmarkets(self):
        return self.query('getmarkets')
    
    def getcurrencies(self):
        return self.query('getcurrencies')
    
    def getticker(self, market):
        return self.query('getticker', {'market': market})
    
    def getmarketsummaries(self):
        # This call takes around .14 seconds
        return self.query('getmarketsummaries')
    
    def getmarketsummary(self, market):
        return self.query('getmarketsummary', {'market': market})
    
    def getorderbook(self, market, type, depth=10):
        #This takes about .25 - .4 seconds. 
        return self.query('getorderbook', {'market': market, 'type': type, 'depth': depth})
    
    def getmarkethistory(self, market, count=20):
        return self.query('getmarkethistory', {'market': market, 'count': count})
    
    def buylimit(self, market, quantity, rate):
        return self.query('buylimit', {'market': market, 'quantity': quantity, 'rate': rate})
    
    def buymarket(self, market, quantity):
        return self.query('buymarket', {'market': market, 'quantity': quantity})
    
    def selllimit(self, market, quantity, rate):
        return self.query('selllimit', {'market': market, 'quantity': quantity, 'rate': rate})
    
    def sellmarket(self, market, quantity):
        return self.query('sellmarket', {'market': market, 'quantity': quantity})
    
    def cancel(self, uuid):
        return self.query('cancel', {'uuid': uuid})
    
    def getopenorders(self, market):
        return self.query('getopenorders', {'market': market})
    
    def getbalances(self):
        return self.query('getbalances')
    
    def getbalance(self, currency):
        return self.query('getbalance', {'currency': currency})
    
    def getdepositaddress(self, currency):
        return self.query('getdepositaddress', {'currency': currency})
    
    def withdraw(self, currency, quantity, address):
        return self.query('withdraw', {'currency': currency, 'quantity': quantity, 'address': address})
    
    def getorder(self, uuid):
        return self.query('getorder', {'uuid': uuid})
    
    def getorderhistory(self, market, count):
        return self.query('getorderhistory', {'market': market, 'count': count})
    
    def getwithdrawalhistory(self, currency, count):
        return self.query('getwithdrawalhistory', {'currency': currency, 'count': count})
    
    def getdeposithistory(self, currency, count):
        return self.query('getdeposithistory', {'currency': currency, 'count': count})



