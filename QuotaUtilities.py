import requests,datetime,json,demjson,os,re
import time as t
import pandas as pd
import logging
from datetime import *
from tqdm import tqdm
from urllib import parse
from concurrent.futures import ThreadPoolExecutor, as_completed,wait
import lxml.html

def checkTradingDay(mkt=None):#检查交易时间
    with open('idxTradeConfig.json') as f:
        config=json.load(f)
    today = datetime.now()
    for market,cfg in config.items():
        cfg=config[market]
        response = requests.get(url=cfg['url'],headers={"user-agent": "Mozilla"})
        cfg['xq_a_token'] = 'xq_a_token=' + response.cookies['xq_a_token'] + ';'
        html = lxml.html.etree.HTML(response.text)
        timeinfo = html.xpath('//div[@class="stock-time"]/span/text()')
        cfg['date']= pd.to_datetime(xqQuot(symbol=cfg['url'].split('/')[-1],cookie=cfg['xq_a_token'])['item'][-1][0],unit='ms',utc=True).tz_convert('Asia/Shanghai').date()
        print(market + ' '.join(timeinfo),cfg['date'])
        if mkt is not None:
            if market == mkt:
                return market, config
        elif today.hour==config[market]['PM'] or today.hour==config[market]['AM']:
            return market,config
    return False,False

def getUrl(url,cookie=''):
    retryTimes = 0
    while retryTimes < 99:
        try:
            response = requests.get(url,headers={"user-agent": "Mozilla", "cookie": cookie,"Connection":"close"},timeout=5)
            return response.text
        except Exception as e:
            mlog(e.args)
            mlog('retrying.....')
            t.sleep(60)
            retryTimes += 1
            continue

def fillDates(dates,dataDf:pd.DataFrame):
    if dates is None:
        return
    dataDf['date'] = pd.to_datetime(dataDf['date'])
    dataDf['date']= dataDf['date'].dt.date
    dataDf.set_index('date',inplace=True)
    return dataDf.reindex(dates,method='ffill')

def mlog(*args):
    for v in args:
        logging.debug(v)

def getTimestamp(dateString):
    d=[int(x) for x in dateString.split('-')]
    return int(t.mktime(datetime(d[0],d[1],d[2]).timetuple())) * 1000

def xqQuot(period='year', symbol='', type='before', latestDay=0, count=142,cookie=''):   # 获取雪球行情
    if latestDay==0:
        latestDay = int(t.mktime(datetime.now().date().timetuple()))*1000
    url = "https://stock.xueqiu.com/v5/stock/chart/kline.json\
?symbol={symbol}&begin={latestDay}&period={period}&type={type}&count={count}\
&indicator=kline,ma,pe,pb,ps,pcf,market_capital,agt,ggt,balance" \
        .format(period=period, symbol=symbol, type=type, latestDay=latestDay, count=-abs(count))
    # print(symbol,url)
    return json.loads(getUrl(url,cookie))['data']

def xueqiuK(symbol='QQQ',startDate=None,cookie=''):
    symbol=symbol.upper()
    quoFile='Quotation/'+symbol+'.csv'
    latestDay = int(t.mktime(datetime.now().date().timetuple())) * 1000
    # mlog(klineYear)
    if startDate is None:
        klineYear = xqQuot(symbol=symbol, period='year', latestDay=latestDay, type='before', cookie=cookie)
        if len(klineYear['item']) == 0:
            return None
        startYear=datetime.utcfromtimestamp(int(klineYear['item'][0][0])/1000).date().year
        df = pd.DataFrame(data=klineYear['item'], columns=klineYear['column'])
        # df.set_index(['timestamp'], inplace=True)
        df = df.iloc[0:0]
        df.drop(['volume_post', 'amount_post'], axis=1, inplace=True)
    else:
        startYear=int(startDate[:4])
        df=pd.DataFrame()
    while datetime.utcfromtimestamp(latestDay/1000).date().year>=startYear:
        mlog('latestDay:', latestDay,datetime.utcfromtimestamp(int(latestDay)/1000).date().year)
        quoteDaily=xqQuot(symbol=symbol,period='day',latestDay=latestDay,count=7000,type='before',cookie=cookie)
        if len(quoteDaily['item'])==0:
            break
        if latestDay==quoteDaily['item'][0][0]:
            # mlog('Reach last year')
            break
        else:
            latestDay = quoteDaily['item'][0][0]
        dfDaily = pd.DataFrame(data=quoteDaily['item'], columns=quoteDaily['column'])
        df=df.append(dfDaily,sort=False)
    # if startDate is not None:
    #     df=df[df.index>=getTimestamp(startDate)]
    df.drop_duplicates(subset='timestamp', keep='first', inplace=False)
    df.set_index(['timestamp'], inplace=True)
    df.index = pd.to_datetime(df.index,unit='ms',utc=True).tz_convert('Asia/Shanghai')
    df.index.name='date'
    df.sort_index(inplace=True)
    df['percent']=df['percent'].div(100).round(4)
    df.to_csv(quoFile,encoding='utf-8',index_label='date')
    return df

def dragonTigerBoard(symbol,xq_a_token):
    if symbol[:2] not in ['SZ', 'SH']:
        return []
    url = 'https://stock.xueqiu.com/v5/stock/capital/longhu.json?symbol=' + symbol + '&page=1&size=100'
    mlog(url)
    quoteData = json.loads(getUrl(url,xq_a_token))['data']['items']
    tdateList = []
    for q in quoteData:
        if len(q)!=2:
            continue
        if '专用' in str(q[0]['branches']) and '专用' not in str(q[1]['branches']):
            tdateList.append(q[0]['td_date'])
    tdateSeries = pd.to_datetime(pd.Series(data=tdateList, dtype='float64'), unit='ms',utc=True).dt.tz_convert('Asia/Shanghai').dt.date
    return tdateSeries

def getTimestamp(dateString):
    d=[int(x) for x in str(dateString).split('-')]
    return int(t.mktime(datetime(d[0],d[1],d[2]).timetuple())) * 1000

def dragonTigerBoards(pdate,xq_a_token):
    klineSZZS = xueqiuK('SH000001',pdate.strftime('%Y-%m-%d'),xq_a_token)
    stocks=[]
    stocksDict=dict()
    checked=[]
    tqdmRange=tqdm(klineSZZS.index.values[-20:])
    for d in tqdmRange:
        timestampstr=str(int(t.mktime(d.timetuple())*1000))
        if os.path.isfile('md/board'+timestampstr+'.json'):
            df = pd.read_json('md/board'+timestampstr+'.json')
            stocks.extend(df['symbol'].to_list())
        else:
            url = 'https://xueqiu.com/service/v5/stock/hq/longhu?date=' + timestampstr
            print(url)
            response = requests.get(url=url,
                                    headers={"user-agent": "Mozilla", "cookie": xq_a_token, "Connection": "close"},
                                    timeout=5)
            result=json.loads(response.text)['data']['items']
            if len(result)==0:
                continue
            string=json.dumps(result)
            with open('md/board' + timestampstr + '.json', 'w')as f:
                f.write(string)
            df=pd.DataFrame(result)

        for s in df['symbol'].to_list():
            tqdmRange.set_description(str(d)+'龙虎'+s)
            if s in checked or s.startswith('SH688'):
                continue
            checked.append(s)
            check = dragonTigerBoard(s, xq_a_token)
            if len(check) == 0:
                continue
            elif t.mktime(klineSZZS.index.values[-60].timetuple())>t.mktime(check[0].timetuple()):
                continue
            else:
                stocksDict[s] = check

    mlog(len(checked),len(stocksDict.keys()))
    return stocksDict


def debt():
    cookies = {
        # 'kbzw__Session': 'uefksvudi503ot70avlqtto2u3',
        # 'Hm_lvt_164fe01b1433a19b507595a43bf58262': '1597515456',
        # 'kbz_newcookie': '1',
        # 'Hm_lpvt_164fe01b1433a19b507595a43bf58262': '1597515566',
    }

    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.jisilu.cn',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.jisilu.cn/data/cbnew/',
        'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
    }

    params = (
        # ('___jsl', 'LST___t=1597548679161'),
    )

    data = {
      'fprice': '',
      'tprice': '',
      'curr_iss_amt': '',
      'volume': '',
      'svolume': '',
      'premium_rt': '',
      'ytm_rt': '',
      'market': '',
      'rating_cd': '',
      'is_search': 'N',
      'btype': '',
      'listed': 'Y',
      'sw_cd': '',
      'bond_ids': '',
      'rp': '50'
    }
    try:
        response = requests.post('https://www.jisilu.cn/data/cbnew/cb_list/', headers=headers, params=params, cookies=cookies, data=data)
    #NB. Original query string below. It seems impossible to parse and
    #reproduce query strings 100% accurately so the one below is given
    #in case the reproduced version is not "correct".
    # response = requests.post('https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t=1597548679161', headers=headers, cookies=cookies, data=data)
        rows= json.loads(response.text)['rows']
        data=[]
        for r in rows:
            data.append([r['cell']['stock_id'][:2]+r['id'].upper(),r['cell']['stock_id'].upper(),r['cell']['premium_rt']])
        df= pd.DataFrame(data=data,columns=['id','symbol','premium_rt'])
        df.set_index('symbol',inplace=True)
        return df

    except Exception as e:
        mlog(e.args)
        return None

def usETFpage(page):
    us_sina_stock_list_url = "http://stock.finance.sina.com.cn/usstock/api/jsonp.php/" \
                             "IO.XSRV2.CallbackList['xY9bItB5t8F8mTxm']/" \
                             "US_DataCenterService.getInstrType?page={}" \
                             "&num=60&sort=&asc=0&market=&id=&instr_type=3".format(page)
    res = requests.get(us_sina_stock_list_url)
    return json.loads(res.text[res.text.find("({") + 1: res.text.rfind(");")])

def usETFlist():
    """新浪财经-所有美国ETF数据, 注意延迟 15 分钟
    """
    data_json = usETFpage(str(1))
    big_df,total_page_count =pd.DataFrame(data_json["data"]), int(data_json['count']) // 60 + 1
    for page in tqdm(range(1, total_page_count)):
        pageDf=pd.DataFrame(usETFpage(str(page))["data"])
        big_df= big_df.append(pageDf, ignore_index=True)
    big_df.to_csv('usETFsina.csv',encoding='GBK')
    return big_df

def tencentK(mkt:str = '',symbol: str = "QQQ",KAll=False) -> pd.DataFrame:
    symbol=symbol.lower()
    # A股的mkt为''
    if mkt=='us' and '.' not in symbol:
        symbol = mkt + symbol + '.' + re.findall(re.compile(r'~%s\.(.*?)~' % symbol, re.S),requests.get('http://smartbox.gtimg.cn/s3/?q=%s&t=us' % symbol).text)[0]
    elif mkt=='hk':
        symbol=mkt+symbol
    """
        腾讯证券-获取有股票数据的第一天, 注意这个数据是腾讯证券的历史数据第一天
        http://gu.qq.com/usQQQ.OQ/
        :param symbol: 带市场标识的股票代码
        :type symbol: str
        :return: 开始日期
        :rtype: pandas.DataFrame
        """
    range_start = (date.today()-timedelta(days=40)).year
    headers = {"user-agent": "Mozilla", "Connection": "close"}
    if KAll:
        url = "http://web.ifzq.gtimg.cn/other/klineweb/klineWeb/weekTrends"
        params = {
            "code": symbol,
            "type": "qfq",
            "_var": "trend_qfq",
            "r": "0.3506048543943414",
        }
        res = requests.get(url,headers=headers,params=params)
        text = res.text
        start_date = demjson.decode(text[text.find("={") + 1:])["data"][0][0]
        range_start = int(start_date.split("-")[0])
    range_end = date.today().year + 1
    url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
    temp_df = pd.DataFrame()
    url_list=[]
    for year in range(range_start, range_end):
        params = {
            "_var": f"kline_dayqfq{year}",
            "param": f"{symbol},day,{year}-01-01,{year + 1}-12-31,1350,qfq",
            "r": "0.8205512681390605",
        }
        url_list.append(url + parse.urlencode(params))
        continue
    # print(url_list)
    with ThreadPoolExecutor(max_workers=10) as executor:  # optimally defined number of threads
        responeses = [executor.submit(getUrl, url) for url in url_list]
        wait(responeses)

    for res in responeses:
        text=res.result()
        try:
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1:])["data"][symbol]["day"]
            )
        except:
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1:])["data"][symbol]["qfqday"]
            )
        temp_df = temp_df.append(inner_temp_df, ignore_index=True)

    if temp_df.shape[1] == 6:
        temp_df.columns = ["date", "open", "close", "high", "low", "amount"]
    else:
        temp_df = temp_df.iloc[:, :6]
        temp_df.columns = ["date", "open", "close", "high", "low", "amount"]
    temp_df.index = pd.to_datetime(temp_df["date"])
    del temp_df["date"]
    temp_df = temp_df.astype("float")
    temp_df.drop_duplicates(inplace=True)
    temp_df.rename(columns={'amount':'volume'}, inplace = True)
    temp_df.to_csv('Quotation/'+symbol+'.csv',encoding='utf-8',index_label='date')
    return temp_df

def eastmoneyK(code:str, quota_type='k', fuquan='fa', **kwargs):
    quoFile = 'Quotation/' + code + '.csv'
    """
    东方财富A股行情数据
    :param code:
    :param quota_type: 行情数据类型
            m5k、m15k、m30k、m60k：最近30个交易日的5分钟、15分钟、30分钟、60分钟行情
            k、wk、mk：日线、周线、月线行情
    :param fuquan: 复权
            空值：不复权；fa：前复权；ba：后复权
    :param iscr: 是否获取开盘前15分钟内的行情
    :return:
    """
    code=code.lower()
    if len(code)==8 and code[:2] == "sh":
        code = code[2:] + '1'
    elif len(code)==8 and code[:2] == "sz":
        code = code[2:] + '2'
    # print(code)
    url = 'http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js'
    params = {'id': code,
              'type': quota_type,
              'authorityType': fuquan,
              'rtntype': kwargs.get('rtntype', 5),
              'iscr': kwargs.get('iscr', 'false'),
              }
    h = requests.get(url=url, params=params)
    if h is not None:
        try:
            data = json.loads(h.content[1:-1])
            data = [x.split(",") for x in data['data']]
            df=pd.DataFrame(data=data,columns=["date","open","close","high","low","volume","amount","amplitude","turnoverrate"])
            df.set_index('date',inplace=True)
            df.index=pd.to_datetime(df.index).date
            df=df.apply(pd.to_numeric, errors='coerce').fillna(df)
            df.to_csv(quoFile,encoding='utf-8',index_label='date')
            return df
        except Exception as e:
            print(e)
            return h

def cmsK(code:str,type:str='daily'):
    """招商证券A股行情数据"""
    typeNum={'daily':1,'monthly':3}
    code=code.upper()
    quoFile = 'Quotation/' + code + '.csv'
    if len(code)==8:
        code = code[:2] + ':'+code[2:]
    params = (
        ('funcno', 20050),
        ('version', '1'),
        ('stock_list', code),
        ('count', '10000'),
        ('type', typeNum[type]),
        ('field', '1:2:3:4:5:6:7:8:9:10:11:12:13:14:15:16:18:19'),
        ('date', datetime.now().strftime("%Y%m%d")),
        ('FQType', '2'),#不复权1，前复权2，后复权3
    )
    url='https://hq.cmschina.com/market/json?'+parse.urlencode(params)
    data = json.loads(getUrl(url))['results'][0]['array']
    df=pd.DataFrame(data=data,columns=['date','open','high','close','low','yesterday','volume','amount','price_chg','percent','turnoverrate','ma5','ma10','ma20','ma30','ma60','afterAmt','afterVol'])
    df.set_index('date',inplace=True)
    df.index=pd.to_datetime(df.index,format='%Y%m%d')
    df=df.apply(pd.to_numeric, errors='coerce').fillna(df)
    if type=='daily':
        df.to_csv(quoFile,encoding='utf-8',index_label='date')
    df['percent']=df['percent'].round(4)
    return df