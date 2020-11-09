import mplfinance as mpf
import matplotlib as mpl  # 用于设置曲线参数
from cycler import cycler  # 用于定制线条颜色
import numpy as np
from lxml import etree
import base64
from matplotlib.font_manager import _rebuild
from idxTrade import *

ENCODE_IN_USE='GBK'

def loadMd(filename,update=False):
    indDf = pd.read_csv('concepts10jqka.csv', encoding='gb18030', dtype=str)
    # indDf.drop(indDf.columns[:1], axis=1,inplace=True)
    # indDf['行业'] = indDf['行业'].str.replace(r"[A-Za-z0-9\!\%\[\]\,\。]", '')
    # indDf.dropna(subset=['symbl'],inplace=True)
    # indDf['所属概念'] = indDf['所属概念'].str.replace(r"[A-Za-z0-9\!\%\[\]\。]", '')
    # indDf['要点'] = indDf['要点'].str.replace("要点", '')
    indDf.set_index('symbl',inplace=True)
    with open (filename,'r') as f:
        line=f.read().split('---')[0].split('***')#f.read().split('---')[1]是图片base64
        mlog('入选数量：',len(line))
        for l in line:
            #0:'',1:'name',2:'symbl',3:'要点',4:'本地图片链接'
            stock=l.split('\n<br>')
            mlog(stock)
            indDf.at[stock[2], 'BAK'] = indDf.loc[stock[2],'要点'].values[0]
            indDf.at[stock[2],'要点']=stock[3]
    if update:
        indDf.to_csv('concepts10jqka'+datetime.now().strftime('%Y%m%d')+'.csv',encoding='gb18030')

def draw(symbol,info,boardDates=[]):
    df = pd.read_csv('Quotation/'+symbol+'.csv',index_col=0,encoding=ENCODE_IN_USE)
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
        title=info[10:-4]+'60天'+str(round(df['Close'][-1]/df['Close'][0]*100-100,2))+'% 最新'+str(round(df['percent'][-1]*100,2))+'% '+str(round(df['amount'][-1]/100000000,2))+'亿',
        # ylabel='OHLCV Candles',
        # ylabel_lower='Shares\nTraded Volume',
        savefig = info,
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
    dfk=dfk.iloc[-25:]
    closes = dfk['close']
    vol = dfk['volume']
    # pct=dfk['percent'].round(2)
    mtm_1 = sum(closes[i]/min(closes[-2],closes[0])-1 for i in range(len(vol)))*vol[-1]/vol[-2]
    mtm_2 = (closes[-10:].mean()-closes[-20:].mean())/(closes[-5:].mean()-closes[-10:].mean()-0.0001)*vol[-5:].mean()/vol[-20:].mean()

    return {'_J':round(mtm_1,12),'_U':round(mtm_2,12)}

def xueqiuBackupByIndustry(mkt=None,pdate=None,test=0):
    # if market == 'cn':
    #     getLimit(pdate.strftime("%Y%m%d"))
    url = "https://xueqiu.com/hq#"
    mlog(url)
    response = requests.get(url=url,headers={"user-agent": "Mozilla","cookie":g.xq_a_token})
    html = etree.HTML(response.text)
    hrefname = html.xpath('//li/a/@title')
    hrefList = html.xpath('//li/a/@href')[2:]
    # mlog(len(hrefname),hrefname,'\n',len(hrefList),hrefList)

    mktDf=pd.DataFrame()
    tqdmRange = tqdm(range(len(hrefList)))
    for i in tqdmRange:
        tqdmRange.set_description((mkt+hrefname[i]).ljust(15))
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
        df.to_csv('Industry/'+mkt+hrefname[i]+indCode+'.csv',encoding=ENCODE_IN_USE)
        # writeIndustry(df[['symbol','name']].copy(), market, hrefname[i], indCode)
        df.dropna(subset=['volume'],inplace=True)
        df['行业']=hrefname[i]
        mktDf = mktDf.append(df)

    mktDf=mktDf.loc[mktDf['current'] >= 1.0]
    mktDf.set_index('symbol',inplace=True)
    mktDf['float_market_capital'] = mktDf['float_market_capital'].astype('float').div(100000000.0).round(1)
    mktDf['market_capital'] = mktDf['market_capital'].astype('float').div(100000000.0).round(1)
    mktDf.to_csv('md/'+mkt+pdate.strftime('%Y%m%d')+'_Bak.csv',encoding=ENCODE_IN_USE)
    return mktDf

def thsIndustry(mkt='cn',pdate=None):
    p_url = 'http://q.10jqka.com.cn/thshy'
    proxies = {}
    # 爬取板块名称以及代码并且存在文件
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'text/html, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'hexin-v': 'As9gGJ-FzGAE3MgcfO1_6HmTWGja9CJ5vUonveHeaU1E3eEe6cSzZs0Yt17y',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
        # 'Referer': 'http://q.10jqka.com.cn/thshy/detail/code/881148/',
        'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
    }
    while True:
        try:
            print(p_url)
            response = requests.get('http://q.10jqka.com.cn/thshy', headers=headers, verify=False,proxies = proxies)
            html = etree.HTML(response.text)
            if 'forbidden.' in response.text:
                if len(proxies)!=0:
                    proxies = {"http": "http://127.0.0.1:7890"}
                else:
                    proxies={}
                    t.sleep(150)
                continue
            break
        except Exception as e:
            mlog(e.args)
            print('retrying...')
            t.sleep(150)
            continue

    gnbk = html.xpath('/html/body/div[2]/div[1]/div//div//div//a')
    thsgnbk = []
    for i in range(len(gnbk)):
        thsgnbk.append((gnbk[i].text))

    # 板块代码
    bkcode = html.xpath('/html/body/div[2]/div[1]/div//div//div//a/@href')
    bkcode = list(map(lambda x: x.split('/')[-2], bkcode))
    data = {'Name': thsgnbk}

    # 存储
    gnbk = pd.DataFrame(data, index=bkcode)
    #symbol,net_profit_cagr,ps,type,percent,has_follow,tick_size,pb_ttm,float_shares,current,amplitude,pcf,current_year_percent,float_float_market_capital,float_market_capital,dividend_yield,lot_size,roe_ttm,total_percent,percent5m,income_cagr,amount,chg,issue_date_ts,main_net_inflows,volume,volume_ratio,pb,followers,turnover_rate,first_percent,name,pe_ttm,total_shares
    #序号	代码	名称	现价 	涨跌幅(%) 	涨跌 	涨速(%) 	换手(%) 	量比 	振幅(%) 	成交额 	流通股 	流通市值 	市盈率
    cols=['symbol','name','current','percent','chg','speed','turnover_rate','qrr','amplitude','amount','float_shares','float_market_capital','pe_ttm','行业']
    indDf=pd.DataFrame(columns=cols)
    tqdmRange = tqdm(gnbk.iterrows(),total=gnbk.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description(v['Name'])
        bk_code = str(k)
        url = p_url + '/detail/code/' + bk_code + '/'
        # print(v['Name'],url)
        headers['Referer']=url
        resp = requests.get(url, headers=headers, verify=False,proxies = proxies)

        # 得出板块成分股有多少页
        html = etree.HTML(resp.text)
        result = html.xpath('//*[@id="m-page"]/span/text()')
        count = 0
        page = 1
        if len(result) > 0:
            page = int(result[0].split('/')[-1])
        rows = []
        while count < page:
            count += 1
            curl = p_url + '/detail/field/199112/order/desc/page/' + str(count) + '/ajax/1/code/' + bk_code
            resp = requests.get(curl, headers=headers, verify=False,proxies = proxies)
            #             print(driver.page_source)
            if 'forbidden.' in resp.text:
                t.sleep(150)
                continue
            html = etree.HTML(resp.text)
            tr=html.xpath('/html/body/table/tbody/tr/td//text()')
            for i in range(14,len(tr),14):
                if str(tr[i-13]).startswith('688'):
                    continue
                elif str(tr[i-13]).startswith('6'):
                    row=['SH'+tr[i-13]]
                else:
                    row=['SZ'+tr[i-13]]
                row.extend(tr[i-12:i])
                row.append(v['Name'])
                rows.append(row)
        pageDf=pd.DataFrame(data=rows,columns=cols)
        pageDf.to_csv('Industry/' + mkt + v['Name'] + bk_code + '.csv', encoding=ENCODE_IN_USE)
        indDf=indDf.append(pageDf)

    indDf.set_index('symbol', inplace=True)
    indDf=indDf.replace('--',np.nan)
    indDf['float_market_capital'] = indDf['float_market_capital'].str.rstrip('亿').astype('float')
    indDf['amount'] = indDf['amount'].str.rstrip('亿').astype('float')
    indDf['current_year_percent']=np.nan
    indDf.to_csv('md/' + mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE)
    return indDf

def dailyCheck(mkt=None,pdate=None,test=0):
    if mkt is None or pdate is None:
        mkt, pdate = g.paramSet['mkt'], g.paramSet['pdate']
        if not pdate:
            return
    if os.path.isfile('md/'+mkt + pdate.strftime('%Y%m%d') + '_Bak.csv'):
        indDf = pd.read_csv('md/'+mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE, dtype={'symbol': str})#防止港股数字
        indDf.set_index('symbol', inplace=True)
    elif mkt=='cn':
        indDf = thsIndustry(mkt, pdate)
    else:
        indDf = xueqiuBackupByIndustry(mkt, pdate, test)
    avgAmount=indDf['amount'].mean()
    indDf=indDf[indDf['amount']>avgAmount]
    indDf = indDf.fillna(value=np.nan)
    indDf=indDf[~indDf['name'].str.contains("N|\*ST", na=False)]
    cal={'_J':[],'_U':[]}
    indDf['filename']=None
    indDf['past60Days']=-999.0
    tqdmRange=tqdm(indDf.iterrows(), total=indDf.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description(("%s %s %s %s"%(mkt, v['行业'], k, v['name'])).ljust(25))
        if g.testMode() and os.path.isfile('Quotation/'+k+'.csv'):
            qdf= pd.read_csv('Quotation/'+k+'.csv',index_col=0, parse_dates=True)
        elif mkt=='cn':
            qdf=cmsK(k)
        else:
            qdf = xueqiuK(symbol=k,startDate=(pdate-timedelta(days=250)).strftime('%Y%m%d'),cookie=g.xq_a_token)
        indDf.at[k, 'past60Days']=round(qdf['close'][-1]/min(qdf['close'][-60:])-1,4)
        info = [mkt, v['行业'], k, v['name']]
        indDf.at[k, 'filename']='plotimage/'+'_'.join(info)+'.png'
        mtm = cauculate(qdf)
        for mk,mv in mtm.items():
            cal[mk].append(mv)
    for k,v in cal.items():
        indDf[k]= v
        df2md(mkt,k,indDf.copy(),pdate)

    mtmDfBAK=indDf[list(cal.keys())].copy()
    mtmDfBAK.to_csv('md/'+mkt+pdate.strftime('%Y%m%d')+'.txt',encoding=ENCODE_IN_USE,index_label='symbol')

    if mkt=='cn' and len(sys.argv)==0:
        idxtrade=idxTrade('cn',0)
        idxtrade.run()

def df2md(mkt,calKey,indDf,pdate,num=10):
    mCap = {'us': 'market_capital', 'cn': 'float_market_capital', 'hk': 'float_market_capital'}[mkt]
    capTpye={'us': '总', 'cn': '流通', 'hk': '港股'}[mkt]
    midMktCap = indDf[mCap].median()
    df=indDf[indDf[mCap]<midMktCap].sort_values(by=[calKey], ascending=True).copy().iloc[:num]
    df[mCap]=df[mCap].apply(str) + '亿'
    df.dropna(subset=[calKey], inplace=True)
    # indDf.groupby('行业').apply(lambda x: x.sort_values(calKey, ascending=True)).to_csv('md/'+ mkt + pdate.strftime('%Y%m%d') + '.csv', encoding=ENCODE_IN_USE)
    # df = df.groupby('行业').apply(lambda x: x.sort_values(calKey, ascending=False))
    article = []
    images=[]
    debts=debt()
    tqdmRange=tqdm(df.iterrows(),total=df.shape[0])
    for k,v in tqdmRange:
        tqdmRange.set_description('【'+calKey+'】'+k+v['name'])
        dfmax=indDf[indDf['行业']==v['行业']].sort_values(by=['past60Days'], ascending=False).iloc[0]
        vlines=[]
        if g.boardlist:
            vlines=g.boardlist.get(k)
        elif not g.testMode():
            vlines=dragonTigerBoard(k,g.xq_a_token)
        if not g.testMode():
            draw(k,v['filename'],vlines)
        elif not os.path.isfile(v['filename']):
            draw(k, v['filename'], vlines)
        deb=debts[debts.index==k]
        with open(v['filename'], "rb") as image_file:
            # image_base64 = '[%s]:data:image/png;base64,%s'%(v['symbl'],base64.b64encode(image_file.read()).decode(ENCODE_IN_USE))
            # images.append(image_base64)
            # artxt=['**'+v['name']+'**'+v['行业'],k[-1],str(v['所属概念'])+'~'+str(v['要点']),'![][%s]'%(v['symbl'])]
            image_base64 = 'data:image/png;base64,%s'%(base64.b64encode(image_file.read()).decode(ENCODE_IN_USE))
            cur_year_perc={k:v['current_year_percent'],dfmax.name:dfmax['current_year_percent']}
            if mkt == 'cn':
                for cnstock in cur_year_perc.keys():
                    mK = cmsK(cnstock, 'monthly')
                    yr=1
                    for i in range(-min(datetime.now().month,len(mK)),0):
                        yr=yr*(1+mK['percent'][i])
                    cur_year_perc[cnstock]=round(yr*100-100,2)
            rowtitle='[%s(%s)](https://xueqiu.com/S/%s) %s市值%s TTM%s 今年%s%%  %s%s'%(v['name'],k,k,capTpye,v[mCap],v['pe_ttm'],cur_year_perc[k],calKey,v[calKey])
            if len(deb)!=0:
                rowtitle='[%s](https://xueqiu.com/S/%s) [%s](https://xueqiu.com/S/%s) %s市值%s亿 TTM%s 今年%s%%  %s%s'%(v['name'],k,'债溢价'+deb['premium_rt'].values[0],deb['id'].values[0],capTpye,v[mCap],v['pe_ttm'],cur_year_perc[k],calKey,v[calKey])
            maxtxt=v['行业']+'行业近60日最强：[%s](https://xueqiu.com/S/%s) %s市值%s亿 TTM%s 60日低点至今涨幅%d%% 今年%s%%'%(dfmax['name'],dfmax.name,capTpye,dfmax[mCap],dfmax['pe_ttm'],dfmax['past60Days']*100,cur_year_perc[dfmax.name])
            artxt=[rowtitle,'![](%s)'%(image_base64),maxtxt]
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
        .replace('TTMnan','亏损')\
        .replace('.0亿','亿')

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
        dailyCheck(test=self.test)

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