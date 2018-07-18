# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import math
import ssdata
import matplotlib.pyplot as plt

###############################################################################
#                         Define the functions needed                         #
###############################################################################


def initialize():
    # initialize stock information

    global n, trade_days, order_days, ini_dic, ret, benchmark, history_max
    history_max = 0
    ini_dic = {}
    for stock in universe:
        try:
            ini_dic[stock] = ssdata.get_data(secid=stock,
                                             start_date=start_date,
                                             end_date=end_date,
                                             field='open').sort_index()
        except Exception:
            universe.remove(stock)
            print(stock, " data unavailable.")
    n = 0
    trade_days = ini_dic[universe[0]].index
    order_days = get_order_days(freq)
    ret = pd.DataFrame()
    benchmark = pd.read_csv('file:///Users/liushihao/emacs/python/\
benchmarkdata.csv', index_col=0)


def get_order_days(freq):
    tdays = list(trade_days)
    days = []
    for i in range(len(tdays)):
        if i % freq == 0:
            days.append(tdays[i])
    return days


def cal_position(pb, max_pos):
    if pb > 2.0:
        return 0
    else:
        return min(2 - pb, max_pos)


def pos(pb0, pb1):
    if pb0 < pb1:
        pos0 = cal_position(pb0, 0.7)
        pos1 = cal_position(pb1, 1 - pos0)
    else:
        pos1 = cal_position(pb1, 0.7)
        pos0 = cal_position(pb0, 1 - pos1)
    return [pos0, pos1]


def handle_data(date):
    pb = pd.Series()
    positions = pd.Series()
    ini_dic1 = {}
    ini_dic1['600036.XSHG'] = pd.read_csv('file:///Users/liushihao/emacs/\
python/600036.XSHG.csv', index_col=0)
    ini_dic1['601166.XSHG'] = pd.read_csv('file:///Users/liushihao/emacs/\
python/601166.XSHG.csv', index_col=0)
    for stock in universe:
        stock_data = ini_dic1[stock].loc[date.strftime('%Y/%-m/%-d')]
        pb[stock] = stock_data['PB']
    positions['600036.XSHG'] = pos(pb['600036.XSHG'], pb['601166.XSHG'])[0]
    positions['601166.XSHG'] = pos(pb['600036.XSHG'], pb['601166.XSHG'])[1]
    order_pct_to(positions)


def order_pct_to(target):
    global drawdown_start, drawdown_end, history_max, cash, n, h_amount, ret
    if date in order_days:
        print(date.strftime('%Y-%m-%d'), list(target.index))
        t_amount = pd.DataFrame({'tamount': [0]}, index=list(target.index))

        # Sell stocks in holding but not in target
        for stock in list(h_amount.index):
            if stock not in list(target.index):
                stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
                price = stock_data['open']
                cash += h_amount.loc[stock, 'hamount']*(price-0.01)*(1-tax-commission)
                print('order: ', stock, 'amount ', int(0-h_amount.loc[stock, 'hamount']))
                h_amount.drop(stock)

        # Deal with stocks in target
        for stock in list(target.index):
            stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
            price = stock_data['open']

            # Buy stocks in target but not in holding
            if stock not in list(h_amount.index):
                h_amount = h_amount.append(pd.DataFrame({'hamount': [0],
                                                         'price': [0],
                                                         'value': [0]}, index=[stock]))

            t_amount.loc[stock, 'tamount'] = math.floor((target[stock] * today_capital) / (100 * price)) * 100

            # If hoding > target, sell
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount'] > 0:
                cash += (h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount'])*(price-0.01)*(1-tax-commission)

            # If hoding < target, buy
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount'] < 0:
                # Attention: buy hand by hand in case cash becomes negative
                for number in range(int(t_amount.loc[stock, 'tamount']/100), 0, -1):
                    if cash - (number*100-h_amount.loc[stock, 'hamount'])*(price+0.01)*(1+commission) < 0:
                        continue
                    else:
                        cash -= (number*100-h_amount.loc[stock, 'hamount'])*(price+0.01)*(1+commission)
                        t_amount.loc[stock, 'tamount'] = number * 100
                        break

            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount'] != 0:
                print('order: ', stock, 'amount ', int(t_amount.loc[stock, 'tamount'] - h_amount.loc[stock, 'hamount']))

            h_amount.loc[stock, 'hamount'] = t_amount.loc[stock, 'tamount']
            h_amount.loc[stock, 'price'] = price
            h_amount.loc[stock, 'value'] = h_amount.loc[stock, 'price'] * h_amount.loc[stock, 'hamount']

        h_amount['percent'] = h_amount['value'] / sum(h_amount['value'])

    # # Output holding details
    # h_amount.to_csv('position_details.csv')

    capital.append(today_capital)
    try:
        drawdown = (max(capital[:-1])-capital[-1])/(max(capital[:-1]))
    except Exception:
        drawdown = 0

    if drawdown > history_max:
        drawdown_start = trade_days[capital.index(max(capital[:-1]))]
        drawdown_end = trade_days[capital.index(capital[-1])]
        history_max = drawdown

    ret = ret.append(pd.DataFrame(
        {'rev': (capital[-1]-capital[0])/capital[0],
         'max_drawdown': history_max,
         'benchmark': (benchmark.loc[date.strftime('%Y/%-m/%-d'), 'closeIndex']
                       -
                       benchmark.loc['2015/1/5', 'closeIndex']) /
         benchmark.loc['2015/12/31', 'closeIndex']}, index=[date]))

    n += 1


def result_display():
    # ret.to_csv('return_details.csv')
    # strategy annual return
    Ra = ((1+(ret.iloc[-1].rev))**(250/n)) - 1
    df = pd.DataFrame({'benchmark return':
                       '%.2f%%' % (ret.iloc[-1].benchmark * 100),
                       'Strategy return':
                       '%.2f%%' % (ret.iloc[-1].rev * 100),
                       'Strategy annual return':
                       '%.2f%%' % (Ra*100),
                       'Max drawdown':
                       '%.2f%%' % (ret.iloc[-1].max_drawdown*100),
                       'Max drawdown interval':
                       str(drawdown_start.strftime('%Y-%m-%d')
                           + ' to '
                           + drawdown_end.strftime('%Y-%m-%d'))},
                      index=[''])
    df.reindex(['benchmark return',
                'Strategy return',
                'Strategy annual return',
                'Max drawdown',
                'Max drawdown interval'], axis=1)
    print(df.transpose())

    # plot the results
    ret['rev'].plot(color='royalblue', label='strategy return')
    ret['benchmark'].plot(color='firebrick', label='benchmark return')
    x = np.array(list(ret.index))
    plt.fill_between(x, max(max(ret.rev), max(ret.benchmark)),
                     min(min(ret.rev), min(ret.benchmark)),
                     where=((x <= drawdown_end) & (x >= drawdown_start)),
                     facecolor='lightsteelblue',
                     alpha=0.4)
    plt.legend()
    plt.show()


###############################################################################
#                         Set the backtest parameters                         #
###############################################################################

start_date = '2015-01-01'
end_date = '2016-01-01'
capital = []
position = 0.
cash = 1000000
freq = 1
tax = 0.001
commission = 0.00025
universe = ['600036.XSHG', '601166.XSHG']

###############################################################################
#                               Backtest begins                               #
###############################################################################

initialize()

for date in trade_days:
    if n == 0:
        today_capital = position + cash
        h_amount = pd.DataFrame({'hamount': [0],
                                 'price': [0],
                                 'value': [0],
                                 'percent': [0]}, index=universe)
    else:
        today_capital = 0
        for stock in list(h_amount.index):
            stock_data = ini_dic[stock].loc[date.strftime('%Y-%m-%d')]
            price = stock_data['open']
            today_capital += price * h_amount.loc[stock, 'hamount']
        today_capital += cash

    handle_data(date)

result_display()
