# -*- coding: utf-8 -*-

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
                'pairs': ['MIOTA-USDT'],
            },
        }

        # seconds for broker to call trade()
        # do not set the frequency below 60 sec.
        # 10 * 60 for 10 mins
        self.period = 10 * 60
        self.options = {}
        # set trade frequency(multiply of period)
        self.trade_amount = 0
        self.close_price_X = []
        self.close_price_Y = []

        # at most 120K USDT
        self.upper_bound = 120000
        self.current_left = 120000
        self.total_buy_amount = 0
        self.last_buy_price = 0
        self.last_high_price = 0
        self.last_trade = 'SELL'
        self.counter = 0
        self.last_buy_time = 0

    def linear_regression(self, X, Y):
        np_X = np.array(X)
        np_Y = np.array(Y)
        return np.linalg.pinv(np_X).dot(np_Y)


    # called every self.period
    def trade(self, information):
        # for single pair strategy, user can choose which exchange/pair to use when launch, get current exchange/pair from information
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_Y.append(close_price)
        self.close_price_X.append([1, self.counter])
        weight = self.linear_regression(self.close_price_X[-18:], self.close_price_Y[-18:])
        # Log('Slot: ' + str(weight[1]))

        if self.counter >= 36 and self.counter % 6 == 0:
            self.counter += 1
            if self.last_trade == 'BUY':
                # 止損
                if self['assets'][exchange]['MIOTA'] * close_price < 0.75 * self.total_buy_amount:
                    self.trade_amount = self['assets'][exchange]['MIOTA']
                    self.total_buy_amount = 0
                    self.current_left += self.trade_amount * close_price
                    self.last_buy_price = 0
                    self.last_high_price = 0
                    self.last_trade = 'SELL'
                    Log('stop loss')
                    return [
                        {
                            'exchange': exchange,
                            'amount': -self.trade_amount,
                            'price': -1,
                            'type': 'MARKET',
                            'pair': pair,
                        }
                    ]
                else:
                    if self['assets'][exchange]['MIOTA'] * close_price > self.total_buy_amount:
                        if close_price < self.last_high_price:
                            self.trade_amount = self['assets'][exchange]['MIOTA']
                            self.total_buy_amount = 0
                            self.current_left += self.trade_amount * close_price
                            self.last_buy_price = 0
                            self.last_high_price = 0
                            self.last_trade = 'SELL'
                            # Log('selling: ' + str(self.trade_amount))
                            return [
                                {
                                    'exchange': exchange,
                                    'amount': -self.trade_amount,
                                    'price': -1,
                                    'type': 'MARKET',
                                    'pair': pair,
                                }
                            ]
                        else:
                            self.last_high_price = close_price
                            return []
                    else:
                        if self.counter - self.last_buy_time > 72 and self['assets'][exchange]['MIOTA'] * close_price >= 0.98 * self.total_buy_amount:
                            self.trade_amount = self['assets'][exchange]['MIOTA']
                            self.total_buy_amount = 0
                            self.current_left += self.trade_amount * close_price
                            self.last_buy_price = 0
                            self.last_high_price = 0
                            self.last_trade = 'SELL'
                            Log('Hold too long')
                            return [
                                {
                                    'exchange': exchange,
                                    'amount': -self.trade_amount,
                                    'price': -1,
                                    'type': 'MARKET',
                                    'pair': pair,
                                }
                            ]
                        return []
                
            elif self.last_trade == 'SELL' and weight[1] > 0:
                invest_amount = min(self.upper_bound, self.current_left * 0.5)
                self.trade_amount = int(invest_amount / close_price)
                self.total_buy_amount += self.trade_amount * close_price
                self.current_left -= self.trade_amount * close_price
                self.last_buy_price = close_price
                self.last_high_price = close_price
                self.last_buy_time = self.counter - 1
                self.last_trade = 'BUY'
                # Log('buying: ' + str(self.trade_amount))
                return [
                    {
                        'exchange': exchange,
                        'amount': self.trade_amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else:
                return []
        else:
            self.counter += 1
            return []