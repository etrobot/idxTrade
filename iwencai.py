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
            # 规范返回的columns，去掉[xxxx]内容
            df_data.columns = [col.split("[")[0] for col in df_data.columns]
            return df_data
            # 筛选查询字段，非查询字段丢弃
            df = df_data[fields]
            # 增加列, 交易日期 code 设置索引
            return df.assign(trade_date=trade_date, code=df["股票代码"].apply(lambda x: x[0:6])).set_index("trade_date",
                                                                                                       drop=False)
        else:
            print("连接访问接口失败")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    idx=eastmoneyK('SZ000001')
    xueqiuCfg={'bmob': '15d5b095f9',"xueqiu":{'idx':'ZH2492692'}}
    # xueqiuCfg={'bmob': 'cc8966d77d',"xueqiu":{'idx':'ZH1353951'}}
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xueqiuPp= xueqiuP.getPosition()['idx']
    position = xueqiuPp['holding']
    cash=xueqiuPp['cash']

    # buy filter
    if len(sys.argv)==1:
        wencaiDf = pd.DataFrame()
        for k, q in conf['wencai'].items():
            df = crawl_data_from_wencai(q)
            df['股票代码'] = df['股票代码'].str[7:] + df['股票代码'].str[:6]
            df['date'] = idx.index[-1]
            df['type'] = k[1:]
            wencaiDf = wencaiDf.append(df[['股票简称', '股票代码','区间振幅', '区间涨跌幅:前复权','date','type']])
    else:
        wencaiDf = pd.read_csv('wencai.csv')
    wencaiDf.sort_values(by=['区间涨跌幅:前复权'],ascending=False,inplace=True)
    wencaiDf = wencaiDf.drop_duplicates(subset='股票代码', keep='first')[:10]
    if len(sys.argv) == 1:
        wencaiDf.append(pd.read_csv('wencai.csv')).to_csv('wencai.csv', index=False)

    # sell filter
    if len(position)==4:
        kurl = 'https://xueqiu.com/service/v5/stock/batch/quote?symbol=' + ','.join(
            x['stock_symbol'] for x in position)
        quotes = json.loads(requests.get(url=kurl, headers={"user-agent": "Mozilla"}).text)['data']['items']
        sortedHoldings = sorted(
            [[x['quote']['symbol'],x['quote']['symbol'] not in wencaiDf['股票代码'].values[:10],float(x['quote']['percent'])] for x in quotes],
            key=lambda x: (x[1],x[2]))
        print(sortedHoldings)
        for p in position:
            if p['stock_symbol']==sortedHoldings[-1][0]:
                cash=int(p['weight'])
                p['weight']=0
                break

    # trade
    position.append(xueqiuP.newPostition('cn', wencaiDf['股票代码'].values[0], min(25, cash)))
    xueqiuP.trade('cn','idx',position)