# 策略收益计算
import sys
from Selectors import *
from XueqiuPortfolio import *
from QuotaUtilities import *
from lxml import etree

class idxTrade:#保存参数的类
    def __init__(self,market=None,backtest=0):
        self.backtest=backtest
        self.mkt,self.config = checkTradingDay(market)#交易时间
        self.cfg=self.config[self.mkt]
        self.xq_a_token = self.cfg['xq_a_token']
        self.baseIdx=self.cfg['baseIdx']
        self.xueqiu=xueqiuPortfolio(self.mkt,self.cfg)

    def run(self):  # 主程序
        market=self.mkt
        for mode in self.cfg['paramSet'].keys():
            if mode=='idx':
                ik = idxCompare(market, self.cfg, mode, self.backtest)
                position = self.xueqiu.getPosition()[mode]['holding']
                cash=self.xueqiu.getPosition()[mode]['cash']
                iCls = ik['k']['close']
                sell=[]
                #检查卖出
                for stock in position:
                    print(self.mkt,stock['stock_symbol'])
                    if market=='cn':
                        dailyK=cmsK(stock['stock_symbol'])
                        vol=dailyK['volume']
                        cls=dailyK['close']
                    else:
                        cls=getK(stock['stock_symbol'],self.cfg['date'],self.xq_a_token)['close']
                    sellSignal=False
                    if cls[-1]/cls[-8]<iCls[-1]/iCls[-8] and cls[-1]/cls[-2]<iCls[-1]/iCls[-2]:
                        sellSignal = True
                    if stock['weight']>30:
                        sellSignal = True
                    if sellSignal:
                        cash=stock['weight']
                        stock['weight']=0
                        stock["proactive"] = True
                        sell.append(stock['stock_symbol'])

                #检查买入
                print([int(x['weight']!=0) for x in position],position)
                if sum(int(x['weight']!=0) for x in position)<5:
                    filename = '../CMS/source/Quant/%s%s_J.html' % (market,ik['k'].index[-1].weekday()+1)
                    if self.mkt!='us' and datetime.now().hour<14:
                        filename = '../CMS/source/Quant/%s%s_U.html' % (market, ik['k'].index[-1].weekday() + 1)
                    if os.path.isfile(filename):
                        with open(filename, "r") as f:
                            html = etree.HTML(f.read())
                            symbols=[x.split('/')[-1] for x in html.xpath('//a[not(@id)]/@href')]
                    # print(symbols)
                    if symbols[0] not in [x['stock_symbol'] for x in position]:
                        # for stock in toBuy['雪球代码'][:avalableNum]:
                        #     position.append(self.xueqiu.newPostition(market, stock, 25))
                        position.append(self.xueqiu.newPostition(market, symbols[0], min(20,cash)))
                        # print(sell,toBuy,position)
                        self.xueqiu.trade(market,mode,position)
            # elif mode=='etf':
                # self.cfg['paramSet'][mode]=usETF()
                # ik = idxCompare(self.mkt, self.cfg, mode, self.backtest)
                # position = self.xueqiu.getPosition()[mode]
                # for stock in position:
                #     if stock['stock_symbol'] in self.cfg['hedge'].keys():
                #         stock['weight'] = 10
                #     else:
                #         stock['weight'] =0
                # for stock in ik['list']:
                #     position.append(xueqiuPortfolio.newPostition(self.mkt, stock, 30))
        return

if __name__=='__main__':
    if len(sys.argv)==3:
        g = idxTrade(sys.argv[1], int(sys.argv[2]))
    else:
        g=idxTrade()
    g.run()
