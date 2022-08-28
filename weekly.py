import urllib.request,csv,json
from video import *
import numpy as np

QUOTEPATH='Quotation/'
ASSETPATH='video/'

def invesco(etfCode):
    proxy = {
        'http': 'http://127.0.0.1:8081',  # 访问http需要
        'https': 'https://127.0.0.1:8081',  # 访问https需要
    }
    proxy_handler = urllib.request.ProxyHandler(proxy)
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
    url="https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&action=download&ticker="+etfCode
    file_name, headers = urllib.request.urlretrieve(url)
    df = pd.read_csv(file_name)
    df['Holding Ticker']=df['Holding Ticker'].str.strip()
    return df

def ssga(etfCode):
    urls={
        'SPY':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx',
        'DIA':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-dia.xlsx'
    }
    file_name, headers = urllib.request.urlretrieve(urls[etfCode])
    df=pd.read_excel(file_name, skiprows = [0, 1, 2, 3])
    return df


if __name__=='__main__':
    all = ak.stock_us_spot_em()
    all.dropna(inplace=True)
    all['代码']=[x.split('.')[1] for x in all['代码']]
    all=all[['总市值','代码']]
    all.set_index('代码',inplace=True)
    df=invesco('QQQ')[['Holding Ticker','Sector']]
    df.columns=['Ticker','Sector']
    df=df.append(ssga('SPY')[['Ticker','Sector']])
    df=df.append(ssga('DIA')[['Ticker','Sector']])
    df.dropna(inplace=True)
    df.drop_duplicates(subset='Ticker', keep='last', inplace=True)
    df.set_index('Ticker',inplace=True)
    df=df.join(all)
    sector=list(df.groupby('Sector').groups.keys())
    sectorCN=translate(','.join(sector)).split('，')
    sector2CN={sector[x]:sectorCN[x] for x in range(len(sector))}
    df['Sector']=[sector2CN[x] for x in df['Sector']]

    for symbol,item in df.iterrows():
        if symbol=='CASH_USD':
            continue
        print(symbol)
        quofile=QUOTEPATH+symbol+'.csv'
        retry=False
        retry=True
        if os.path.isfile(quofile) and retry:
            df=pd.read_csv(quofile,index_col='date')
        else:
            df=futuKLine(symbol).drop(['date'],axis=1)
            df.to_csv(quofile,index_label='date')
        with open(ASSETPATH+symbol+'.json', 'w',encoding='utf-8') as outfile:
            json.dump({
                'martketValue':item['总市值'],
                'sector':item['Sector'],
                'close':df['close'][-60:].tolist()
            }, outfile,ensure_ascii=False)