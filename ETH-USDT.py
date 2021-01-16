class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Bitfinex': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 10* 60
        self.options = {}
        # user defined class attribute
        self.last_type = 'sell'
        self.last_rsi_status = None
        self.last_ma_status = None
        self.close_price_trace = np.array([])
        self.UP = 1
        self.DOWN = 2
        self.ma_long = 13
        self.ma_short = 6
        self.first=0 
        self.spend=0

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    def calrsi(self):
        rsi_long = talib.RSI(self.close_price_trace, 6)[-1]
        rsi_short = talib.RSI(self.close_price_trace, 13)[-1]
        if np.isnan(rsi_short) or np.isnan(rsi_long)  :
            return None
        if  rsi_short >  rsi_long:
            return self.UP
        return self.DOWN
    # called every self.period
    def trade(self, information):


        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        # calculate current ma cross status
        cur_cross = self.calrsi()
        curma_cross = self.calrsi()
        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))

        if cur_cross is None:
            return []

        if self.last_rsi_status is None:
            self.last_rsi_status = cur_cross
            return []
        if self.last_ma_status is None:
            self.last_ma_status = cur_cross
            return []
        rsiup=(cur_cross == self.UP and self.last_rsi_status == self.DOWN ) or  talib.RSI(self.close_price_trace, 10)[-1]<30
        rsidown=(cur_cross == self.DOWN and self.last_rsi_status == self.UP) and talib.RSI(self.close_price_trace,10)[-1]>80
        maup=cur_cross == self.UP and self.last_ma_status == self.DOWN 
        madown=cur_cross == self.DOWN and self.last_ma_status == self.UP
        # cross up
        targetCurrency = pair.split('-')[0]  #BTC
        baseCurrency = pair.split('-')[1]  #USDT
        targetCurrency_amount = self['assets'][exchange][targetCurrency] 
        baseCurrency_amount = self['assets'][exchange][baseCurrency] 
        asset=targetCurrency_amount *close_price+baseCurrency_amount
        if(asset>66000or asset<48000):
            return [
                {
                    'exchange': exchange,
                    'amount':  targetCurrency_amount*-1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        if(self.first==0):
            amount=15000/ close_price 
            self.first=1
            return [
                {
                    'exchange': exchange,
                    'amount': amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }           
            ]
        if rsiup and maup:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_rsi_status = cur_cross
            self.last_ma_status = curma_cross
            baseCurrency_amount = self['assets'][exchange][baseCurrency] 
            amount=(baseCurrency_amount/close_price)*0.1
            return [
                {
                    'exchange': exchange,
                    'amount': amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif  rsidown and madown :
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_rsi_status = cur_cross
            self.last_ma_status = curma_cross
            targetCurrency_amount = self['assets'][exchange][targetCurrency] 
            self.spend=0
            return [
                {
                    'exchange': exchange,
                    'amount':  targetCurrency_amount*-0.1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_rsi_status = cur_cross
        self.last_ma_status = curma_cross
        return []
