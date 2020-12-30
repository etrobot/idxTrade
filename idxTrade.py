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
                position = self.xueqiu.getPosition()[mode]
                iCls = ik['k']['close']
                sell=[]
                #检查卖出
                for stock in position:
                    print(self.mkt,stock['stock_symbol'])
                    if market=='cn':
                        cls=cmsK(stock['stock_symbol'])['close']
                    else:
                        cls=getK(stock['stock_symbol'],self.cfg['date'],self.xq_a_token)['close']
                    if cls[-1]/cls[-2]<iCls[-1]/iCls[-2] and cls[-1]/cls[-5]<iCls[-1]/iCls[-5]:
                        stock['weight']=0
                        stock["proactive"] = True
                        sell.append(stock['stock_symbol'])

                avalableNum=4-(len(position)-len(sell))
                #检查买入
                if avalableNum>0:
                    # toBuy=pd.read_csv('md/'+self.mkt+ik['k'].index[-5].strftime("%Y%m%d")+'.csv').iloc[:10].copy()
                    # factor=[]
                    # for stock in toBuy['雪球代码']:
                    #     stockK=cmsK(stock)
                    #     factor.append(factor_2(stockK))
                    # toBuy['f']=factor
                    # toBuy.sort_values(by='f', ascending=True,inplace=True)
                    # toBuy = pd.read_csv('md/' + self.mkt + ik['k'].index[-1].strftime("%Y%m%d") + '.txt',dtype={'symbol': str})
                    filename = '../html/%s%s_U.html' % (market,ik['k'].index[-1].weekday()+1)
                    if os.path.isfile(filename):
                        with open(filename, "r") as f:
                            html = etree.HTML(f.read())
                            symbols=[x.split('/')[-1] for x in html.xpath('//a/@href')]
                    if symbols[0] not in [x['stock_symbol'] for x in position]:
                        # for stock in toBuy['雪球代码'][:avalableNum]:
                        #     position.append(self.xueqiu.newPostition(market, stock, 25))
                        position.append(self.xueqiu.newPostition(market, symbols[0], 21))
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
