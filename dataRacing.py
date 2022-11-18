from video import  *
from QuotaUtilities import *

ASSETPATH='html/'

def raceVideo(symbols:dict,baseSymbol='.IXIC',beforeStartDate=datetime(2018,12,31).date()):
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    sortedArr=[]
    qdf=xueqiuK(baseSymbol,cookie=xq_a_token)[['close','percent']]
    for symbol,name in symbols.items():
        if symbol==baseSymbol:
            continue
        k=xueqiuK(symbol,cookie=xq_a_token)[['close','percent']]
        qdf=qdf.join(k,how='left',rsuffix='_%s'%symbol).fillna(method='ffill')
    qdf.rename(columns={'close':'close_'+baseSymbol,'percent':'percent_'+baseSymbol},inplace=True)
    qdf=qdf.dropna()
    qdf=qdf[qdf.index>=beforeStartDate]
    length=len(qdf.index)
    dates = [x.strftime("%Y-%m-%d") for x in qdf.index[-length:]]
    for symbol, name in symbols.items():
        k=qdf['close_'+symbol]
        pct=[1]
        for i in range(1,len(qdf)):
            pct.append(pct[-1]*(1+qdf['percent_'+symbol][i]))
        stock={
            'name':'%s %s'%(name,symbol),
            'oriData':k[-length:].tolist(),
            'data':[round(x*100-100,2) for x in pct]
        }
        sortedArr.append(stock)
    with open(ASSETPATH+'race.json', 'w',encoding='utf-8') as outfile:
        json.dump({'date': dates,'data':sortedArr}, outfile,ensure_ascii=False)
    with open('Template/race.xhtml', "r") as fin:
        with open(ASSETPATH + 'race.html', "w") as fout:
            fout.write(fin.read())

if __name__=='__main__':
    raceVideo(symbols={
        'UUP':'美元指数',
        'SPY':'标普ETF',
    },baseSymbol='SZ000568',beforeStartDate=datetime(2021,12,29).date())