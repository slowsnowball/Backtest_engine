# -*- coding: utf-8 -*-
import pandas as pd
import math
import ssdata
import matplotlib.pyplot as plt
import numpy as np


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

        # 存储股票数据的字典，key是股票代码，value是一个以时间为索引的dataframe
        self.ini_dic = None
        # 存储基准证券数据的dataframe
        self.benchmark_data = None
        # 从起始日期到终止日期之间的交易日列表
        self.trade_days = None
        # 根据交易日列表和设定的交易频率得出的下单日
        self.order_days = None
        # 每个交易日的总资产，用来计算收益率
        self.today_capital = None
        # 存储收益情况的dataframe，索引是日期，列有策略收益率、基准收益率、最大回撤、
        # 最大回撤区间
        self.ret = None
        # 历史最大回撤
        self.history_max = None
        # 历史最大回撤区间起始日
        self.drawdown_start = None
        # 历史最大回撤区间终止日
        self.drawdown_end = None
        # 存储每个交易日总资产的列表
        self.capital = None
        # 现金
        self.cash = None

    def setup(self):
        """
        用来初始化账户，得到ini_dic, benchmark_data, trade_days 和 order_days等。
        """
        # 初始化这些变量
        self.ini_dic = {}
        self.ret = pd.DataFrame()
        self.benchmark_data = pd.DataFrame()
        self.history_max = 0
        self.capital = []
        self.cash = self.capital_base

        # 遍历universe，通过ssdata包获取股票数据，存入ini_dic
        # 注：新三板股票都是月度数据
        for stock in self.universe:
            # 使用try-except是为了防止获取不到某些数据
            try:
                # 得到的data是一个dataframe
                data = ssdata.get_data(secid=stock,
                                       start_date=self.start_date,
                                       end_date=self.end_date,
                                       field='open,yoyop').dropna().\
                    sort_index()
                self.ini_dic[stock] = data
                print("Succeed: ", stock, self.universe.index(stock)+1, '/',
                      len(self.universe))
            except Exception:
                print(stock, "data unavailable.", self.universe.index(
                    stock)+1, '/', len(self.universe))

        # 把获取不到数据的股票从universe中去掉
        self.universe = list(self.ini_dic.keys())

        # 获取benchmark的数据
        try:
            data = ssdata.get_data(secid=self.benchmark,
                                   start_date=self.start_date,
                                   end_date=self.end_date,
                                   field='open').sort_index().dropna()
            self.benchmark_data = self.benchmark_data.append(data)
        except Exception:
            print("Benchmark ", self.benchmark, " data unavailable.")

        # 交易日列表
        self.trade_days = self.benchmark_data.index
        # 调用下面的get_order_days函数算出下单日列表
        self.order_days = self.get_order_days()

    def get_order_days(self):
        """
        Return the list of order days based on frequency.
        """
        tdays = list(self.trade_days)
        odays = []
        # 遍历tdays，如果能够整除freq，则说明在下单日，将其存入odays
        for i in range(len(tdays)):
            if i % self.freq == 0:
                odays.append(tdays[i])
        return odays


###############################################################################
#                          Define framework functions                         #
###############################################################################


def order_to(target):
    """
    下单到多少股。
    """
    global h_amount
    trade_days = account.trade_days
    order_days = account.order_days
    tax = account.tax
    commission = account.commission
    ini_dic = account.ini_dic
    today_capital = account.today_capital
    slippage = account.slippage

    # 如果date在下单日，就需要进行调仓
    if date in order_days:
        # print(date.strftime('%Y-%m-%d'), list(target.index))
        # t_amount是目标仓位数据的dataframe
        t_amount = pd.DataFrame({'tamount': [0]}, index=list(target.index))

        # Sell stocks in holding but not in target
        for stock in list(h_amount.index):
            if stock not in list(target.index):
                try:
                    stock_data = ini_dic[stock].loc[date.strftime("%Y-%m-%d")]
                    price = stock_data['open']
                    account.cash += h_amount.loc[stock, 'hamount'] *\
                        (price-slippage) * (1-tax-commission)
                    print('order: ', stock, 'amount ',
                          int(0-h_amount.loc[stock, 'hamount']))
                    h_amount.loc[stock, 'hamount'] = -1
                except Exception:
                    h_amount.loc[stock, 'hamount'] = -1
        h_amount = h_amount[h_amount['hamount'] != -1]
        # print("cash: ", account.cash)

        # Deal with stocks in target
        for stock in list(target.index):
            stock_data = ini_dic[stock].loc[date.strftime(
                "%Y-%m-%d")].fillna(0)
            price = stock_data['open']
            # price = stock_data.loc[date.strftime('%Y-%m-%d'), 'open']

            # Buy stocks in target but not in holding
            if stock not in list(h_amount.index):
                h_amount = h_amount.append(pd.DataFrame({'hamount': [0],
                                                         'price': [0],
                                                         'value': [0],
                                                         'percent': [0]},
                                                        index=[stock]))
            # print(target)
            t_amount.loc[stock, 'tamount'] = math.floor(target[stock]/100)*100

            # If hoding > target, sell
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount']\
               > 0:
                account.cash += (h_amount.loc[stock, 'hamount'] -
                                 t_amount.loc[stock, 'tamount'])\
                    * (price-slippage) * (1-tax-commission)

            # If hoding < target, buy
            if h_amount.loc[stock, 'hamount'] - t_amount.loc[stock, 'tamount']\
               < 0:
                # Attention: buy hand by hand in case cash becomes negative
                for number in range(int(t_amount.loc[stock, 'tamount']/100),
                                    0, -1):
                    if account.cash - (number*100 -
                                       h_amount.loc[stock, 'hamount']) *\
                            (price+slippage) * (1+commission) < 0:
                        continue
                    else:
                        account.cash -= (number*100 -
                                         h_amount.loc[stock, 'hamount']) *\
                            (price+slippage) * (1+commission)
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
    """
    下单到多少百分比。
    """
    ini_dic = account.ini_dic
    today_capital = account.today_capital
    # target是存储目标股数的Series
    target = pd.Series()

    # 将pct_target中的仓位百分比数据转化为target中的股数
    for stock in list(pct_target.index):
        stock_data = ini_dic[stock].loc[date.strftime("%Y-%m-%d")]
        price = stock_data['open']
        # price = stock_data.loc[date.strftime('%Y-%m-%d'), 'open']
        # print("today_capital: ", today_capital)
        target[stock] = (pct_target[stock]*today_capital) / price

    print("pct_target: ", pct_target)
    print("target: ", target)
    # 调用order_to函数
    order_to(target)


def result_display(account):
    """
    Display results, including the return curve and a table showing returns
    drawdown and drawdown intervals.
    """
    # account.ret.to_csv('return_details.csv')
    # strategy annual return
    Ra = (1+(account.ret.iloc[-1].rev)) **\
        (12/len(list(account.trade_days))) - 1
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
                                + account.drawdown_end.strftime('%Y-%m-%d'))
                            },
                           index=[''])
    results.reindex(['benchmark return',
                     'Strategy return',
                     'Strategy annual return',
                     'Max drawdown'
                     'Max drawdown interval'
                     ], axis=1)
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


def initialize(account):
    """
    This is a function that runs only once, before the backtest begins.
    """
    pass


def stock_filter(account):
    """
    根据yoyop进行选股的函数。选yoyop前50的股票。
    """
    global selected
    # 将date这一交易日的股票数据取出存到一个新的dataframe中
    all_stock_df = pd.DataFrame()
    mktmaker_information = pd.read_csv(
        'market_maker_information1.csv', index_col="secid")
    amount_information = pd.read_csv(
        'amount_information1.csv', index_col="secid")
    # 遍历ini_dic中所有的股票
    for stock in list(account.ini_dic.keys()):
        # 将date这一天的数据存入all_stock_df中，去掉无数据的
        if mktmaker_information.loc[stock, date.strftime('%Y-%m-%d')] == 1 and\
           amount_information.loc[stock, date.strftime('%Y-%m-%d')] >= 1000000:
            try:
                all_stock_df = all_stock_df.append(
                    account.ini_dic[stock].loc[date.strftime('%Y-%m-%d')])
            except Exception:
                pass

    # 按yoyop降序排序
    all_stock_df = all_stock_df.sort_values('yoyop', ascending=False)
    # 取前50支股票
    selected_stock_df = all_stock_df[:5]
    # 将选取的股票代码存入buylist
    buylist = list(selected_stock_df['secid'])
    # 输出选股情况
    print(date.strftime('%Y-%m-%d'), "selected stocks: ", buylist)
    selected = selected.append(pd.DataFrame(
        {"selected stocks": str(buylist)}, index=[date.strftime('%Y-%m-%d')]))
    return buylist


def handle_data(account):
    """
    This is a function that runs every backtest frequency.
    """
    # selected_stocks为上述选股函数选出的函数
    selected_stocks = stock_filter(account)
    # print(selected_stocks)
    # positions为声明的一个存储目票仓位情况的Series
    positions = pd.Series()
    # 这里采用平均配仓的方式
    for stock in selected_stocks:
        positions[stock] = 1/len(selected_stocks)
        # 将仓位传入下单函数进行下单
    order_pct_to(positions)


print("Hello world!")
start_date = '2015-07-01'
end_date = '2018-06-01'
capital_base = 1000000
freq = 1
benchmark = ['430002.OC']
universe = list(pd.read_csv("All stocks.csv")['secid'])

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
                         'percent': [0]}, index=account.universe)
selected = pd.DataFrame()

for date in list(account.trade_days):
    account.today_capital = 0
    for stock in list(h_amount.index):
        try:
            stock_data = account.ini_dic[stock].loc[date.strftime(
                "%Y-%m-%d")].fillna(0)
            price = stock_data['open']
            account.today_capital += price * h_amount.loc[stock, 'hamount']
        except Exception:
            pass
    account.today_capital += account.cash

    print("cash: ", account.cash)
    print("today_capital: ", account.today_capital)
    handle_data(account)

selected.to_csv(str("with_selected_stocks_information5.csv"))
result_display(account)
