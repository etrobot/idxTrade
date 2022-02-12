import numpy as np
from idxTrade import *
from selenium import webdriver

ENCODE_IN_USE = 'GBK'
IMG_FOLDER = '../upknow/'

def genEchartJson(qdf:pd.DataFrame,filename:str):
    qdf['date']=qdf.index.strftime('%m-%d').tolist()
    transdf = qdf[-75:][['date', 'open', 'close', 'low', 'high', 'volume']].copy()
    transdf.T
    with open('../CMS/source/Quant/q/%s.json' % filename, 'w', encoding='utf-8') as f:
        json.dump(transdf.values.tolist(), f)


def updateAllImg(mkt, pdate, calKeys, cookie=''):
    tqdmRange = tqdm(range(0, 5))
    drawedSymbolList = []
    for i in tqdmRange:
        if pdate.weekday() != i:
            for calKey in calKeys:  # 加入url参数（小时），让浏览器不使用缓存
                filename = '../CMS/source/Quant/%s%s%s.html' % (mkt,pdate.weekday()+1,calKey)
                if os.path.isfile(filename):
                    with open(filename, "r") as f:
                        html = etree.HTML(f.read())
                        symbols = [x.split('/')[-1] for x in html.xpath('//div[(@id)]/@id')]
                        for k in symbols:
                            if k not in drawedSymbolList:
                                genEchartJson(getK(k,pdate,cookie), k)
                                drawedSymbolList.append(k)


def updateFund(pdate:dt):
    fundDf = ak.fund_em_open_fund_rank()
    fundDf.drop('序号',1,inplace=True)
    fundDf['weekday']=None
    fundDf['stock']=None
    for mkt in ['cn','hk']:
        quoteFile='md/'+ mkt + pdate.strftime('%Y%m%d') + '_Bak.csv'
        if not os.path.isfile(quoteFile):
            return
        quote = pd.read_csv(quoteFile, encoding='GBK',dtype={'symbol':str})
        for i in range(0, 5):
            for calKey in ['_U', '_J']:  # 加入url参数（小时），让浏览器不使用缓存
                weekday='%s%s%s' % (mkt, range(1,6)[i-pdate.weekday()-1], calKey)
                filename = '../CMS/source/Quant/%s.html' % weekday
                if os.path.isfile(filename):
                    with open(filename, "r") as f:
                        output = re.findall('<a id="(.*)"></a>', f.read())
                        for stockSymbol in output:
                            stockSymbol=stockSymbol.replace('#','')
                            converters = {c:lambda x: str(x) for c in fundDf.columns}
                            try:
                                df = pd.read_html('../CMS/source/Fund/%s.html'%stockSymbol,encoding='utf-8', converters=converters)[0][::-1]
                            except:
                                continue
                            for k in df['基金代码'].values.tolist():
                                if k not in fundDf['基金代码'].values or stockSymbol not in quote['symbol'].values:
                                    continue
                                idx=fundDf.index[fundDf['基金代码'] == k][0]
                                stockName=quote.loc[quote['symbol']==stockSymbol]['name'].values[0]
                                fundDf.at[idx,'stock']='<a href="https://xueqiu.com/S/%s">%s%s</a>'%(stockSymbol,stockSymbol,stockName)
                                fundDf.at[idx,'weekday']='<a href="%s.html#%s">%s</a>'%(weekday,stockSymbol,weekday)
    fundDf.dropna(subset=['weekday'],inplace=True)
    fundDf.sort_values('weekday',inplace=True)
    # fundDf['基金简称'] = fundDf.apply(
    #     lambda x: '<a href="http://fund.eastmoney.com/{fundcode}">{fundname}</a>'.format(fundcode=x['基金代码'],
    #                                                                                     fundname=x['基金简称']), axis=1)
    # fundDf['基金代码'] = fundDf['基金代码'].apply(
    #     lambda x: '<a href="https://xueqiu.com/S/F{fundcode}">{fundcode}</a>'.format(fundcode=x))
    renderHtml(fundDf,'../CMS/source/Quant/fund.html','含量化选股的内地基金')

def cauculate(dfk):
    if len(dfk['close'].values) < 44:
        return {'_J': np.nan, '_U': np.nan}
    # ma =dfk['close'].rolling(window=3).mean()
    dfk = dfk.iloc[-42:]
    closes = dfk['close']
    vol = dfk['volume']
    # pct=dfk['percent'].round(2)
    mtm_1 = abs(closes[-20:].mean()-closes[-10:].mean())/(closes[-20]-closes[-1])*vol[-1]/vol.mean()
    mtm_2 = (closes.mean()-min(closes[-15:]))/max(0.01,abs((max(closes[-10:-1])+min(closes[-10:-1])-closes[-1]*2)))*vol[-2]/vol[-1]
    return {'_U': round(mtm_1, 12), '_J': round(mtm_2, 12)}


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
        df['行业'] = hrefname[i]
        mktDf = mktDf.append(df)
    mktDf.dropna(subset=['current_year_percent'], inplace=True)
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
    mktDf.dropna(subset=['current_year_percent'], inplace=True)
    mktDf = mktDf.loc[mktDf['current'] >= 1.0]
    mktDf.set_index('symbol', inplace=True)
    mktDf['float_market_capital'] = mktDf['float_market_capital'].astype('float').div(100000000.0).round(1)
    mktDf['market_capital'] = mktDf['market_capital'].astype('float').div(100000000.0).round(1)
    mktDf.to_csv('md/' + 'us' + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding=ENCODE_IN_USE)
    return mktDf

def thsIndustry(mkt='cn', pdate=datetime.now().date(),cptOrInd='thshy'):
    p_url = 'http://q.10jqka.com.cn/'+cptOrInd
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
    # options.add_argument('--headless')
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
                    t.sleep(180)
                    continue
                if len(driver.get_cookies())>0:
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
    indDf[['current','percent']] = indDf[['current','percent']].apply(pd.to_numeric, errors='coerce', axis=1)
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
        indDf = indDf[~indDf['name'].str.contains("N|\*ST", na=False)]
        # indDf = indDf[~indDf.index.str.startswith("SH688", na=False)]
    # elif mkt=='us':
    #     indDf=usHot(pdate,g.xq_a_token)
    # elif mkt=='hk':
    else:
        indDf = xueqiuBackupByIndustry(mkt, pdate, test)
    avgAmount = indDf['amount'].mean()
    indDf = indDf[indDf['amount'] > avgAmount]
    # indDf = indDf[indDf.index.isin(xueqiuConcerned(mkt,g.xq_a_token)['symbol'])]

    indDf = indDf.fillna(value=np.nan)
    cal = {'_J': [], '_U': []}
    indDf['filename'] = None
    indDf['past45Days'] = -999.0
    if mkt=='cn':
        boardhk=dict()
        for b in g.boardlist.keys():
            if len(g.boardlist[b])>0:
                boardhk[b]=g.boardlist[b]
        indDf=indDf[indDf.index.isin(list(boardhk.keys()))]
    tqdmRange = tqdm(indDf.iterrows(), total=indDf.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description(("%s %s %s %s" % (mkt, v['行业'], k, v['name'])).ljust(25))
        qdf = getK(k, pdate,g.xq_a_token, test)
        if len(qdf)<30:
            for mk, mv in cal.items():
                cal[mk].append(None)
            continue
        if max(qdf['open'][x]/qdf['close'][x-1] for x in range(-29,0))>1.2:
            continue
        indDf.at[k, 'past45Days'] = round(qdf['close'][-1] / min(qdf['close'][-45:]) - 1, 4)
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
    if not g.testMode():
        updateAllImg(mkt, pdate, cal.keys(), g.xq_a_token)
    if mkt in ['cn','hk']:
        updateFund(pdate)
    if len(sys.argv) == 2:
        idxtrade = idxTrade(mkt, 0)
        idxtrade.run()


def df2md(mkt, calKey, indDf, pdate, test=0, num=10):
    upRatio=round(indDf['percent'][indDf['percent']>0].count()/len(indDf['percent'])*100,1)
    mCap = {'us': 'market_capital', 'cn': 'float_market_capital', 'hk': 'float_market_capital'}[mkt]
    capTpye = {'us': '总', 'cn': '流通', 'hk': '港股'}[mkt]
    avgMktCap = indDf[mCap].mean()
    df = indDf.dropna(subset=[calKey])
    if mkt=='cn':
        df = df.sort_values(by=[calKey],ascending=True).iloc[:num]
    else:
        df = df[df[mCap] < avgMktCap].sort_values(by=[calKey], ascending=True).iloc[:num]
    df[mCap] = df[mCap].apply(str) + '亿'
    article = []
    drawedSymbolList = []

    tqdmRange = tqdm(df.iterrows(), total=df.shape[0])
    for k, v in tqdmRange:
        tqdmRange.set_description('【' + calKey + '】' + k + v['name'])
        dfmax = indDf[indDf['行业'] == v['行业']].sort_values(by=['past45Days'], ascending=False).iloc[0]
        if not g.testMode() and k not in drawedSymbolList:
            qdf = getK(k, pdate,g.xq_a_token, 1)
            genEchartJson(qdf,k)
            drawedSymbolList.append(k)

        cur_year_perc = {k: v['current_year_percent'], dfmax.name: dfmax['current_year_percent']}

        rowtitle='[%s(%s)](https://xueqiu.com/S/%s)'%(v['name'], k,k)
        if mkt == 'cn':
            for cnstock in cur_year_perc.keys():
                mK = cmsK(cnstock, 'monthly')
                yr = 1
                for i in range(-min(datetime.now().month, len(mK)), 0):
                    yr = yr * (1 + mK['percent'][i])
                cur_year_perc[cnstock] = round(yr * 100 - 100, 2)
        # if mkt=='cn' or mkt=='hk':
        #     fundDf = heldBy(k, pdate,mkt)
        #     if fundDf is not None and len(fundDf)>0:
        #         rowtitle += '[%s](../Fund/%s.html)'%('持股基金',k)
        #         renderHtml(fundDf,'../CMS/source/Fund/' + k + '.html','%s(%s)'%(v['name'],k))

        rowtitle += '%s市值%s TTM%s 今年%s%%  %s' % (capTpye, v[mCap], v['pe_ttm'], cur_year_perc[k], calKey)

        maxtxt = v['行业'] + '板块近45日最强：[%s](https://xueqiu.com/S/%s) %s市值%s亿 TTM%s 45日低点至今涨幅%d%% 今年%s%%' % (
            dfmax['name'], dfmax.name, capTpye, dfmax[mCap], round(dfmax['pe_ttm'],0), dfmax['past45Days'] * 100,
            cur_year_perc[dfmax.name])
        # if mkt=='cn' or mkt=='hk':
        #     fundDf = heldBy(dfmax.name, pdate,mkt)
        #     if fundDf is not None and len(fundDf)>0:
        #         maxtxt += '[%s](../Fund/%s.html)'%('持股基金',dfmax.name)
        #         renderHtml(fundDf,'../CMS/source/Fund/' + dfmax.name + '.html','%s(%s)'%(dfmax['name'],dfmax.name))

        artxt = [rowtitle, '<div id="%s" style="height:12rem"></div>' % k, maxtxt]
        article.append('\n<br><div>' + '\n<br>'.join([str(x) for x in artxt]) + '</div>')
    upWarning='\n<br>上涨比例%s%%' % upRatio
    if upRatio<13.5:
        upWarning+='可能有系统性风险，警惕！'
    txt = upWarning+'\n<br>'.join(article)
    title = ' '.join([mkt, pdate.strftime('%y/%m/%d'), datetime.now().strftime('%H:%M'), calKey])
    if mkt == 'cn':
        txt='\n<br>高亮k线代表当天被港资大力买入，入选标准为5日10日均线交缠\n<br>'+txt
    html = markdown.markdown('#' + title + '#' + txt) \
        .replace('<a href="https://xueqiu', '<a class="button is-black" href="https://xueqiu') \
        .replace('<a href="../Fund', '<a class="button is-dark" href="../Fund')\
        .replace('/a>', '/a><br>') \
        .replace('a><br><a class="button is-dark', 'a><a class="button is-dark') \
        .replace('TTMnan', '亏损') \
        .replace('.0亿', '亿')

    html = html.replace(IMG_FOLDER, 'https://upknow.gitee.io/')
    # html = html.replace(IMG_FOLDER, '../../'+IMG_FOLDER)
    gAds = '<script data-ad-client="ca-pub-7398757278741889" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>\n'
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
    <link href="https://cdn.jsdelivr.net/npm/bulma@0.9.0/css/bulma.min.css"rel="stylesheet">{style}\
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>\
    <script type ="text/javascript" src="https://cdn.bootcdn.net/ajax/libs/zepto/1.2.0/zepto.min.js" ></script >\
        </head><body class="bgc has-text-white-ter"><div class="container">\
        <div class="columns is-centered"><div class="column is-two-thirds"><article class="section">'.format(
        title=title,style='<style>.bgc{background-color: #33363b;}</style>')

    echartjs = '<script type="text/javascript">var names=' + str(df.index.tolist()) + ';for(var i=0;i<names.length;i++){getJSON(names[i])}function splitData(rawData){var categoryData=[];var values=[];var volumes=[];for(var i=0;i<rawData.length;i++){categoryData.push(rawData[i].splice(0,1)[0]);values.push(rawData[i]);volumes.push([i,rawData[i][4],rawData[i][0]>rawData[i][1]?1:-1])}return{categoryData:categoryData,values:values,volumes:volumes}}function calculateMA(dayCount,data){var result=[];for(var i=0,len=data.values.length;i<len;i++){if(i<dayCount){result.push("-");continue}var sum=0;for(var j=0;j<dayCount;j++){sum+=data.values[i-j][1]}result.push(+(sum/dayCount).toFixed(3))}return result}function getJSON(id){$.getJSON("./q/"+id+".json?random="+new Date().getTime(),function(result){var data=splitData(result);option={animation:false,visualMap:{show:false,seriesIndex:4,dimension:2,pieces:[{value:1,color:"seagreen"},{value:-1,color:"firebrick"}]},grid:[{left:"10%",top:"10%",height:"60%"},{left:"10%",top:"80%",height:"20%"}],xAxis:[{type:"category",data:data.categoryData,scale:true,boundaryGap:false,axisLine:{onZero:false},splitLine:{show:false},splitNumber:20,min:"dataMin",max:"dataMax",axisPointer:{z:100}},{type:"category",gridIndex:1,data:data.categoryData,scale:true,boundaryGap:false,axisLine:{onZero:false},axisTick:{show:false},splitLine:{show:false},axisLabel:{show:false},splitNumber:20,min:"dataMin",max:"dataMax"}],yAxis:[{scale:true,splitLine:{lineStyle:{color:"#555"}}},{scale:true,gridIndex:1,splitNumber:2,axisLabel:{show:false},axisLine:{show:false},axisTick:{show:false},splitLine:{show:false}}],series:[{name:"日K",type:"candlestick",data:data.values,itemStyle:{color:"#f64769",color0:"mediumaquamarine",borderColor:null,borderColor0:null},},{name:"MA5",type:"line",data:calculateMA(5,data),smooth:false,showSymbol:false},{name:"MA10",type:"line",data:calculateMA(10,data),smooth:false,showSymbol:false},{name:"MA20",type:"line",data:calculateMA(20,data),smooth:false,showSymbol:false},{name:"Volume",type:"bar",xAxisIndex:1,yAxisIndex:1,data:data.volumes}]};echarts.init(document.getElementById(id),"dark").setOption(option)})};</script>'
    with open('../CMS/source/Quant/' + mkt + str(pdate.weekday() + 1) + calKey + '.html', 'w') as f:
        finalhtml = css + html + '<p><br>© Frank Lin 2020</p></ariticle></div>' + gAdBtm + '</div></div>'+gAds+'\n</body>'+echartjs+'\n</html>'
        f.write(finalhtml)
        mlog('complete' + title)
        # if g.testMode():
        #     return finalhtml

class params:
    def __init__(self, market=None, test=0,pdate=None):
        self.test = test
        mkt, cfg = checkTradingDay(market,pdate)  # 交易时间
        self.xq_a_token = cfg[mkt]['xq_a_token']
        self.paramSet = {'mkt': mkt, 'pdate': cfg[mkt]['date']}
        self.boardlist ={}

    def go(self):
        if self.paramSet['mkt']=='cn':
            self.boardlist = dragonTigerBoards(self.paramSet['pdate'], self.xq_a_token)
        dailyCheck(test=self.test)

    def testMode(self):
        return self.test


if __name__ == '__main__':
    logging.basicConfig(
        filename='daily.log',
        level=logging.DEBUG
    )
    if len(sys.argv) == 3:
        g = params(market=sys.argv[1], test=int(sys.argv[2]))
    elif len(sys.argv) == 4:
        dateInts=[int(x) for x in sys.argv[3].split('-')]
        g = params(market=sys.argv[1], test=int(sys.argv[2]),pdate=date(dateInts[0],dateInts[1],dateInts[2]))
    else:
        g = params(market=sys.argv[1])
    g.go()
