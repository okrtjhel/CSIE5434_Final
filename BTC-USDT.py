# Class name must be Strategy
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
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 10 * 60 #分鐘線
        self.options = {}

        # user defined class attribute
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.UP = 1
        self.DOWN = 2

        #可更改參數：
        self.cont = 1
        self.ma_long = 30  #定義長均線
        self.ma_short = 5  #定義短均線
        self.theta_percent = 80 #可以調整百分比的參數


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]

        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):
        #在哪個交易所
        exchange = list(information['candles'])[0]
        #哪個交易對
        pair = list(information['candles'][exchange])[0]
        #拿收盤價格，也可以拿開盤價格或是當下的交易量
        close_price = information['candles'][exchange][pair][0]['close']

        targetCurrency = pair.split('-')[0]  #BTC
        targetCurrency_amount = self['assets'][exchange][targetCurrency]
        baseCurrency = pair.split('-')[1]  #USDT
        baseCurrency_amount = self['assets'][exchange][baseCurrency]

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-(self.ma_long+1):]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        #Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(targetCurrency_amount) + ', pucket' + str(baseCurrency_amount))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # cross up
        if cur_cross == self.UP and self.last_cross_status == self.DOWN and self.close_price_trace[0] < self.close_price_trace[-1] and self.cont : #長期看漲
            self.last_cross_status = cur_cross
            # (這次 和 短線外1st 的價差) / 短線外1st價格
            theta = (self.close_price_trace[-1] - self.close_price_trace[-(self.ma_short+1)]) / self.close_price_trace[-(self.ma_short+1)]  
            # theta * 調整百分比
            theta *= self.theta_percent
            theta = (theta**2) 
            if theta>1:
                theta=1
            Log('percent' + str(theta*100))
            return [
                {
                    'exchange': exchange,
                    'amount': baseCurrency_amount/self.close_price_trace[-1] * theta,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif targetCurrency_amount > 0 and cur_cross == self.DOWN and self.last_cross_status == self.UP and self.close_price_trace[0] > self.close_price_trace[-1] and self.cont: #長期看跌
            self.last_cross_status = cur_cross
            # (這次 和 短線外1st 的價差) / 短線外1st價格
            theta = (self.close_price_trace[-1] - self.close_price_trace[-(self.ma_short+1)]) / self.close_price_trace[-(self.ma_short+1)]
            theta *= self.theta_percent
            theta = (theta**2) 
            if theta>1:
                theta=1
            Log('percent' + str(theta*100))
            return [
                {
                    'exchange': exchange,
                    'amount': - targetCurrency_amount * theta,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif targetCurrency_amount*self.close_price_trace[-1] + baseCurrency_amount > 60000*1.1:
            self.cont = 0
            return [
                {
                    'exchange': exchange,
                    'amount': - targetCurrency_amount ,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []