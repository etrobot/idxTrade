# 指数研究
import matplotlib.pyplot as plt
from QuotaUtilities import *
from Selectors import *
import akshare as ak

plt.figure(figsize=(20, 5))

def research():
    iK=dict()
    idx=['sh000300','sz399101','sz399102']
    for iCode in idx:
        iK[iCode] = ak.stock_zh_index_daily_tx(symbol=iCode)
    num=min(len(iK['sh000300']),len(iK['sz399101']),len(iK['sz399102']))
    for iCode in iK.keys():
        iK[iCode] = iK[iCode].iloc[-num:]
        iK[iCode][iCode]=[iK[iCode]['close'][j] / iK[iCode]['close'][0] for j in range(len(iK[iCode]['close']))]

    # 绘制走势
    fig = iK[idx[0]][idx[0]].plot(figsize=(20, 5), color='purple')
    fig.plot(iK[idx[1]][idx[1]], color='green', alpha=1)
    fig.plot(iK[idx[2]][idx[2]], color='brown', alpha=1)

    days = 20
    i = -days
    signal = 0
    nSeri = []
    while i < len(iK[idx[0]])-days-1:
        i += days
        if i < days:
            nSeri.extend([1.0 for r in range(days+1)])
            continue
        # 收益曲线
        compare = [
            iK[idx[0]][idx[0]][i]/iK[idx[0]][idx[0]][i-days],
            iK[idx[1]][idx[1]][i] / iK[idx[1]][idx[1]][i - days],
            iK[idx[2]][idx[2]][i] / iK[idx[2]][idx[2]][i - days]
        ]
        m=compare.index(max(compare))
        nSeri.extend([nSeri[-1]*iK[idx[m]][idx[m]][r]/iK[idx[m]][idx[m]][i-days] for r in range(i-days,i)])
    fig.plot(pd.Series(data=nSeri,index=iK[idx[m]].index), color='black', alpha=1)
    fig.legend()

    timespans = {'x1': [], 'x2': [], 'o1': [], 'o2': []}
    colors = {'x1': 'green', 'x2': 'blue', 'o1': 'red', 'o2': 'orange'}

    cs=iK['sh000300']['close']
    i = -1
    days = 44
    x2 = timespans['x2']
    while i < len(cs) - 1 - days:
        i += 1
        c = cs[i:i + days]
        if c[-1] < c[0] and max(c) == c[0]:
            i += days - 1
            x2.append(c.index)

    days = 32
    spans = []
    testnum = 4
    for n in tqdm(range(testnum)):
        nSpan = []
        i = -1
        while i < len(cs) - 1 - days:
            i += 1
            c = cs[i:i + days]
            if int(days / testnum * n) <= c.values.argmax() < int(days / testnum * (n + 1)) and c[-1] < c[0]:
                nSpan.append(c.index)
                i += days - 1
        spans.append(nSpan)

    minCount = 999
    minSpaniK = 0
    for si in range(testnum):
        match = 0
        for sp in spans[si]:
            for ts in timespans['x2']:
                if ts[0] in sp:
                    match += 1
        if len(spans[si]) < minCount and len(spans[si]) != 0 and match > 0:
            minCount = len(spans[si])
            minSpaniK = si

    timespans['x1'] = spans[minSpaniK]
    print(len(spans[minSpaniK]), minSpaniK)

    for k, v in timespans.items():
        if len(v) == 0:
            continue
        for span in v:
            if len(span) == 0:
                continue
            fig.axvspan(span[0], span[-1], facecolor=colors[k], edgecolor='none', alpha=.2)

    plt.show()


if __name__=='__main__':
    cfg= {
        "url": "https://xueqiu.com/S/.IXIC",
        "baseIdx": ".IXIC",
        "paramSet": {
            "etf": {
                "QQQ": ["signal off", 15, 4, 7, 4],
                "SPY": ["signal off", 15, 4, 7, 4],
                "DIA": ["signal off", 15, 4, 7, 4]
            }
        }
    }
    for f in usETF().keys():
    # for f in pd.read_csv('usETF.csv',encoding='GB18030')['symbol']:
        cfg['paramSet']['etf'][f]=["signal off", 15, 4, 7, 4]
    print(cfg)
    print(idxCompare('us', cfg, mode='etf', backtest=1))
