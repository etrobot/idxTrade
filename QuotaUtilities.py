import requests,datetime,json,demjson,os,re
import time as t
import pandas as pd
import numpy as np
import logging
import datetime as dt
from datetime import *
from tqdm import tqdm
from urllib import parse
from concurrent.futures import ThreadPoolExecutor, as_completed,wait
import lxml.html
import akshare as ak
from lxml import etree
import traceback

def getK(k:str, pdate=None,xq_a_token=None,test=0):
    if test == 1 and os.path.isfile('Quotation/' + k + '.csv'):
        qdf = pd.read_csv('Quotation/' + k + '.csv', index_col='date',parse_dates=['date'])
    elif k.upper()[:2] in ['SH','SZ'] and k.upper()[2:].isdigit() and len(k)==8:
        qdf = cmsK(k)
    elif xq_a_token is not None:
        qdf = xueqiuK(symbol=k, startDate=pdate, cookie=xq_a_token)#pdate - timedelta(days=250)).strftime('%Y%m%d')
    return qdf

def getInfo(symbol:str,all:pd.DataFrame):
    if symbol[-6:] in all['股票简称'] and all['行业分类'].get(symbol[-6:])!='--':
        return {'股票简称':all['股票简称'].get(symbol[-6:]),'行业':all['行业分类'].get(symbol[-6:]),'region':all['省份'].get(symbol[-6:]),'city':all['省份'].get(symbol[-6:]),'上市时间':all['上市日期'].get(symbol[-6:]).replace('-','')}
    try:
        info = ak.stock_individual_info_em(symbol=symbol[-6:]).set_index('item').to_dict()['value']
        info['行业'] = info['行业'].replace('行业','')
        info['region']=all['省份'].get(symbol[-6:],'')
        info['city'] = all['城市'].get(symbol[-6:], '').replace('市','')
        return info
    except:
        return {}
        pass

def getAllInfo():
    start_time = t.time()  # 获取程序开始运行时间
    df = pd.DataFrame()  # 定义一个空的DataFrame用于存储数据
    i=1
    while i<=250:
        try:
            url = 'https://s.askci.com/stock/a/?reportTime=2021-12-31&pageNum={i}'.format(i=i)  # 日期可以改，可获取季度数据
            print(url)
            df = pd.concat([df, pd.read_html(url)[3].loc[:, :]])  # 第1个表格故填[0],经观察发现所需表格是网页中第4个表格，故为[3]。获得后纵向追加到df中
            endtime = t.time() - start_time
            print('正在获取上市公司基本信息表第' + str(i) + '页', '已运行%.2f秒' % endtime)
        except Exception:
            traceback.print_exc()
            pass
            t.sleep(20)
            continue
        i += 1
    df['股票代码'] = df['股票代码'].astype('str').str.zfill(6)  # 将原本的int数据类型转换为文本，补齐股票代码为6位，用的时候必须加上.str前缀
    df.drop(['序号', '招股书', '公司财报'], axis=1, inplace=True)  # 删除多余的列，axis=1（按列方向操作）、inplace=True（修改完数据，在原数据上保存）
    df.to_csv('info.csv',index='股票代码')
    print('\n', '*******目标爬取完成*******')

def getLimit(pdate:date=None,fname=None,mode=None):
    zdt_url = 'http://home.flashdata2.jrj.com.cn/limitStatistic/ztForce/' + pdate.strftime("%Y%m%d") + ".js"
    zdt_indexx = [u'代码', u'名称', u'最新价格', u'涨跌幅', u'封成比', u'封流比', u'封单金额', u'最后一次涨停时间',
                  u'第一次涨停时间', u'打开次数',u'振幅', u'涨停强度']
    header_zdt = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'home.flashdata2.jrj.com.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
    }

    #获取昨日连板
    if mode is not None:
        zdt_url = 'http://hqdata.jrj.com.cn/zrztjrbx/limitup.js'+'?_='+str(t.time()).replace('.','')[:13]
        zdt_indexx = [u'序号', u'代码', u'名称',u'最后一次涨停时间', u'最新价格', u'涨跌幅', u'最大涨幅',u'最大跌幅',u'是否连续涨停',
                      u'连续涨停次数',u'昨日强度', u'今日强度', u'是否开板', u'上个交易日',u'昨日涨停价',u'今日开盘价',u'开盘涨幅 ']
        header_zdt = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Host': 'hqdata.jrj.com.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15',
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        # {index: 0, stockcode: 1, stockname: 2, lastzttime: 3, nowprice: 4, pricelimit: 5, highlimit: 6, lowlimit: 7,
        #  iscon: 8, conztnums: 9, lastforce: 10, todayforce: 11, isstop: 12, lasttradedate: 13, lastcloseprice: 14,
        #  openprice: 15, openlimit: 16}

    # mlog(zdt_url)
    s = requests.Session()

    try:
        resp = s.get(zdt_url, headers=header_zdt)
        # mlog(resp.text)
        if resp.status_code == 404:
            mlog(resp.status_code)
        md_check = re.findall('summary|lasttradedate', resp.text)
        if resp.text and len(md_check) > 0:
            p = re.compile(r'"Data":(.*)};', re.S)
            if len(resp.text) <= 0:
                mlog('Content\'s length is 0')
                exit(0)
            result = p.findall(resp.text.replace('Infinity','0').replace('\r','').replace('\n','').replace(',,',',"",').replace('NaN','0'))
            if result:
                try:
                    t1 = result[0]
                    t2 = list(eval(t1))
                    t2.reverse()
                    for i in range(len(t2)):
                        st=0
                        if mode is not None:
                            st=1
                        if t2[i][st].startswith('6'):
                            t2[i][st]='SH'+t2[i][st]
                        else:
                            t2[i][st] = 'SZ' + t2[i][st]
                    df = pd.DataFrame(t2, columns=zdt_indexx)
                    # df.to_csv('md/limit'+pdate.strftime("%Y%m%d")+'.csv')
                    return df[~df['名称'].str.contains('\*|退')]
                        # return df[~df['代码'].astype(str).str.startswith('SH688')]
                        # return df[~df['代码'].astype(str).str.startswith('SH688') & ~df['代码'].astype(str).str.startswith('SZ3')]
                except Exception as e:
                    mlog(e)
        else:
            mlog('failed to get content')
    except Exception as e:
        mlog(e)


def checkTradingDay(mkt=None,pdate=None):#检查交易时间
    with open('idxTradeConfig.json') as f:
        config=json.load(f)
    today = datetime.now()
    for market,cfg in config.items():
        cfg=config[market]
        response = requests.get(url=cfg['url'],headers={"user-agent": "Mozilla"})
        cfg['xq_a_token'] = 'xq_a_token=' + response.cookies['xq_a_token'] + ';'
        html = lxml.html.etree.HTML(response.text)
        timeinfo = html.xpath('//div[@class="stock-time"]/span/text()')
        cfg['date'] = pdate
        if pdate is None:
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
        print(v)
        # logging.debug(v)

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
        startYear=startDate.year
        df=pd.DataFrame()
    while datetime.utcfromtimestamp(latestDay/1000).date().year>=startYear:
        mlog('latestDay:', latestDay,datetime.utcfromtimestamp(int(latestDay)/1000).date().year)
        quoteDaily=xqQuot(symbol=symbol,period='day',latestDay=latestDay,count=7000,type='before',cookie=cookie)
        if 'item' not in quoteDaily.keys():
            return []
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
    if 'timestamp' not in df.columns:
        return []
    df.drop_duplicates(subset='timestamp', keep='first', inplace=True)
    df.set_index(['timestamp'], inplace=True)
    df.index = pd.to_datetime(df.index,unit='ms',utc=True).tz_convert('Asia/Shanghai').date
    df.index.name='date'
    df.sort_index(inplace=True)
    df['percent']=df['percent'].div(100).round(4)
    df.to_csv(quoFile,encoding='utf-8',index_label='date',date_format='%Y-%m-%d')
    return df

def getTimestamp(dateString):
    d=[int(x) for x in str(dateString).split('-')]
    return int(t.mktime(datetime(d[0],d[1],d[2]).timetuple())) * 1000

def dragonTigerBoard(symbol,xq_a_token):
    if symbol[:2] not in ['SZ', 'SH']:
        return []
    url = 'https://stock.xueqiu.com/v5/stock/capital/longhu.json?symbol=' + symbol + '&page=1&size=100'
    mlog(url)
    quoteData = json.loads(getUrl(url,xq_a_token))['data']['items']
    tdateList = []
    for q in quoteData:
        if len(q)!=2 or '连续三个交易日内' in q[0]['info_type_name']:
            continue
        for branch in q[0]['branches']:
            if '股通' in branch['branch_name'] and branch['net_amt']>0:
                tdateList.append(q[0]['td_date'])
                break
    tdateSeries = pd.to_datetime(pd.Series(data=tdateList, dtype='float64'), unit='ms',utc=True).dt.tz_convert('Asia/Shanghai').dt.date
    return tdateSeries

def dragonTigerBoards(pdate,xq_a_token):
    klineSZZS = xueqiuK('SH000001',pdate,xq_a_token)
    stocks=[]
    stocksDict=dict()
    checked=[]
    tqdmRange=tqdm(klineSZZS.index[-20:].date)
    for d in tqdmRange:
        timestampstr=str(int(t.mktime(d.timetuple())*1000))
        if os.path.isfile('md/board'+timestampstr+'.json'):
            df = pd.read_json('md/board'+timestampstr+'.json')
            stocks.extend(df['symbol'].to_list())
        else:
            url = 'https://xueqiu.com/service/v5/stock/hq/longhu?date=' + timestampstr
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
            tqdmRange.set_description(str(d)+'龙虎 '+s)
            checked.append(s)
            url = 'https://stock.xueqiu.com/v5/stock/capital/longhu.json?symbol=' + s + '&page=1&size=100'
            quoteData = json.loads(getUrl(url, xq_a_token))['data']['items']
            tdateList = []
            noIns=True
            for q in quoteData:
                if not noIns:
                    break
                if len(q) != 2 or '连续三个交易日内' in q[0]['info_type_name']:
                    continue
                if q[0]['buy_total']<=q[1]['sell_total'] and q==quoteData[0]:
                    noIns = False
                    break
                for branch in q[0]['branches']:
                    if t.mktime(klineSZZS.index.date[-60].timetuple()) > t.mktime(datetime.fromtimestamp(q[0]['td_date']/1000).timetuple()):
                        continue
                    if '机构' in branch['branch_name']:
                        noIns=False
                        break
                    elif '股通' in branch['branch_name']:
                        if branch['net_amt'] > 0:
                            tdateList.append(q[0]['td_date'])
            if not noIns:
                continue
            tdateSeries = pd.to_datetime(pd.Series(data=tdateList, dtype='float64'), unit='ms', utc=True).dt.tz_convert(
                'Asia/Shanghai').dt.date
            stocksDict[s] = tdateSeries

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
    big_df.to_csv('usETFsina.csv',encoding='GBK',date_format='%Y-%m-%d')
    return big_df

def tencentK(mkt:str = 'us',symbol: str = "QQQ",KAll=False,period='week') -> pd.DataFrame:
    # symbol=symbol.lower()
    # A股的mkt为''
    if mkt=='us' and '.' not in symbol:
        symbolTxt=requests.get(f"http://smartbox.gtimg.cn/s3/?q={symbol}&t=us").text
        symbol = mkt + symbolTxt.split("~")[1].upper()
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
    if mkt=='us':
        url = "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?"
    temp_df = pd.DataFrame()
    url_list=[]
    if period == 'day':
        for year in range(range_start, range_end):
            params = {
                "_var": f"kline_dayqfq{year}",
                "param": f"{symbol},day,{year}-01-01,{year + 1}-12-31,1350,qfq",
                "r": "0.8205512681390605",
            }
            url_list.append(url + parse.urlencode(params))
    else:
        params = {
            "_var": f"kline_{period}qfq",
            "param": f"{symbol},{period},,,320,qfq",
            "r": "0.012820108110342066",
        }
        url_list.append(url + parse.urlencode(params))
    # print(url_list)
    with ThreadPoolExecutor(max_workers=10) as executor:  # optimally defined number of threads
        responeses = [executor.submit(getUrl, url) for url in url_list]
        wait(responeses)

    for res in responeses:
        text=res.result()
        try:
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1:])["data"][symbol][period]
            )
        except:
            inner_temp_df = pd.DataFrame(
                demjson.decode(text[text.find("={") + 1:])["data"][symbol]["qfq%s"%period]
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
    temp_df.to_csv('Quotation/'+symbol+'.csv',encoding='utf-8',index_label='date',date_format='%Y-%m-%d')
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
    :param iscr: 是否获取开盘前15分钟内的行情te
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
            df.set_index(pd.to_datetime(df['date']),inplace=True)
            df=df.apply(pd.to_numeric, errors='coerce').fillna(df)
            df.to_csv(quoFile,encoding='utf-8',index=False,date_format='%Y-%m-%d')
            return df
        except Exception as e:
            print(e)
            return h

def cmsK(code:str,type:str='daily'):
    """招商证券A股行情数据"""
    typeNum={'daily':1,'monthly':3,'weekly':2}
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
    kjson=json.loads(getUrl(url))
    if len(kjson['results'])==0:
        return []
    data = kjson['results'][0]['array']
    df=pd.DataFrame(data=data,columns=['date','open','high','close','low','yesterday','volume','amount','price_chg','percent','turnoverrate','ma5','ma10','ma20','ma30','ma60','afterAmt','afterVol'])
    df.set_index('date',inplace=True)
    df.index=pd.to_datetime(df.index,format='%Y%m%d')
    df=df.apply(pd.to_numeric, errors='coerce').fillna(df)
    if type=='daily':
        df.to_csv(quoFile,encoding='utf-8',index_label='date',date_format='%Y-%m-%d')
    df['percent']=df['percent'].round(4)
    return df

def reportDate():
    '''
    每季度最后一日
    :return:
    '''
    months = [1, 4, 7, 10, 12]
    for i in range(1, len(months)):
        if months[i - 1] <= datetime.now().month < months[i]:
            rmonth = months[i - 1]
    reportDate = datetime(datetime.now().year, rmonth, 1) - timedelta(days=1)
    return reportDate

def heldBy(symbol:str,pdate:dt,mkt='cn'):
    '''
    获取持仓当前股票的基金列表
    :param symbol:
    :return list:
    '''
    if mkt == 'cn':
        symbol=symbol[-6:]
        furl='http://data.eastmoney.com/dataapi/zlsj/detail?SHType=1&SHCode=&SCode=%s&ReportDate=%s&sortField=FREE_SHARES_RATIO&sortDirec=1&pageNum=1&pageSize=290'%(symbol,reportDate().strftime('%Y-%m-%d'))
        response = requests.get(url=furl, headers={"user-agent": "Mozilla"})
        data=pd.DataFrame(json.loads(response.text)['data'])
        if len(data) > 0:
            flist = data[data['PARENT_ORGCODE_OLD'].isin(getFundListSorted()[:30])]['HOLDER_CODE'].to_list()
        else:
            return None
    elif mkt=='hk':
        data=getFundHoldingHK(pdate)
        if len(data) > 0:
            flist = data[data['股票代码']==symbol]['fundCode'].to_list()
        else:
            return None
    else:
        return None
    fname='./fund/'+pdate.strftime('%Y%m%d')+'.csv'
    if os.path.isfile(fname):
        df=pd.read_csv(fname,dtype={'基金代码':str})
    else:
        df=ak.fund_em_open_fund_rank()
        df.drop('序号',1,inplace=True)
        df.to_csv(fname,index=False)
    cols=['单位净值','累计净值','日增长率','近1周','近1月','近3月','近6月','近1年','近2年','近3年','今年来','成立来','自定义']
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce', axis=1)
    df=df[df['基金代码'].isin(flist)].sort_values(by=['近1月', '近1周'], ascending=False)
    if len(df) == 0:
        return df
    df['基金简称'] = df.apply(lambda x: '<a href="http://fund.eastmoney.com/{fundcode}.html">{fundname}</a>'.format(fundcode=x['基金代码'],fundname=x['基金简称']), axis=1)
    df['基金代码'] = df['基金代码'].apply(
        lambda x: '<a href="https://xueqiu.com/S/F{fundcode}">{fundcode}</a>'.format(fundcode=x))
    return df

def renderHtml(df,filename:str,title:str):
    df.index = np.arange(1, len(df) + 1)
    df.index.name='序号'
    df.reset_index(inplace=True)
    #pd.set_option('colheader_justify', 'center')
    html_string = '<html><head><title>%s</title>{style}</head><body>{table}{tablesort}{gAds}</body></html>'%title
    html_string = html_string.format(
        table=df.to_html(render_links=True, escape=False, index=False),
        style='<link rel="stylesheet" type="text/css" href="../link/table.css"/>',
        tablesort='<script src="../link/tablesort.min.js"></script><script src="../link/tablesort.number.min.js"></script><script>new Tablesort(document.getElementById("container"));</script>',
        gAds='<script data-ad-client="ca-pub-7398757278741889" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>'
    )
    with open(filename, 'w') as f:
        f.write(html_string.replace('<table border="1" class="dataframe">','<table id="container">').replace('<th>','<th role="columnheader">'))

def getFundListSorted():
    '''
    获取基金公司规模倒序排名，返回名单
    :return list:
    '''
    furl='http://fund.eastmoney.com/Company/home/gspmlist?fundType=25'
    response = requests.get(url=furl, headers={"user-agent": "Mozilla"})
    html = etree.HTML(response.text)
    result = html.xpath('//td[position()=2]/a/text()')
    return result

# def getFundHolding(fundCode:str):
#     '''
#     基金持仓,数据不全，估计api已无人维护
#     :param fundCode:
#     :return:
#     '''
#     furl='http://datainterface3.eastmoney.com/EM_DataCenter_V3/api/ZLCCMX/GetZLCCMX?tkn=eastmoney&SHType=1&SHCode=%s&SCode=&ReportDate=%s&sortField=SCode&sortDirec=1&pageNum=1&pageSize=1000&cfg=ZLCCMX'%(fundCode,reportDate())
#     response = requests.get(url=furl, headers={"user-agent": "Mozilla"})
#     cols='SCode,SName,RDate,SHCode,SHName,IndtCode,InstSName,TypeCode,Type,ShareHDNum,Vposition,TabRate,TabProRate'.split(',')
#     rawdata = [x.split('|') for x in json.loads(response.text)['Data'][0]['Data']]
#     df = pd.DataFrame(rawdata,columns=cols)
#     df['SCode']=[x[7:]+x[:6] for x in df['SCode']]
#     df.set_index('SCode',inplace=True)
#     return df

def getFundHoldingHK(pdate:dt):
    '''
    生成持仓为港股通的基金列表
    '''
    rDate=reportDate()
    hkQuote = pd.read_csv('md/hk' + pdate.strftime('%Y%m%d') + '_Bak.csv', encoding='GBK')
    df = ak.fund_em_open_fund_rank()
    df.drop('序号', 1, inplace=True)
    df = df[df['基金简称'].str.contains('港股|香港')]
    fundlist = df[['基金代码','基金简称']].copy().set_index('基金代码')
    df['基金简称'] = df.apply(
        lambda x: '<a href="http://fund.eastmoney.com/{fundcode}.html">{fundname}</a>'.format(fundcode=x['基金代码'],
                                                                                     fundname=x['基金简称']), axis=1)
    df['基金代码'] = df['基金代码'].apply(
        lambda x: '<a href="https://xueqiu.com/S/F{fundcode}">{fundcode}</a>'.format(fundcode=x))
    df['weekday']=None
    for i in range(0, 5):
        for calKey in ['_U','_J']:  # 加入url参数（小时），让浏览器不使用缓存
            filename = '../etrobot.github.io/Quant/%s%s%s.html' % ('hk', i + 1, calKey)
            if os.path.isfile(filename):
                with open(filename, "r") as f:
                    output = re.findall('\?t=.*"', f.read())
    renderHtml(df, '../CMS/source/Quant/fundhk.html', '持仓港股的内地基金' + rDate.strftime('%y%m%d'))

    fname='fund/hk'+rDate.strftime('%Y%m%d')+'.csv'
    if os.path.isfile(fname):
        return pd.read_csv(fname,dtype={'fundCode':str})
    mlog('港股基金爬取中...')
    df_hk_holding=pd.DataFrame()
    for fundCode in fundlist.index:
        df_holding=ak.fund_em_portfolio_hold(code=fundCode, year=str(rDate.year))
        if len(df_holding)==0:
            continue
        df_hk=df_holding[df_holding['股票名称'].isin(hkQuote['name'])]
        df_hk['股票代码'] = [x[1:] for x in df_hk['股票代码'].values]
        df_hk['fundCode']=fundCode
        df_hk['fundName']=fundlist.at[fundCode,'基金简称']
        df_hk_holding=df_hk_holding.append(df_hk)
    df_hk_holding.to_csv(fname)
    return df_hk_holding

def getNews(mkt:str,symbol:str,startDate:datetime,midDate:datetime):
    newsDf=pd.DataFrame()
    i=0
    while i<2:
        i+=1
        params = (
            ('_appver', '1.0'),
            ('page', i),
            ('symbol', mkt+symbol),
            ('n', '51'),
            ('_var', 'finance_news'),
            ('type', '2'),
            ('_', int(datetime.now().timestamp() * 10000)),
        )

        response = requests.get('https://proxy.finance.qq.com/ifzqgtimg/appstock/news/info/search',
                                headers={"user-agent": "Mozilla", 'Connection': 'close'}, params=params)
        news = (json.loads(response.text[len('finance_news='):])['data']['data'])
        df=pd.DataFrame(news)
        df['time'] = df['time'].astype('datetime64[ns]').dt.date
        newsDf=newsDf.append(df)
        if df['time'].values[-1]<startDate.date():
            break
    df1=newsDf[newsDf['time']<midDate]
    return len(newsDf)-len(df1)

def xueqiuConcerned(mkt:str,xq_a_token:str)->pd.DataFrame:
    url='https://xueqiu.com/service/screener/screen?category=%s&indcode=&order_by=follow7dpct&order=desc&page=1&size=100&only_count=0&current=&pct=&follow7dpct=0_471.43&_=%s'%(mkt.upper(),int(datetime.now().timestamp() * 10000))
    response = requests.get(url,headers={"user-agent": "Mozilla", 'Connection': 'close',"cookie": xq_a_token})
    result=pd.DataFrame(json.loads(response.text)['data']['list'])
    return result

def getCsvK(filename='symbols.csv',cookie=None):
    if cookie is None:
        cookie = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    df=pd.read_csv(filename,dtype={'symbols':str})
    for k,v in df.iterrows():
        v=v['symbols']
        if len(v)==6:
            if v.startswith('6'):
                v='SH'+v
            if (v.startswith('0') or v.startswith('3')):
                v='SZ'+v
            df.at[k, 'month_percent']=cmsK(v,'monthly')['percent'].values[-1]
        elif len(v)==5:
            qdf= xqQuot(period='month',symbol=v,cookie=cookie)
            qdf=pd.DataFrame(qdf['item'],columns=qdf['column'])
            df.at[k, 'month_percent']=qdf['percent'].values[-1]
    df.to_csv(filename,index=False)
