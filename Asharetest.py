# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import math
import ssdata
import matplotlib.pyplot as plt


###############################################################################
#                           Define framework classes                          #
###############################################################################

class account:
    def __init__(self, start_date, end_date, capital_base, freq, benchmark,
                 universe, tax=0.001, commission=0.00025, slippage=0.01):
        """
        start_date: the start date of back test
        end_date: the end date of back test
        capital_base: initial fund to perform back test
        freq: back test frequencies, measured in days, eg. 1 for daily and 7
            for weekly
        tax: tax rate
        commission: commission rate
        slippage: slippage
        """
        self.start_date = start_date
        self.end_date = end_date
        self.capital_base = capital_base
        self.freq = freq
        self.benchmark = benchmark
        self.universe = universe
        self.tax = tax
        self.commission = commission
        self.slippage = slippage

        self.ini_dic = None
        self.benchmark_data = None
        self.trade_days = None
        self.order_days = None
        self.today_capital = None
        self.ret = None
        self.history_max = None
        self.drawdown_start = None
        self.drawdown_end = None
        self.capital = None
        self.cash = None

    def setup(self):
        """
        Set up the ini_dic, benchmark_data, trade_days and order_days.
        """
        self.ini_dic = {}
        self.ret = pd.DataFrame()
        self.benchmark_data = pd.DataFrame()
        self.history_max = 0
        self.capital = []
        self.cash = capital_base

        for stock in self.universe:
            try:
                data = ssdata.get_data(secid=stock,
                                       start_date=self.start_date,
                                       end_date=self.end_date,
                                       field='open').sort_index()
                self.ini_dic[stock] = data
            except Exception:
                self.universe.remove(stock)
                print("Stock ", stock, " data unavailable.")

        try:
            data = ssdata.get_data(secid=self.benchmark,
                                   start_date=self.start_date,
                                   end_date=self.end_date,
                                   field='open').sort_index()
            self.benchmark_data = self.benchmark_data.append(data)
        except Exception:
            print("Benchmark ", self.benchmark, " data unavailable.")
        self.trade_days = self.ini_dic[self.universe[0]].index
        self.order_days = []
        for i in range(len(list(self.trade_days))):
            if i % self.freq == 0:
                self.order_days.append(list(self.trade_days)[i])


###############################################################################
#                          Define framework functions                         #
###############################################################################

def order_to(target):
    global h_amount
    trade_days = account.trade_days
    order_days = account.order_days
    tax = account.tax
    commission = account.commission
    ini_dic = account.ini_dic
    today_capital = account.today_capital

    if date in order_days:
        print(date.strftime('%Y-%m-%d'), list(target.index))
        t_amount = pd.DataFrame({'tamount': [0]}, index=list(target.index))

        # Sell stocks in holding but not in target
        for stock in list(h_amount.index):
            if stock not in list(target.index):
                stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
                price = stock_data['open']
                account.cash += h_amount.loc[stock, 'hamount'] *\
                    (price-0.01) * (1-tax-commission)
                print('order: ', stock, 'amount ',
                      int(0-h_amount.loc[stock, 'hamount']))
                h_amount.drop(stock)

        # Deal with stocks in target
        for stock in list(target.index):
            stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
            price = stock_data['open']

            # Buy stocks in target but not in holding
            if stock not in list(h_amount.index):
                h_amount = h_amount.append(pd.DataFrame({'hamount': [0],
                                                         'price': [0],
                                                         'value': [0],
                                                         'percent': [0]},
                                                        index=[stock]))

            t_amount.loc[stock, 'tamount'] = math.floor(target[stock]/100)*100

            # If hoding > target, sell
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount']\
               > 0:
                account.cash += (h_amount.loc[stock, 'hamount'] -
                                 t_amount.loc[stock, 'tamount'])\
                                 * (price-0.01) * (1-tax-commission)

            # If hoding < target, buy
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount']\
               < 0:
                # Attention: buy hand by hand in case cash becomes negative
                for number in range(int(t_amount.loc[stock, 'tamount']/100),
                                    0, -1):
                    if account.cash - (number*100 -
                                       h_amount.loc[stock, 'hamount']) *\
                       (price+0.01) * (1+commission) < 0:
                        continue
                    else:
                        account.cash -= (number*100 -
                                         h_amount.loc[stock, 'hamount']) *\
                            (price+0.01) * (1+commission)
                        t_amount.loc[stock, 'tamount'] = number * 100
                        break

            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount']\
               != 0:
                print('order: ', stock, 'amount ',
                      int(t_amount.loc[stock, 'tamount'] -
                          h_amount.loc[stock, 'hamount']))

            h_amount.loc[stock, 'hamount'] = t_amount.loc[stock, 'tamount']
            h_amount.loc[stock, 'price'] = price
            h_amount.loc[stock, 'value'] = h_amount.loc[stock, 'price'] *\
                h_amount.loc[stock, 'hamount']

        h_amount['percent'] = h_amount['value'] / sum(h_amount['value'])

    # # Output holding details
    # h_amount.to_csv('position_details.csv')

    account.capital.append(today_capital)
    try:
        drawdown = (max(account.capital[:-1])-account.capital[-1]) /\
            max(account.capital[:-1])
    except Exception:
        drawdown = 0

    if drawdown > account.history_max:
        account.drawdown_start =\
            trade_days[account.capital.index(max(account.capital[:-1]))]
        account.drawdown_end =\
            trade_days[account.capital.index(account.capital[-1])]
        account.history_max = drawdown

    account.ret = account.ret.append(pd.DataFrame(
        {'rev': (account.capital[-1]-account.capital[0])/account.capital[0],
         'max_drawdown': account.history_max,
         'benchmark':
         (account.benchmark_data.loc[date.strftime('%Y-%m-%d'), 'open'] -
          account.benchmark_data.loc[trade_days[0].strftime('%Y-%m-%d'),
                                     'open']) /
         account.benchmark_data.loc[trade_days[0].strftime('%Y-%m-%d'),
                                    'open']},
        index=[date]))


def order_pct_to(pct_target):
    ini_dic = account.ini_dic
    today_capital = account.today_capital
    target = pd.Series()

    for stock in list(pct_target.index):
        stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
        price = stock_data['open']
        target[stock] = (pct_target[stock]*today_capital) / price

    order_to(target)


def result_display(account):
    """
    Display results, including the return curve and a table showing returns
    drawdown and drawdown intervals.
    """
    # account.ret.to_csv('return_details.csv')
    # strategy annual return
    Ra = (1+(account.ret.iloc[-1].rev)) **\
        (250/len(list(account.trade_days))) - 1
    results = pd.DataFrame({'benchmark return':
                            '%.2f%%' % (account.ret.iloc[-1].benchmark * 100),
                            'Strategy return':
                            '%.2f%%' % (account.ret.iloc[-1].rev * 100),
                            'Strategy annual return':
                            '%.2f%%' % (Ra*100),
                            'Max drawdown':
                            '%.2f%%' % (account.ret.iloc[-1].max_drawdown*100),
                            'Max drawdown interval':
                            str(account.drawdown_start.strftime('%Y-%m-%d')
                                + ' to '
                                + account.drawdown_end.strftime('%Y-%m-%d'))},
                           index=[''])
    results.reindex(['benchmark return',
                     'Strategy return',
                     'Strategy annual return',
                     'Max drawdown',
                     'Max drawdown interval'], axis=1)
    print(results.transpose())

    # plot the results
    account.ret['rev'].plot(color='royalblue', label='strategy return')
    account.ret['benchmark'].plot(color='black', label='benchmark return')
    x = np.array(list(account.ret.index))
    plt.fill_between(x, max(max(account.ret.rev), max(account.ret.benchmark)),
                     min(min(account.ret.rev), min(account.ret.benchmark)),
                     where=((x <= account.drawdown_end) &
                            (x >= account.drawdown_start)),
                     facecolor='lightsteelblue',
                     alpha=0.4)
    plt.legend()
    plt.show()


###############################################################################
#                   Parameters and functions set up manually                  #
###############################################################################

print("Hello world!")
start_date = '2015-01-01'
end_date = '2016-01-01'
capital_base = 1000000
freq = 1
benchmark = ['000001.XSHE']
universe = ['600036.XSHG', '601166.XSHG']


def initialize(account):
    """
    This is a function that runs only once, before the backtest begins.
    """
    pass


def handle_data(account):
    """
    This is a function that runs every backtest frequency.
    """
    positions = pd.Series()
    for stock in account.universe:
        positions[stock] = 0.5
    order_pct_to(positions)


###############################################################################
#                               Backtest begins                               #
###############################################################################


account = account(start_date=start_date, end_date=end_date,
                  capital_base=capital_base, freq=freq,
                  benchmark=benchmark, universe=universe)
account.setup()
initialize(account)

h_amount = pd.DataFrame({'hamount': [0],
                         'price': [0],
                         'value': [0],
                         'percent': [0]}, index=universe)

for date in account.trade_days:
    account.today_capital = 0
    for stock in list(h_amount.index):
        stock_data = account.ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
        price = stock_data['open']
        account.today_capital += price * h_amount.loc[stock, 'hamount']
    account.today_capital += account.cash

    handle_data(account)

result_display(account)
