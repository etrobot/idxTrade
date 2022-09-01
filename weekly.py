import urllib.request,csv,json
from video import *
from QuotaUtilities import *

PROXY = {
    'http': 'http://127.0.0.1:8081',  # 访问http需要
    'https': 'https://127.0.0.1:8081',  # 访问https需要
}
QUOTEPATH='Quotation/'
ASSETPATH='video/'
IFREAD=True

def invesco(etfCode):
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

def weekVideo(readText:str,subTitle='',read=True):
    symbols={'IXIC':'纳斯达克','DJI':'道琼斯','INX':'标普500'}
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    # symbols = {'DIA':'道琼斯ETF', 'QQQ':'纳斯卡克ETF', 'SPY':'标普500ETF'}
    sortedArr=[]
    for symbol,name in symbols.items():
        k=getK('.'+symbol,pdate=datetime.now()-timedelta(days=180),xq_a_token=xq_a_token)['close']
        stock={
            'symbol':symbol,
            'line1':name,
            'line3': '5日 %s%%&nbsp;&nbsp;&nbsp;20日 %s%%&nbsp;&nbsp;&nbsp;60日 %s%%'%(round(k[-1]*100/k[-6]-100,2),round(k[-1]*100/k[-21]-100,2),round(k[-1]*100/k[-61]-100,2)),
            'close':k[-61:].tolist()
        }
        sortedArr.append(stock)
    with open(ASSETPATH+'week.json', 'w',encoding='utf-8') as outfile:
        json.dump(sortedArr, outfile,ensure_ascii=False)
    with open("Template/weekTemp.xhtml", "r") as fin:
        with open(ASSETPATH + "week%s.html"%subTitle, "w") as fout:
            fout.write(fin.read().replace('{{text}}', readText))
    videopic='http://127.0.0.1:5500/week%s.html'%subTitle
    print(videopic)
    genVideo(videopic, readText, 'week'+subTitle,read,canvas=True)


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
    df=df[~df.index.str.contains('_')]
    df=df[(df.index != 'GOOG')]
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

    conditions=['mktValue','5daysmoney','20days','5days']
    for condition in conditions:
        df.sort_values(by=[condition],ascending=False,inplace=True)
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

    for condition in conditions:
        if condition=='mktValue':
            readText='当前美股市值前十大企业为：'+ ','.join(df['股票名称'][:10].tolist()).replace('-A','')
        elif condition=='5daysmoney':
            readText='本周美股成交前十大股票为：'+ ','.join(df['股票名称'][:10].tolist())
        else:
            rank=df.index[:3].tolist()
            names=df['股票名称'][:3].tolist()
            readText='美股近%s个交易日涨幅最高前三个股是:'%condition[:len(condition)-4]+','.join(names)+'；'+','.join(futuComInfo(x) for x in rank)
        with open('Template/wk_%s.xhtml'%condition, "r") as fin:
            with open(ASSETPATH + 'wk_%s.html'%condition, "w") as fout:
                fout.write(fin.read())
        videopic='http://127.0.0.1:5500/wk_%s.html'%condition.lower()
        print(videopic)
        genVideo(videopic, readText, 'wk_'+condition,IFREAD)

    conf = configparser.ConfigParser()
    conf.read('config.ini')
    weekVideo(conf['weekend']['conclusion'],'end',IFREAD)
    weekVideo(conf['weekend']['begin'],read=IFREAD)
    videolist = [VideoFileClip(ASSETPATH + 'wk_'+ x + '.mp4') for x in conditions]
    videolist.insert(0, VideoFileClip(ASSETPATH + 'week.mp4'))
    videolist.append(VideoFileClip(ASSETPATH + 'weekend.mp4'))
    final_clip = concatenate_videoclips(videolist, method='compose')
    final_clip.write_videofile(ASSETPATH + datetime.now().strftime('%m%d')+'_week_' + '_'.join(conditions) + ".mp4")


if __name__=='__main__':
    run()