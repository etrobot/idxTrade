from copy import deepcopy
import sys
from XueqiuPortfolio import *
from QuotaUtilities import *

def crawl_data_from_wencai(question:str):
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9',
               'Cache-Control': 'max-age=0',
               'Connection': 'keep-alive',
               'Upgrade-Insecure-Requests': '1',
               #   'If-Modified-Since': 'Thu, 11 Jan 2018 07:05:01 GMT',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'}

    headers_wc = deepcopy(headers)
    headers_wc["Referer"] = "http://www.iwencai.com/unifiedwap/unified-wap/result/get-stock-pick"
    headers_wc["Host"] = "www.iwencai.com"
    headers_wc["X-Requested-With"] = "XMLHttpRequest"

    Question_url = "http://www.iwencai.com/unifiedwap/unified-wap/result/get-stock-pick"
    """通过问财接口抓取数据

    Arguments:
        trade_date {[type]} -- [description]
        fields {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    payload = {
        # 查询问句
        "question": question,
        # 返回查询记录总数
        "perpage": 5000,
        "query_type": "stock"
    }

    try:
        response = requests.get(Question_url, params=payload, headers=headers_wc)

        if response.status_code == 200:
            json = response.json()
            df_data = pd.DataFrame(json["data"]["data"])
            # 规范返回的columns，去掉[xxxx]内容,并将重复的命名为.1.2...
            cols = pd.Series([re.sub(r'\[[^)]*\]', '', col) for col in pd.Series(df_data.columns)])
            for dup in cols[cols.duplicated()].unique():
                cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
            df_data.columns=cols
            return df_data
        else:
            print("连接访问接口失败")
    except Exception as e:
        print(e)

def conceptSorted(num:int):
    params = (
        ('filter', 'HS,GEM2STAR'),
        ('date',idx.index[-1].strftime('%Y%m%d')),
    )

    response = requests.get('https://data.10jqka.com.cn/dataapi/limit_up/block_top', headers={"user-agent": "Mozilla"}, params=params)
    exclude=['融资融券', '转融券标的', '富时罗素概念股', '标普道琼斯A股', '富时罗素概念', '地方国资改革', '三季报预增','半年报预增', '央企国资改革', '沪股通','深股通', 'MSCI概念', '一带一路', '雄安新区','央企控股','深圳','广东(除深圳)','浙江','江苏','湖北','上海(除浦东)','上海', '山东']

    df=pd.DataFrame(json.loads(response.text)['data'])
    df['limit_up_num'] = pd.to_numeric(df['limit_up_num'], errors='coerce')

    concept=df[~df['name'].isin(exclude)][['name','limit_up_num']].sort_values(by=['limit_up_num'],ascending=False).set_index('name')
    print(concept.to_dict()['limit_up_num'])
    return concept.loc[concept['limit_up_num']>num].index.tolist()

if __name__ == "__main__":
    idx=eastmoneyK('SZ000001')
    cptSorted = conceptSorted(int(sys.argv[-1]))
    MAXHOLDING=4
    xueqiuCfg={'vika': 'xueqiu1',"xueqiu":{'idx':'ZH2492692'}}
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xueqiuPp= xueqiuP.getPosition()['idx']
    position = xueqiuPp['holding']
    cash=xueqiuPp['cash']
    latest=xueqiuPp['latest']
    stockHeld=[x['stock_symbol'] for x in position]

    # buy filter
    df = crawl_data_from_wencai(conf['wencai']['cn'])
    # df.to_csv('test.csv',encoding='GBK')
    # print(df.columns)
    df['code']=df['股票代码'].str[:6]
    df['股票代码'] = df['股票代码'].str[7:] + df['股票代码'].str[:6]
    df['a股市值(不含限售股)']= np.round(pd.to_numeric(df['a股市值(不含限售股)'], errors='coerce')/1000000000)*10
    df['factor']= pd.to_numeric(df["5日均线"], errors='coerce')/(pd.to_numeric(df['跌停价'], errors='coerce')+pd.to_numeric(df['涨停价'], errors='coerce'))*(100+pd.to_numeric(df['最新涨跌幅'], errors='coerce'))
    # df['factor']= df['融资余额增速']
    df['date'] = idx.index[-1]
    if os.path.isfile('limit/limits.csv'):
        limit = pd.read_csv('limit/limits.csv')
        limit = limit[['symbol', 'reason_type']]
        limit.columns = ['股票代码', '概念']
        df = df.merge(limit).dropna(subset=['股票简称'])
    wencaiDf = df
    wencaiDf.sort_values(by=['factor'],ascending=False,inplace=True)
    wdf = wencaiDf.drop_duplicates(subset='股票代码', keep='first')[:10]

    # wdfX700=wdf.loc[wdf['code'].isin(ak.index_stock_hist(index="sh000907")['stock_code'])]
    # wdf = wdf.loc[wdf['a股市值(不含限售股)'].between(min(wdf['a股市值(不含限售股)']),max(wdf['a股市值(不含限售股)']), inclusive='neither')]
    # if len(cptSorted) > 0 :
    #     wdf = wdf.loc[wdf['所属概念'].str.contains('|'.join(cptSorted).replace('(', '\(').replace(')', '\)'), na=False)]
        # if int(sys.argv[-1])>5:
        #     wdf = wdf.loc[wdf['所属概念'].str.contains('|'.join(cptSorted).replace('(', '\(').replace(')', '\)'), na=False)]
        # else:
        #     wdf = wdf.loc[~wdf['所属概念'].str.contains('|'.join(cptSorted).replace('(', '\(').replace(')', '\)'), na=False)]

    # if len(wdfX700)>0:
    #     w=wdfX700.iloc[0]
    # sell filter
    wait4close=False
    limits = getLimit(idx.index[-1])
    twicePortion = round(len(limits[limits['代码'].isin(getLimit(idx.index[-1],mode='x')['代码'].tolist())])/len(limits)*100,2)
    if len(sys.argv) == 2 and datetime.now().hour>=14:
        df2file = wdf[['股票简称', '股票代码', '最新涨跌幅', 'a股市值(不含限售股)', 'factor', 'date']].append(pd.read_csv('wencai.csv'))
        df2file.to_csv('wencai.csv', index=False)
        df2file['股票简称'] = df2file.apply(lambda x: '<a href="https://xueqiu.com/S/{stock_code}">{stock_name}</a>'.format(
            stock_code=x['股票代码'], stock_name=x['股票简称']), axis=1)
        df2file.drop(labels=['股票代码'],axis=1,inplace=True)
        renderHtml(df2file, '../CMS/source/Quant/iwencai.html', '%s%%'%twicePortion)
    limits = limits['代码'].tolist()
    if round(twicePortion) < 20:
        wdf = wdf[~wdf['股票代码'].isin(limits)]
    w = wdf[~wdf['股票代码'].isin(stockHeld)].iloc[0]

    print(w['股票简称'], w['股票代码'], w['最新涨跌幅'],w['a股市值(不含限售股)'],'亿',w['概念'])

    if len(position)>=MAXHOLDING:
        kurl = 'https://xueqiu.com/service/v5/stock/batch/quote?symbol=' + ','.join(stockHeld)
        quotes = json.loads(requests.get(url=kurl, headers={"user-agent": "Mozilla"}).text)['data']['items']
        sortedHoldings = sorted(
            [[x['quote']['symbol'],x['quote']['symbol'] not in wdf['股票代码'].values[:10],float(x['quote']['percent'])] for x in quotes],
            key=lambda x: (x[1],x[2]))
        if latest['error_status'] ==0:
            for stock in latest['rebalancing_histories']:
                if sortedHoldings[-1][0]==stock['stock_symbol'] and stock['target_weight']>0:
                    wait4close=True
        for p in position:
            if p['stock_symbol']==sortedHoldings[-1][0]:
                cash=max(cash,int(p['weight']))
                p['weight']=0
                p["proactive"] = True
                break

    # trade
    if sum(int(x['weight']>0) for x in position) <= MAXHOLDING and len(sys.argv) < 3:
        position.append(xueqiuP.newPostition('cn', w['股票代码'], min(100/MAXHOLDING, cash)))
        if w['股票代码'] in limits or wait4close:
            t.sleep(180)
        xueqiuP.trade('cn','idx',position)
    else:
        pd.options.display.max_rows = 0
        pd.options.display.width = 0
        pd.options.display.colheader_justify = 'left'
        print(wencaiDf[['股票简称', '股票代码', '最新涨跌幅', 'a股市值(不含限售股)', 'factor', 'date','概念']],'\n',twicePortion)