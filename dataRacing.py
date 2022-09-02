from video import  *
from QuotaUtilities import *

ASSETPATH='video/'

def raceVideo(symbols:dict,baseSymbol='.IXIC',length=462):
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    dates=[]
    sortedArr=[]
    # startDate=datetime.now()-timedelta(days=300)
    qdf=xueqiuK(baseSymbol,cookie=xq_a_token)[['close','percent']]
    for symbol,name in symbols.items():
        if symbol==baseSymbol:
            continue
        k=xueqiuK(symbol,cookie=xq_a_token)[['close','percent']]
        qdf=qdf.join(k,how='left',rsuffix='_%s'%symbol).fillna(method='ffill')
    qdf.rename(columns={'close':'close_'+baseSymbol,'percent':'percent_'+baseSymbol},inplace=True)
    qdf=qdf.dropna()
    length=len(qdf.index)
    dates = [x.strftime("%Y-%m-%d") for x in qdf.index[-length:]]
    for symbol, name in symbols.items():
        k=qdf['close_'+symbol]
        pct=[1]
        for i in range(1,len(qdf)):
            pct.append(pct[-1]*(1+qdf['percent_'+symbol][i]))
        stock={
            'name':name,
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
        '.DJI':'道琼斯',
        'SH000001':'上证指数',
        'HKHSI':'恒生指数'
    },baseSymbol='.DJI')