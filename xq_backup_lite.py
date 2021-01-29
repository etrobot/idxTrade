import mplfinance as mpf
import matplotlib as mpl  # 用于设置曲线参数
from cycler import cycler  # 用于定制线条颜色
import numpy as np
from lxml import etree
from matplotlib.font_manager import _rebuild
from idxTrade import *
from selenium import webdriver

ENCODE_IN_USE = 'GBK'
IMG_FOLDER = '../upknow/'


def updateAllImg(mkt, pdate, calKeys):
    tqdmRange = tqdm(range(0, 5))
    drawedSymbolList = []
    for i in tqdmRange:
        if pdate.weekday() != i:
            for calKey in calKeys:  # 加入url参数（小时），让浏览器不使用缓存
                filename = '../etrobot.github.io/Quant/%s%s%s.html' % (mkt, i + 1, calKey)
                if os.path.isfile(filename):
                    with open(filename, "r+") as f:
                        output = re.sub('\?t=.*"', '?t=%s"' % datetime.now().strftime("%m%d%H"), f.read())
                        output=output.replace(IMG_FOLDER,'https://upknow.gitee.io/')
                        f.seek(0)
                        f.write(output)
                        f.truncate()
            imgfolder = IMG_FOLDER + str(i + 1) + '/' + mkt + '/'
            fileList = os.listdir(imgfolder)
            for filename in fileList:
                if filename[-4:] == '.png':
                    tqdmRange.set_description('update ' + imgfolder + filename)
                    symbol = filename.split('_')[2]
                    qdf = getK(symbol, pdate,g.xq_a_token,int(symbol in drawedSymbolList))
                    draw(qdf, imgfolder + filename,dragonTigerBoard(symbol,g.xq_a_token))
                    drawedSymbolList.append(symbol)


def draw(df, info, boardDates=()):
    # 导入数据
    # 导入股票数据
    # 格式化列名，用于之后的绘制
    df.index.names=['date']
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
    dt = df.loc[df.index.isin(boardDates)].copy().index.to_list()
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
    rcpdict = {'font.family': 'Source Han Sans CN'}
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
        mav=(5, 10, 20),
        title=info[len(IMG_FOLDER + '1/cn/'):-4] + '60天' + str(
            round(df['Close'][-1] / df['Close'][0] * 100 - 100, 2)) + '% 最新' + str(
            round(df['percent'][-1] * 100, 2)) + '% 额' + str(round(df['amount'][-1] / 100000000, 2)) + '亿',
        # ylabel='OHLCV Candles',
        # ylabel_lower='Shares\nTraded Volume',
        savefig=info,
        figratio=(8, 5),
        figscale=1,
        tight_layout=True,
    )
    if len(dt)>0:
        kwargs['vlines']=dict(vlines=dt, linewidths=8, alpha=0.2, colors='khaki')
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
    mpf.plot(df, **kwargs, scale_width_adjustment=dict(volume=0.5, candle=1, lines=0.5))
    plt.show()


def cauculate(dfk):
    if len(dfk['close'].values) < 44:
        return {'_J': np.nan, '_U': np.nan}
    # ma =dfk['close'].rolling(window=3).mean()
    dfk = dfk.iloc[-25:]
    closes = dfk['close']
    vol = dfk['volume']
    # pct=dfk['percent'].round(2)
    mtm_1 = abs(closes[-10:].mean()-closes.mean())/(closes[-20]-closes[-1])*closes[-7:].argmax()
    mtm_2 = (closes[-10:].mean()-closes.mean())/((max(closes[-5:])+min(closes[-5:]))/2-closes[-10:].mean())*vol.argmin()
    return {'_U': round(mtm_2, 12), '_J': round(mtm_1, 12)}


def xueqiuBackupByIndustry(mkt=None, pdate=None, test=0):
    # if market == 'cn':
    #     getLimit(pdate.strftime("%Y%m%d"))
    url = "https://xueqiu.com/hq#"
    mlog(url)
    response = requests.get(url=url, headers={"user-agent": "Mozilla", "cookie": g.xq_a_token})
    html = etree.HTML(response.text)
    hrefname = html.xpath('//li/a/@title')
    hrefList = html.xpath('//li/a/@href')[2:]
    # mlog(len(hrefname),hrefname,'\n',len(hrefList),hrefList)
    mktDf = pd.DataFrame()
    tqdmRange = tqdm(range(len(hrefList)))
    for i in tqdmRange:
        tqdmRange.set_description((mkt + hrefname[i]).ljust(15))
        if '#exchange=' + mkt.upper() not in hrefList[i] or 'code=' not in hrefList[i]:
            continue
        indCode = hrefList[i].split('=')[-1]
        mlog(mkt, hrefname[i])
        df = pd.DataFrame()
        page = 1
        while True:
            try:
                indUrl = 'https://xueqiu.com/service/v5/stock/screener/quote/list?page={page}&size=90&order=desc&order_by=percent&exchange={mkt}&market={mkt}&ind_code={code}'.format(
                    page=page, mkt=mkt, code=indCode)
                mlog(indUrl)
                resp = requests.get(url=indUrl, headers={"user-agent": "Mozilla", "cookie": g.xq_a_token})
                data = json.loads(resp.text)
                if data['data']['count'] == 0:
                    break
                for b in data['data']['list']:
                    dict_ = []
                    for a in data['data']['list'][0].keys():
                        dict_.append(b[a])
                    dicts = []
                    dicts.append(dict_)
                    ans = pd.DataFrame(dicts, columns=data['data']['list'][0].keys())
                    df = df.append(ans)
                if page > int(int(data['data']['count']) / 90):
                    break
                page += 1
            except Exception as e:
                mlog(e.args)
                mlog('retrying...')
                t.sleep(20)
                continue
        if len(df) == 0:
            continue
        df.drop_duplicates(subset='symbol', keep='first', inplace=True)
        df.to_csv('Industry/' + mkt + hrefname[i] + indCode + '.csv', encoding=ENCODE_IN_USE)
        # writeIndustry(df[['symbol','name']].copy(), market, hrefname[i], indCode)
        df.dropna(subset=['volume'], inplace=True)
        df['行业'] = hrefname[i]
        mktDf = mktDf.append(df)
    mktDf = mktDf.loc[mktDf['current'] >= 1.0]
    mktDf.set_index('symbol', inplace=True)
    mktDf['float_market_capital'] = mktDf['float_market_capital'].astype('float').div(100000000.0).round(1)
    mktDf['market_capital'] = mktDf['market_capital'].astype('float').div(100000000.0).round(1)
    mktDf.to_csv('md/' + mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE)
    return mktDf

def usHot(pdate:date,xq_a_token:str):
    mktDf=pd.DataFrame()
    for ustype in ['us_star','us_china']:
        page=0
        while True:
            try:
                page+=1
                url='https://xueqiu.com/service/v5/stock/screener/quote/list?page=%s&size=90&order=desc&orderby=percent&order_by=percent&market=US&type=%s'%(page,ustype)
                resp = requests.get(url=url, headers={"user-agent": "Mozilla", "cookie": xq_a_token})
                data = json.loads(resp.text)
                if len(data['data']['list']) == 0:
                    break
                df=pd.DataFrame(data['data']['list'])
                df['行业'] = {'us_star': '美明星股', 'us_china': '中概股'}[ustype]
                mktDf=mktDf.append(df)
            except Exception as e:
                mlog(e.args)
                mlog('retrying...')
                t.sleep(20)
                continue
    mktDf = mktDf.loc[mktDf['current'] >= 1.0]
    mktDf.set_index('symbol', inplace=True)
    mktDf['float_market_capital'] = mktDf['float_market_capital'].astype('float').div(100000000.0).round(1)
    mktDf['market_capital'] = mktDf['market_capital'].astype('float').div(100000000.0).round(1)
    mktDf.to_csv('md/' + 'us' + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE)
    return mktDf

def thsIndustry(mkt='cn', pdate=None):
    p_url = 'http://q.10jqka.com.cn/thshy'
    start = t.time()
    # 爬取板块名称以及代码并且存在文件
    while True:
        try:
            response = requests.get(p_url, headers={"user-agent": "Mozilla"})
            html = etree.HTML(response.text)
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
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    # with open('stealth.min.js') as f:
    #     js = f.read()
    #     driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #         "source": js
    #     })
    # 板块代码
    bkcode = html.xpath('/html/body/div[2]/div[1]/div//div//div//a/@href')
    bkcode = list(map(lambda x: x.split('/')[-2], bkcode))
    data = {'Name': thsgnbk}
    # 存储
    gnbk = pd.DataFrame(data, index=bkcode)
    # symbol,net_profit_cagr,ps,type,percent,has_follow,tick_size,pb_ttm,float_shares,current,amplitude,pcf,current_year_percent,float_float_market_capital,float_market_capital,dividend_yield,lot_size,roe_ttm,total_percent,percent5m,income_cagr,amount,chg,issue_date_ts,main_net_inflows,volume,volume_ratio,pb,followers,turnover_rate,first_percent,name,pe_ttm,total_shares
    # 序号	代码	名称	现价 	涨跌幅(%) 	涨跌 	涨速(%) 	换手(%) 	量比 	振幅(%) 	成交额 	流通股 	流通市值 	市盈率
    cols = ['symbol', 'name', 'current', 'percent', 'chg', 'speed', 'turnover_rate', 'qrr', 'amplitude', 'amount',
            'float_shares', 'float_market_capital', 'pe_ttm', '行业']
    indDf = pd.DataFrame(columns=cols)
    tqdmRange = tqdm(gnbk.iterrows(), total=gnbk.shape[0])
    last=[]
    for k, v in tqdmRange:
        tqdmRange.set_description(v['Name'])
        bk_code = str(k)
        url = p_url + '/detail/code/' + bk_code + '/'
        driver.get(url)
        # print(v['Name'],url)
        # 得出板块成分股有多少页
        content = driver.page_source
        html = etree.HTML(content)
        result = html.xpath('//*[@id="m-page"]/span/text()')
        count = 1
        page = 1
        if len(result) > 0:
            page = int(result[0].split('/')[-1])
        headers = {"user-agent": "Mozilla", "Cookie": "v={}".format(driver.get_cookies()[0]["value"])}
        # lasturl='http://d.10jqka.com.cn/v4/time/bk_%s/last.js'%bk_code
        # driver.get(lasturl)
        # lastJson=re.findall(r'data":"(.*)","dotsCount',driver.page_source)[0].split(';')
        # bkQuot=[float(x.split(',')[1]) for x in lastJson][-60:]
        # last.append([v['Name'],bkQuot[-1]/bkQuot[0]])
        rows = []
        while count <= page:
            curl = p_url + '/detail/field/199112/order/desc/page/' + str(count) + '/ajax/1/code/' + bk_code
            if count > 1 and 'forbidden.' not in driver.page_source and driver.current_url != curl:
                content = requests.get(curl, headers=headers).text
            html = etree.HTML(content)
            if '暂无成份股数据' in content:
                count += 1
                continue
            tr = html.xpath('//td//text()')
            if len(tr) == 0:  # cookie失效
                driver.get(curl)
                content = driver.page_source
                if 'forbidden.' in content:
                    t.sleep(60)
                    continue
                headers["Cookie"] = "v={}".format(driver.get_cookies()[0]["value"])
                continue
            for i in range(14, len(tr) + 14, 14):
                # if str(tr[i-13]).startswith('688'):
                #     continue
                if str(tr[i - 13]).startswith('6'):
                    row = ['SH' + tr[i - 13]]
                else:
                    row = ['SZ' + tr[i - 13]]
                row.extend(tr[i - 12:i])
                row.append(v['Name'])
                rows.append(row)
            count += 1
        pageDf = pd.DataFrame(data=rows, columns=cols)
        pageDf['pe_ttm'] = pageDf['pe_ttm'].apply(pd.to_numeric, errors='coerce')
        pageDf.to_csv('Industry/' + mkt + v['Name'] + bk_code + '.csv', encoding=ENCODE_IN_USE)
        indDf = indDf.append(pageDf)
    driver.quit()
    end = t.time()
    print(p_url + '爬取结束！！\n开始时间：%s\n结束时间：%s\n' % (t.ctime(start), t.ctime(end)))
    indDf.set_index('symbol', inplace=True)
    indDf = indDf.replace('--', np.nan)
    indDf['float_market_capital'] = indDf['float_market_capital'].str.rstrip('亿').astype('float')
    indDf['amount'] = indDf['amount'].str.rstrip('亿').astype('float')
    indDf['current_year_percent'] = np.nan
    indDf.to_csv('md/' + mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE)
    return indDf


def dailyCheck(mkt=None, pdate=None, test=0):
    if mkt is None or pdate is None:
        mkt, pdate = g.paramSet['mkt'], g.paramSet['pdate']
        if not pdate:
            return
    if os.path.isfile('md/' + mkt + pdate.strftime('%Y%m%d') + '_Bak.csv'):
        indDf = pd.read_csv('md/' + mkt + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE,
                            dtype={'symbol': str})  # 防止港股数字
        indDf.set_index('symbol', inplace=True)
    elif mkt == 'cn':
        indDf = thsIndustry(mkt, pdate)
    elif mkt=='us':
        indDf=usHot(pdate,g.xq_a_token)
    else:
        indDf = xueqiuBackupByIndustry(mkt, pdate, test)
    avgAmount = indDf['amount'].mean()
    indDf = indDf[indDf['amount'] > avgAmount]
    indDf = indDf.fillna(value=np.nan)
    indDf = indDf[~indDf.index.str.startswith("SH688", na=False)]
    indDf = indDf[~indDf['name'].str.contains("N|\*ST", na=False)]
    cal = {'_J': [], '_U': []}
    indDf['filename'] = None
    indDf['past60Days'] = -999.0
    tqdmRange = tqdm(indDf.iterrows(), total=indDf.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description(("%s %s %s %s" % (mkt, v['行业'], k, v['name'])).ljust(25))
        qdf = getK(k, pdate,g.xq_a_token, test)
        indDf.at[k, 'past60Days'] = round(qdf['close'][-1] / min(qdf['close'][-60:]) - 1, 4)
        info = [mkt, v['行业'], k, v['name']]
        indDf.at[k, 'filename'] = IMG_FOLDER + str(pdate.weekday() + 1) + '/' + mkt + '/' + '_'.join(
            info) + '.png'
        mtm = cauculate(qdf)
        for mk, mv in mtm.items():
            cal[mk].append(mv)
    for k, v in cal.items():
        indDf[k] = v
        df2md(mkt, k, indDf.copy(), pdate, test)
    mtmDfBAK = indDf[list(cal.keys())].copy()
    mtmDfBAK.to_csv('md/' + mkt + pdate.strftime('%Y%m%d') + '.txt', encoding=ENCODE_IN_USE, index_label='symbol')
    updateAllImg(mkt, pdate, cal.keys())
    if len(sys.argv) == 2:
        idxtrade = idxTrade(mkt, 0)
        idxtrade.run()


def df2md(mkt, calKey, indDf, pdate, test=0, num=10):
    mCap = {'us': 'market_capital', 'cn': 'float_market_capital', 'hk': 'float_market_capital'}[mkt]
    capTpye = {'us': '总', 'cn': '流通', 'hk': '港股'}[mkt]
    midMktCap = indDf[mCap].median()
    df = indDf.dropna(subset=[calKey])
    if mkt=='cn':
        if calKey=='_U':
            df=df[df.index.isin(g.boardlist.keys())].sort_values(by=[calKey], ascending=True).iloc[:num]
        else:
            df = df[df.index.isin(getLimit(pdate)['代码'])].sort_values(by=[calKey], ascending=True).iloc[:num]
    else:
        df = df[df[mCap] < midMktCap].sort_values(by=[calKey], ascending=True).iloc[:num]
    df[mCap] = df[mCap].apply(str) + '亿'
    article = []
    drawedSymbolList = []
    debts = debt()
    tqdmRange = tqdm(df.iterrows(), total=df.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description('【' + calKey + '】' + k + v['name'])
        dfmax = indDf[indDf['行业'] == v['行业']].sort_values(by=['past60Days'], ascending=False).iloc[0]
        vlines = []
        if g.boardlist:
            vlines = g.boardlist.get(k,[])
        elif not g.testMode():
            vlines = dragonTigerBoard(k, g.xq_a_token)
        if not g.testMode() and k not in drawedSymbolList:
            qdf = getK(k, pdate,g.xq_a_token, 1)
            draw(qdf, v['filename'], vlines)
            drawedSymbolList.append(k)
        elif not os.path.isfile(v['filename']):
            qdf = getK(k, pdate,g.xq_a_token, 1)
            draw(qdf, v['filename'], vlines)
        deb = debts[debts.index == k]
        cur_year_perc = {k: v['current_year_percent'], dfmax.name: dfmax['current_year_percent']}
        if mkt == 'cn':
            for cnstock in cur_year_perc.keys():
                mK = cmsK(cnstock, 'monthly')
                yr = 1
                for i in range(-min(datetime.now().month, len(mK)), 0):
                    yr = yr * (1 + mK['percent'][i])
                cur_year_perc[cnstock] = round(yr * 100 - 100, 2)
        rowtitle = '[%s(%s)](https://xueqiu.com/S/%s) %s市值%s TTM%s 今年%s%%  %s' % (
            v['name'], k, k, capTpye, v[mCap], v['pe_ttm'], cur_year_perc[k], calKey)
        if len(deb) != 0:
            rowtitle = '[%s](https://xueqiu.com/S/%s) [%s](https://xueqiu.com/S/%s) %s市值%s亿 TTM%s 今年%s%%  %s%s' % (
                v['name'], k, '债溢价' + deb['premium_rt'].values[0], deb['id'].values[0], capTpye, v[mCap],
                v['pe_ttm'], cur_year_perc[k], calKey, v[calKey])
        maxtxt = v['行业'] + '板块近60日最强：[%s](https://xueqiu.com/S/%s) %s市值%s亿 TTM%s 60日低点至今涨幅%d%% 今年%s%%' % (
            dfmax['name'], dfmax.name, capTpye, dfmax[mCap], round(dfmax['pe_ttm'],0), dfmax['past60Days'] * 100,
            cur_year_perc[dfmax.name])
        artxt = [rowtitle, '![](%s%s)' % (v['filename'], '?t='+datetime.now().strftime("%m%d%H")), maxtxt]
        article.append('\n<br><div>' + '\n<br>'.join([str(x) for x in artxt]) + '</div>')
    txt = '\n<br>'.join(article)
    title = ' '.join([mkt, pdate.strftime('%y/%m/%d'), datetime.now().strftime('%H:%M'), calKey])
    if mkt == 'cn' and calKey == '_U':
        txt='\n<br>高亮k线代表当天被港资大力买入，入选标准为5日10日均线交缠\n<br>'+txt
    html = markdown.markdown('#' + title + '#' + txt) \
        .replace('<a href="https://xueqiu', '<a class="button is-black" href="https://xueqiu') \
        .replace('/a>', '/a><br>') \
        .replace('a><br> <a', 'a><a') \
        .replace('TTMnan', '亏损') \
        .replace('.0亿', '亿')
    if test == 0:
        html = html.replace(IMG_FOLDER, 'https://upknow.gitee.io/')
    gAds = '<script data-ad-client="ca-pub-7398757278741889" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>'
    gAdBtm = '''
        <!-- toufu -->
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-7398757278741889"
             data-ad-slot="7456114770"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>'''
    css = '<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge">\
    <meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>\
    <link href="https://cdn.jsdelivr.net/npm/bulma@0.9.0/css/bulma.min.css"rel="stylesheet">{gAds}{style}</head>\
        <body class="bgc has-text-white-ter"><div class="container">\
        <div class="columns is-centered"><div class="column is-two-thirds"><article class="section">'.format(
        title=title, gAds=gAds,style='<style>.bgc{background-color: #33363b;}</style>')
    with open('../CMS/source/Quant/' + mkt + str(pdate.weekday() + 1) + calKey + '.html', 'w') as f:
        finalhtml = css + html + '<p><br>© Frank Lin 2020</p></ariticle></div>' + gAdBtm + '</div></div></body></html>'
        f.write(finalhtml)
        mlog('complete' + title)
        # if g.testMode():
        #     return finalhtml


def preparePlot():
    mlog(mpl.matplotlib_fname())
    mpl.rcParams['font.family'] = ['sans-serif']
    mpl.rcParams['font.sans-serif'] = ['Source Han Sans CN']  # 用来正常显示中文标签
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    _rebuild()


class params:
    def __init__(self, market=None, test=0):
        self.test = test
        mkt, cfg = checkTradingDay(market)  # 交易时间
        self.xq_a_token = cfg[mkt]['xq_a_token']
        self.paramSet = {'mkt': mkt, 'pdate': cfg[mkt]['date']}
        self.boardlist ={}
        if market=='cn':
            self.boardlist = dragonTigerBoards(self.paramSet['pdate'], self.xq_a_token)

    def go(self):
        dailyCheck(test=self.test)

    def testMode(self):
        return self.test


if __name__ == '__main__':
    preparePlot()
    logging.basicConfig(
        filename='daily.log',
        level=logging.DEBUG
    )
    if len(sys.argv) > 2:
        g = params(market=sys.argv[1], test=int(sys.argv[2]))
    else:
        g = params(market=sys.argv[1])
    g.go()
