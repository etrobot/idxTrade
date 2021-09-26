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
            # 筛选查询字段，非查询字段丢弃
            df = df_data[fields]
            # 增加列, 交易日期 code 设置索引
            return df.assign(trade_date=trade_date, code=df["股票代码"].apply(lambda x: x[0:6])).set_index("trade_date",drop=False)
        else:
            print("连接访问接口失败")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    MAXHOLDING=4
    idx=eastmoneyK('SZ000001')
    xueqiuCfg={'bmob': '15d5b095f9',"xueqiu":{'idx':'ZH2492692'}}
    # xueqiuCfg={'bmob': 'cc8966d77d',"xueqiu":{'idx':'ZH1353951'}}
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xueqiuPp= xueqiuP.getPosition()['idx']
    position = xueqiuPp['holding']
    cash=xueqiuPp['cash']
    stockHeld=[x['stock_symbol'] for x in position]

    # buy filter
    wencaiDf = pd.DataFrame()
    for k, q in conf['wencai'].items():
        t.sleep(10*(int(list(conf['wencai'].keys()).index(k)!=0)))
        df = crawl_data_from_wencai(q)
        print(df.columns)
        df['股票代码'] = df['股票代码'].str[7:] + df['股票代码'].str[:6]
        df['收盘价:不复权']=pd.to_numeric(df['收盘价:不复权'], errors='coerce')
        df['振幅'] = pd.to_numeric(df['振幅'], errors='coerce')
        df['区间最高价:前复权日'] = pd.to_numeric(df['区间最高价:前复权日'], errors='coerce')
        df['成交量'] = pd.to_numeric(df['成交量'], errors='coerce')
        df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
        df['42日均线'] = np.round(pd.to_numeric(df["42日均线"], errors='coerce'), 2)
        df['a股市值(不含限售股)']= np.round(pd.to_numeric(df['a股市值(不含限售股)'], errors='coerce')/1000000000)
        df['factor']= (df['收盘价:不复权']+df['区间最高价:前复权日']-df['成交额']/df['成交量'])/df['42日均线']
        df['date'] = idx.index[-1]
        df['type'] = k[1:]
        wencaiDf = wencaiDf.append(df[['股票简称', '股票代码','最新涨跌幅', 'a股市值(不含限售股)','factor','date','type']])
    wencaiDf.sort_values(by=['factor'],ascending=False,inplace=True)
    wdf = wencaiDf.drop_duplicates(subset='股票代码', keep='first')[:10]
    wdf = wdf.loc[wdf['a股市值(不含限售股)'].between(min(wdf['a股市值(不含限售股)']),max(wdf['a股市值(不含限售股)']), inclusive='neither')]
    if len(sys.argv) == 1 and datetime.now().hour>=14:
        df2file = wdf.append(pd.read_csv('wencai.csv'))
        df2file.to_csv('wencai.csv', index=False)
        df2file['股票简称'] = df2file.apply(lambda x: '<a href="https://xueqiu.com/S/{stock_code}">{stock_name}</a>'.format(
            stock_code=x['股票代码'], stock_name=x['股票简称']), axis=1)
        df2file.drop(labels=['股票代码'],axis=1,inplace=True)
        renderHtml(df2file, '../CMS/source/Quant/iwencai.html', '问财')
    w=wdf[~wdf['股票代码'].isin(stockHeld)].iloc[0]
    print(w['股票简称'], w['股票代码'], w['最新涨跌幅'])


    # sell filter
    if len(position)>=MAXHOLDING:
        kurl = 'https://xueqiu.com/service/v5/stock/batch/quote?symbol=' + ','.join(stockHeld)
        quotes = json.loads(requests.get(url=kurl, headers={"user-agent": "Mozilla"}).text)['data']['items']
        sortedHoldings = sorted(
            [[x['quote']['symbol'],x['quote']['symbol'] not in wdf['股票代码'].values[:10],float(x['quote']['percent'])] for x in quotes],
            key=lambda x: (x[1],x[2]))
        print(sortedHoldings)
        for p in position:
            if p['stock_symbol']==sortedHoldings[-1][0]:
                cash=int(p['weight'])
                p['weight']=0
                p["proactive"] = True
                break

    # trade
    if sum(int(x['weight']>0) for x in position) <= MAXHOLDING and datetime.now().hour>=14 and len(sys.argv) == 1:
        position.append(xueqiuP.newPostition('cn', w['股票代码'], min(25, cash)))
        if w['股票代码'] in getLimit(idx.index[-1])['代码'].tolist():
            t.sleep(180)
        xueqiuP.trade('cn','idx',position)
    else:
        pd.options.display.max_rows = 999
        print(wencaiDf)