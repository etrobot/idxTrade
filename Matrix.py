import pandas as pd
import akshare as ak
import json,time as t
import urllib.request
import requests
from datetime import *


PROXY = {
    # 'http': 'http://127.0.0.1:8081',  # 访问http需要
    # 'https': 'https://127.0.0.1:8081',  # 访问https需要
}

def getUrl(url,cookie=''):
    '''
    访问api，重试n次
    '''
    retryTimes = 0
    while retryTimes < 99:
        try:
            response = requests.get(url,headers={"user-agent": "Mozilla", "cookie": cookie,"Connection":"close"},timeout=5)
            return response.text
        except Exception as e:
            print(e.args)
            print('retrying.....')
            t.sleep(60)
            retryTimes += 1
            continue

def xueqiuK(symbol='QQQ',cookie=''):
    '''
    雪球k线
    '''
    symbol=symbol.upper()
    print('get %s K'%symbol)
    latestDay = int(t.mktime(datetime.now().date().timetuple())) * 1000
    url = "https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={symbol}&begin={latestDay}&period={period}&type={type}&count={count}&indicator=kline,ma,pe,pb,ps,pcf,market_capital,agt,ggt,balance".format(period='day', symbol=symbol, type='before', latestDay=latestDay, count=-462)
    json2dict=json.loads(getUrl(url,cookie))['data']
    df=pd.DataFrame(json2dict['item'],columns=json2dict['column'])
    df.drop_duplicates(subset='timestamp', keep='first', inplace=True)
    df.set_index(['timestamp'], inplace=True)
    df.index = pd.to_datetime(df.index,unit='ms',utc=True).tz_convert('Asia/Shanghai').date
    df.index.name='date'
    df.sort_index(inplace=True)
    df['percent']=df['percent'].div(100).round(4)
    return df

def invesco(etfCode):
    '''
    invesco ETF 成分股
    '''
    print('get '+etfCode+' holdings')
    proxy_handler = urllib.request.ProxyHandler(PROXY)
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
    url="https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&action=download&ticker="+etfCode
    file_name, headers = urllib.request.urlretrieve(url)
    df = pd.read_csv(file_name)
    df['Holding Ticker']=df['Holding Ticker'].str.strip()
    urllib.request.urlcleanup()
    return df

def ssga(etfCode):
    '''
        ssga ETF 成分股
    '''
    print('get '+etfCode+' holdings')
    proxy_handler = urllib.request.ProxyHandler(PROXY)
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
    urls={
        'SPY':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx',
        'DIA':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-dia.xlsx'
    }
    file_name, headers = urllib.request.urlretrieve(urls[etfCode])
    df=pd.read_excel(file_name, skiprows = [0, 1, 2, 3])
    urllib.request.urlcleanup()
    return df

if __name__ == "__main__":
    #获取纳斯达克指数基金QQQ的成分股
    all = ak.stock_us_spot_em().rename(
            columns={'总市值': 'mktValue'})
    all.dropna(inplace=True)
    all['代码']=[x.split('.')[1] for x in all['代码']]
    all=all[['mktValue','代码','名称']]
    all.set_index('代码',inplace=True)
    df=invesco('QQQ')[['Holding Ticker','Sector']]
    df.columns=['Ticker','Sector']
    # df=df.append(ssga('SPY')[['Ticker','Sector']])
    # df=df.append(ssga('DIA')[['Ticker','Sector']])
    df.dropna(inplace=True)
    df.drop_duplicates(subset='Ticker', keep='last', inplace=True)
    df.set_index('Ticker',inplace=True)
    df=df[~df.index.str.contains('_')]
    df=df[(df.index != 'GOOG')]
    df=df.join(all)
    df= df.sort_values(by=['mktValue'],ascending=False).iloc[:100]
    #获取结束

    #爬雪球k线计算连续上涨天数，排序，生成json文件
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    for symbol,item in df.iterrows():
        qdf= xueqiuK(symbol=symbol, cookie=xq_a_token)
        df.at[symbol, 'continue'] = len([x for x in qdf['percent'][-20:] if x>0])

    data=[ {
                    "value": [
                        v['mktValue'],
                        0,
                        v['continue']
                    ],
                    "name": v['名称'],
                    "id": k,
                    "discretion": "rising"
                } for k,v in df.iterrows()]

    finalJson=[{
            "value": [
                sum(df['mktValue']),
                None,
                None
            ],
            "name": "近一月上涨天数",
            "children": data
        }]
    with open('html/continueRising.json', 'w',encoding='utf-8') as outfile:
        json.dump(finalJson, outfile,ensure_ascii=False)