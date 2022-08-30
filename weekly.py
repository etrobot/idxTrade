import urllib.request,csv,json
from video import *
import numpy as np

QUOTEPATH='Quotation/'
ASSETPATH='video/'

def invesco(etfCode):
    print('get '+etfCode+' holdings')
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
    urllib.request.urlcleanup()
    return df

def ssga(etfCode):
    print('get '+etfCode+' holdings')

    urls={
        'SPY':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx',
        'DIA':'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-dia.xlsx'
    }
    file_name, headers = urllib.request.urlretrieve(urls[etfCode])
    df=pd.read_excel(file_name, skiprows = [0, 1, 2, 3])
    urllib.request.urlcleanup()
    return df

def run():
    all = ak.stock_us_spot_em().rename(
        columns={'总市值': 'mktValue'})
    all.dropna(inplace=True)
    all['代码']=[x.split('.')[1] for x in all['代码']]
    all=all[['mktValue','代码']]
    all.set_index('代码',inplace=True)
    df=invesco('QQQ')[['Holding Ticker','Sector']]
    df.columns=['Ticker','Sector']
    df=df.append(ssga('SPY')[['Ticker','Sector']])
    df=df.append(ssga('DIA')[['Ticker','Sector']])
    df.dropna(inplace=True)
    df.drop_duplicates(subset='Ticker', keep='last', inplace=True)
    df.set_index('Ticker',inplace=True)
    df=df[(df.index != 'GOOG') & (df.index != 'CASH_USD')]
    df=df.join(all)
    futuSymbols = pd.read_csv("futuSymbols.csv",index_col='股票简称')[['股票名称']]
    df=df.join(futuSymbols)
    sector=list(df.groupby('Sector').groups.keys())
    sectorCN=translate(','.join(sector)).split('，')
    sector2CN={sector[x]:sectorCN[x] for x in range(len(sector))}
    df['Sector']=[sector2CN[x] for x in df['Sector']]

    for symbol,item in df.iterrows():
        print(symbol)
        quofile=QUOTEPATH+symbol+'.csv'
        retry=False
        retry=True
        if os.path.isfile(quofile) and retry:
            qdf=pd.read_csv(quofile,index_col='date')
        else:
            qdf=futuKLine(symbol).drop(['date'],axis=1)
            qdf.to_csv(quofile,index_label='date')
        for days in [60,20,5]:
            df.at[symbol,str(days)+'days']=round(qdf['close'][-1]*100.0/qdf['close'][-days-1]-100.0,1)
        df.at[symbol,'5daysmoney']=qdf['amount'][-5:].sum()

    if not os.path.isfile(FOLDER+'week.mp4'):
        introText='美股三大指数，道琼斯、纳斯达克和标普500是全球股市的风向标，观察对应指数基金成分股的走势可以揭示当前的投资趋势，接下来就让我们从市值、月涨幅、周涨幅和周成交四个维度来观察这些成分股。'
        text2voice(introText, FOLDER + 'week')
        get_video(get_time_count('week'), 'week')
        get_audio('week')

    conditions=['mktValue','5daysmoney','5days','20days']
    for condition in conditions:
        df.sort_values(by=[condition],ascending=False,inplace=True)
        if condition=='mktValue':
            readText='当前市值前十大企业为：'+ ','.join(df['股票名称'][:10].tolist())
        elif condition=='5daysmoney':
            readText='本周成交前十大股票为：'+ ','.join(df['股票名称'][:10].tolist())
        else:
            rank=df.index[:3].tolist()
            rank.reverse()
            readText='近%s个交易日涨幅最高前三个股是:'%condition[:len(condition)-4]+','.join(futuComInfo(x) for x in rank)
        sortedArr=[]
        for symbol,item in df[:10].iterrows():
            stock={
                'line1':'<b>%s </b>%s'%(symbol,item['股票名称']),
                'line2':'市值'+str(round(item['mktValue']/100000000.0,1)).replace('.0','')+'亿 / '+'周成交'+str(round(item['5daysmoney']/100000000.0,1)).replace('.0','')+'亿 / '+item['Sector'],
                'line3':'&nbsp;&nbsp;&nbsp;'.join(x+'日 +'+str(item[x+'days'])+'%' for x in ['5','20','60']).replace('.0','').replace('+-','-'),
                'close':pd.read_csv(QUOTEPATH+symbol+'.csv',index_col='date')['close'][-60:].tolist()
            }
            sortedArr.append(stock)
        with open(ASSETPATH+'wk_%s.json'%condition, 'w',encoding='utf-8') as outfile:
            json.dump(sortedArr, outfile,ensure_ascii=False)
        videopic='http://127.0.0.1:5500/wk_%s.html'%condition.lower()
        print(videopic)
        genVideo(videopic, readText, 'wk_'+condition)

    videolist = [VideoFileClip(FOLDER + 'wk_'+ x + '.mp4') for x in conditions]
    videolist.insert(0, VideoFileClip(FOLDER + 'week.mp4'))
    final_clip = concatenate_videoclips(videolist, method='compose')
    final_clip.write_videofile(FOLDER + datetime.now().strftime('%m%d')+'_week_' + '_'.join(conditions) + ".mp4")


if __name__=='__main__':
    run()