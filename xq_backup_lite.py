# -*- coding: utf-8 -*-
import lxml.html
import mplfinance as mpf
import matplotlib as mpl  # 用于设置曲线参数
from cycler import cycler  # 用于定制线条颜色
import numpy as np

import matplotlib.pyplot as plt
import base64
from matplotlib.font_manager import _rebuild
import sys

import markdown
from QuotaUtilities import *
from idxTrade import *

def loadMd(filename,update=False):
    indDf = pd.read_csv('concepts10jqka.csv', encoding='gb18030', dtype=str)
    # indDf.drop(indDf.columns[:1], axis=1,inplace=True)
    # indDf['雪球行业'] = indDf['雪球行业'].str.replace(r"[A-Za-z0-9\!\%\[\]\,\。]", '')
    # indDf.dropna(subset=['雪球代码'],inplace=True)
    # indDf['所属概念'] = indDf['所属概念'].str.replace(r"[A-Za-z0-9\!\%\[\]\。]", '')
    # indDf['要点'] = indDf['要点'].str.replace("要点", '')
    indDf.set_index('雪球代码',inplace=True)
    with open (filename,'r') as f:
        line=f.read().split('---')[0].split('***')#f.read().split('---')[1]是图片base64
        mlog('入选数量：',len(line))
        for l in line:
            #0:'',1:'股票简称',2:'雪球代码',3:'要点',4:'本地图片链接'
            stock=l.split('\n<br>')
            mlog(stock)
            indDf.at[stock[2], 'BAK'] = indDf.loc[stock[2],'要点'].values[0]
            indDf.at[stock[2],'要点']=stock[3]
    if update:
        indDf.to_csv('concepts10jqka'+datetime.now().strftime('%Y%m%d')+'.csv',encoding='gb18030')

def draw(symbol,info,boardDates=[]):
    df = pd.read_csv('Quotation/'+symbol+'.csv',index_col=0,encoding='utf-8')
    df.index=pd.to_datetime(df.index)
    # 导入数据
    # 导入股票数据
    # 格式化列名，用于之后的绘制
    df.rename(
        columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        },
        inplace=True)
    df = df[-60:]
    dt= df.loc[df.index.isin(boardDates)].copy().index.to_list()

    '''
    设置marketcolors
    up:设置K线线柱颜色，up意为收盘价大于等于开盘价
    down:与up相反，这样设置与国内K线颜色标准相符
    edge:K线线柱边缘颜色(i代表继承自up和down的颜色)，下同。详见官方文档)
    wick:灯芯(上下影线)颜色
    volume:成交量直方图的颜色
    inherit:是否继承，选填
    '''
    marketcolors = {'candle': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'edge': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'wick': {'up': 'hotpink', 'down': 'aquamarine'},
                    'ohlc': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'volume': {'up': 'firebrick', 'down': 'seagreen'},
                    'vcdopcod': False,  # Volume Color Depends On Price Change On Day
                    'alpha': 1.0
                    }
    # 设置图形风格
    # gridaxis:设置网格线位置
    # gridstyle:设置网格线线型
    # y_on_right:设置y轴位置是否在右
    rcpdict = {'font.family':'Source Han Sans CN'}
    mystyle = mpf.make_mpf_style(
        base_mpf_style='mike',
        rc=rcpdict,
        gridaxis='both',
        gridstyle='-',
        gridcolor='#393f52',
        y_on_right=True,
        marketcolors=marketcolors,
        figcolor='#20212A',
        facecolor='#20212A',
        edgecolor='#393f52',
    )

    '''
    设置基本参数
    type:绘制图形的类型，有candle, renko, ohlc, line等
    此处选择candle,即K线图
    mav(moving average):均线类型,此处设置7,30,60日线
    volume:布尔类型，设置是否显示成交量，默认False
    title:设置标题
    y_label:设置纵轴主标题
    y_label_lower:设置成交量图一栏的标题
    figratio:设置图形纵横比
    figscale:设置图形尺寸(数值越大图像质量越高)
    '''
    kwargs = dict(
        style=mystyle,
        type='candle',
        volume=True,
        mav=(5,10,20),
        title=info+'60天'+str(round(df['Close'][-1]/df['Close'][0]*100-100,2))+'% 最新'+str(df['percent'][-1])+'% '+str(round(df['amount'][-1]/100000000,3))+'亿',
        # ylabel='OHLCV Candles',
        # ylabel_lower='Shares\nTraded Volume',
        savefig = 'plotimage/%s'% (info) ,
        figratio=(8, 5),
        figscale=1,
        tight_layout=True,
        vlines=dict(vlines=dt, linewidths=8, alpha=0.2, colors='khaki')
    )

    # 设置均线颜色，配色表可见下图
    # 建议设置较深的颜色且与红色、绿色形成对比
    # 此处设置七条均线的颜色，也可应用默认设置
    mpl.rcParams['axes.prop_cycle'] = cycler(
        color=['dodgerblue', 'deeppink',
               'navy', 'teal', 'maroon', 'darkorange',
               'indigo'])

    # 图形绘制
    # show_Uontrading:是否显示非交易日，默认False
    # savefig:导出图片，填写文件名及后缀
    mpf.plot(df, **kwargs,scale_width_adjustment=dict(volume=0.5,candle=1,lines=0.5))
    plt.show()

def cauculate(dfk):
    if len(dfk['close'].values)<44:
        return {'_J':np.nan,'_U':np.nan}
    # ma =dfk['close'].rolling(window=3).mean()
    closes = dfk['close'].values
    mtm_1 = [closes[i]/min(closes[-20],closes[-1]) - 1 for i in range(-25,0)]
    mtm_2 = [closes[i]/min(closes[-20],closes[-1]*(1+max(dfk['percent'][-20:])*2)) - 1 for i in range(-20,0)]
    cal = sum(mtm_1)
    cal2 = sum(mtm_2)-sum(closes[i]/max(closes[-10],closes[-30]) - 1 for i in range(-30,-20))
    return {'_J':round(cal,12),'_U':round(cal2,12)}

def xueqiuBackupByIndustry(mkt=None,pdate=None,bak=False):
    # if market == 'cn':
    #     getLimit(pdate.strftime("%Y%m%d"))
    url = "https://xueqiu.com/hq#"
    mlog(url)
    response = requests.get(url=url,headers={"user-agent": "Mozilla","cookie":g.xq_a_token})
    html = lxml.html.etree.HTML(response.text)
    hrefname = html.xpath('//li/a/@title')
    hrefList = html.xpath('//li/a/@href')[2:]
    # mlog(len(hrefname),hrefname,'\n',len(hrefList),hrefList)

    mktDf=pd.DataFrame()
    tqdmRange = tqdm(range(len(hrefList)))
    for i in tqdmRange:
        tqdmRange.set_description(mkt+hrefname[i])
        if '#exchange=' + mkt.upper() not in hrefList[i] or 'code=' not in hrefList[i]:
            continue
        indCode = hrefList[i].split('=')[-1]
        mlog(mkt,hrefname[i])
        df = pd.DataFrame()
        page=1
        while True:
            try:
                indUrl='https://xueqiu.com/service/v5/stock/screener/quote/list?page={page}&size=90&order=desc&order_by=percent&exchange={mkt}&market={mkt}&ind_code={code}'.format(page=page,mkt=mkt,code=indCode)
                mlog(indUrl)
                resp = requests.get(url=indUrl, headers={"user-agent": "Mozilla", "cookie": g.xq_a_token})
                data=json.loads(resp.text)
                if data['data']['count']==0:
                    break
                for b in data['data']['list']:
                    dict_ = []
                    for a in data['data']['list'][0].keys():
                        dict_.append(b[a])
                    dicts = []
                    dicts.append(dict_)
                    ans = pd.DataFrame(dicts, columns=data['data']['list'][0].keys())
                    df = df.append(ans)
                if page>int(int(data['data']['count'])/90):
                    break
                page+=1
            except Exception as e:
                mlog(e.args)
                mlog('retrying...')
                t.sleep(20)
                continue
        if len(df)==0:
            continue
        df.drop_duplicates(subset='symbol', keep='first', inplace=True)
        df.to_csv('Industry/'+mkt+hrefname[i]+indCode+'.csv',encoding='UTF-8')
        # writeIndustry(df[['symbol','name']].copy(), market, hrefname[i], indCode)
        bakDf=df[['symbol','current','percent','current_year_percent', "volume","amount",'turnover_rate','pe_ttm','dividend_yield','float_market_capital','market_capital']].copy()
        bakDf.dropna(subset=['volume'],inplace=True)
        mktDf = mktDf.append(bakDf)
        if not bak:
            mktDf=mktDf.append(bakDf)
    mktDf=mktDf.loc[mktDf['current'] >= 1.0]
    mktDf.set_index(['symbol']).to_csv('md/'+mkt+pdate.strftime('%Y%m%d')+'_Bak.csv',encoding='UTF-8')
    return mktDf

def dailyCheck(mkt=None,pdate=None):
    if mkt is None or pdate is None:
        mkt, pdate = g.paramSet['mkt'], g.paramSet['pdate']
        if not pdate:
            return
    if os.path.isfile('md/'+mkt + pdate.strftime('%Y%m%d') + '_Bak.csv'):
        df = pd.read_csv('md/'+mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding='UTF-8', dtype={'symbol': str})
    else:
        df = xueqiuBackupByIndustry(mkt, pdate)
    df.set_index(['symbol'], inplace=True)
    if mkt=='cn' and g.boardlist:
        df=df.loc[df.index.isin(g.boardlist.keys())].copy()
    else:
        avgAmount=df['amount'].mean()
        df=df[df['amount']>avgAmount]
        midMktCap=df['market_capital'].median()
        df=df[df['market_capital']<midMktCap]
    df = df.fillna(value=np.nan)
    indDf=pd.read_csv('concepts10jqka.csv',encoding='GBK',dtype=str)
    indDf=indDf.loc[indDf['雪球代码'].isin(df.index)].copy()
    indDf.dropna(subset=['雪球行业'],inplace=True)
    indDf=indDf[~indDf['股票简称'].str.contains("N|\*ST", na=False)]
    # top25Ind='S1107,S2701,S1104,S3602,S2702,S1106,S2202,S3403,S1108,S2102,S2705,S2703,S4302,S6103,S7101,S6504,S7102,S4201,S6403,S3705,S4602,S2203,S3502,S3701,S6204,2820,3030,2520,2530,3045,z60,z20,2810,0520,7020,2050,z30,7030,z40,7010,0530,1010,0010,5030,z70,0020,6020,0510,2510,z10,52020,02030,02020,303020,201020,401020,255020,502030,351030,203030,452010,402020,202020,253010,551050,252010,255040,352010,151050,203010,451020,302020,452020,151040,453010'
    # indDf = indDf.loc[indDf['雪球行业代码'].isin(top25Ind.split(','))].copy()
    mlog(len(indDf))
    cal={'_J':[],'_U':[]}
    indDf.set_index(['雪球代码'], inplace=True)
    indDf['filename'],indDf['percent'],indDf['current_year_percent'],indDf['market_capital'],indDf['pe_ttm']=None,None,None,None,np.nan
    tqdmRange=tqdm(indDf.iterrows(), total=indDf.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description("%s %s %s %s"%(v['市场'], v['雪球行业'], k, v['股票简称']))
        indDf.at[k, 'percent'] = df.loc[k,'percent'].values[0]
        indDf.at[k, 'current_year_percent'] = df.loc[k, 'current_year_percent'].values[0]
        indDf.at[k, 'market_capital'] = round(df.loc[k, 'market_capital'].values[0]/100000000.0,1)
        indDf.at[k, 'pe_ttm'] = round(df.loc[k, 'pe_ttm'].values[0],1)#round(np.nan,1)==nan
        if g.testMode() and os.path.isfile('Quotation/'+k+'.csv'):
            qdf= pd.read_csv('Quotation/'+k+'.csv',index_col=0, parse_dates=True)
        elif mkt=='cn':
            qdf=cmsK(k)
        else:
            qdf = xueqiuK(symbol=k,startDate=(pdate-timedelta(days=250)).strftime('%Y%m%d'),cookie=g.xq_a_token)
        info = [v['市场'], v['雪球行业'], k, v['股票简称']]
        indDf.at[k, 'filename']='_'.join(info)+'.png'
        mtm = cauculate(qdf)
        for mk,mv in mtm.items():
            cal[mk].append(mv)

    for k,v in cal.items():
        indDf[k]= v
        df2md(mkt,k,indDf.copy(),pdate)
    indDf.to_csv('md/'+mkt+pdate.strftime('%Y%m%d')+'mtm.csv',encoding='UTF-8')
    if mkt=='cn' and len(sys.argv)==0:
        idxtrade=idxTrade('cn',0)
        idxtrade.run()

def df2md(mkt,calKey,df,pdate,num=36):
    df.dropna(subset=[calKey],inplace=True)
    df.groupby('雪球行业').apply(lambda x: x.sort_values(calKey, ascending=True)).to_csv('md/'+ mkt + pdate.strftime('%Y%m%d') + '.csv', encoding='UTF-8')
    df=df.sort_values(by=[calKey], ascending=True)[:num]#指标排序前100
    # df = df.groupby('雪球行业').apply(lambda x: x.sort_values(calKey, ascending=False))
    article = []
    images=[]
    debts=debt()
    for k,v in df.iterrows():
        vlines=[]
        if g.boardlist:
            vlines=g.boardlist.get(k)
        else:
            vlines=dragonTigerBoard(k,g.xq_a_token)
        draw(k,'_'.join([v['市场'], v['雪球行业'], k, v['股票简称']]) + '.png',vlines)
        deb=debts[debts.index==k]
        with open("plotimage/"+v['filename'], "rb") as image_file:
            # image_base64 = '[%s]:data:image/png;base64,%s'%(v['雪球代码'],base64.b64encode(image_file.read()).decode('utf-8'))
            # images.append(image_base64)
            # artxt=['**'+v['股票简称']+'**'+v['雪球行业'],k[-1],str(v['所属概念'])+'~'+str(v['要点']),'![][%s]'%(v['雪球代码'])]
            image_base64 = 'data:image/png;base64,%s'%(base64.b64encode(image_file.read()).decode('utf-8'))
            rowtitle='[%s](https://xueqiu.com/S/%s) 总市值%s亿 TTM%s 今年%s%%  %s%s'%(v['股票简称'],k,v['market_capital'],v['pe_ttm'],v['current_year_percent'],calKey,v[calKey])
            if len(deb)!=0:
                rowtitle='[%s](https://xueqiu.com/S/%s) [%s](https://xueqiu.com/S/%s) 总市值%s亿 TTM%s 今年%s%%  %s%s'%(v['股票简称'],k,'债溢价'+deb['premium_rt'].values[0],deb['id'].values[0],v['market_capital'],v['pe_ttm'],v['current_year_percent'],calKey,v[calKey])
            artxt=[rowtitle,k,str(v['要点']),'![](%s)'%(image_base64)]
            article.append('\n<br>'+'\n<br>'.join([str(x) for x in artxt]))
    txt = '\n***'.join(article)
    title=mkt+calKey+pdate.strftime('%Y%m%d')
    # with open('md/'+title+'.md','w') as f:
    #     # f.write('\n***'.join(article)+'\n\n---\n'+'\n'.join(images))
    #     f.write(txt)
    html = markdown.markdown('#'+title+'#'+txt)\
        .replace('<a','<a class="button is-rounded is-dark"')\
        .replace('/a>','/a><br/>')\
        .replace('a><br/> <a','a><a')\
        .replace('<hr />','<br/><br/>')\
        .replace('TTMnan','亏损')

    gAds='''<script data-ad-client="ca-pub-7398757278741889" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>'''

    css='<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge">\
    <meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>\
    <link href="https://cdn.jsdelivr.net/npm/bulma@0.9.0/css/bulma.min.css"rel="stylesheet">{gAds}</head>\
        <body class="has-background-grey-dark has-text-white-ter"><div class="container">\
        <div class="columns is-centered"><div class="column is-two-thirds"><article class="section">'.format(title=title,gAds=gAds)
    with open('../html/'+mkt+str(pdate.weekday()+1)+calKey+'.html', 'w') as f:
        finalhtml=css+html+'<p><br/>© Frank Lin 2020</p></ariticle></div></div></div></body></html>'
        f.write(finalhtml)
        mlog('complete ' + title)
        if g.testMode():
            return finalhtml


def preparePlot():
    mlog(mpl.matplotlib_fname())
    mpl.rcParams['font.family'] = ['sans-serif']
    mpl.rcParams['font.sans-serif']=['Source Han Sans CN']  # 用来正常显示中文标签
    mpl.rcParams['axes.unicode_minus']=False  # 用来正常显示负号
    _rebuild()

class params:
    def __init__(self,market=None,test=0):
        self.test=test
        self.xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies[
            'xq_a_token'] + ';'
        mkt,cfg = checkTradingDay(market)#交易时间
        self.paramSet={'mkt':mkt, 'pdate':cfg[mkt]['date']}
        self.boardlist={}

    def go(self):
        # if self.test:
        #     print(sys.argv)
        #     mkt = sys.argv[1]
        #     dateArg = [int(x) for x in sys.argv[2].split('/')]
        #     pdate = datetime.(dateArg[0], dateArg[1], dateArg[2])
        #     df = pd.read_csv('md/' + mkt + pdate.strftime('%Y%m%d') + 'mtm.csv', encoding='UTF-8', dtype=str)
        #     df.set_index(['雪球代码'], inplace=True)cal
        #     for k in {'_J': [], '_U': []}.keys():
        #          mdcontent=df2md(mkt, k, df.copy(), pdate)
        #         # send_email(mkt+k+pdate.strftime('%Y%m%d'),mdcontent)
        #     exit()
        dailyCheck()

    def testMode(self):
        return self.test

if __name__=='__main__':
    preparePlot()
    logging.basicConfig(
        filename='daily.log',
        level=logging.DEBUG
    )
    if len(sys.argv) > 1:
        g = params(market=sys.argv[1],test=int(sys.argv[2]))
    else:
        g=params()
    g.go()