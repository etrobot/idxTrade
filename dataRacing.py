from video import  *
from QuotaUtilities import *

ASSETPATH='video/'

def raceVideo(symbols:dict,length=462):
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    # symbols = {'DIA':'道琼斯ETF', 'QQQ':'纳斯卡克ETF', 'SPY':'标普500ETF'}
    dates=[]
    sortedArr=[]
    for symbol,name in symbols.items():
        k=getK('.'+symbol,pdate=datetime.now()-timedelta(days=180),xq_a_token=xq_a_token)['close']
        stock={
            'name':name,
            'oriData':k[-length:].tolist(),
            'data':[round(k[x-length]*100/k[-length]-100,2) for x in range(0,length)]
        }
        if len(dates)==0:
            dates=[x.strftime("%Y-%m-%d") for x in k.index[-length:]]
        sortedArr.append(stock)
    with open(ASSETPATH+'race.json', 'w',encoding='utf-8') as outfile:
        json.dump({'date': dates,'data':sortedArr}, outfile,ensure_ascii=False)
    with open('Template/race.xhtml', "r") as fin:
        with open(ASSETPATH + 'race.html', "w") as fout:
            fout.write(fin.read())

if __name__=='__main__':
    raceVideo(symbols={
        'IXIC':'纳斯达克',
        'DJI':'道琼斯',
        'INX':'标普500'
    })