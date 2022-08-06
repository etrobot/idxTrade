from yahoo_fin import news as yNews
from datetime import datetime
from time import mktime
from iwencai import crawl_data_from_wencai
import re,requests
import demjson
from QuotaUtilities import renderHtml,pd

if __name__ == "__main__":
    resp = requests.get('https://xueqiu.com/S/.IXIC', headers={"user-agent": "Mozilla"})
    quote = demjson.decode(re.search(r'(?<=<script>window.STOCK_PAGE = true;SNB = ).*(?=;</script><script>window.analytics_config = )', resp.text.replace('\n','')).group())
    tradeDate = datetime.utcfromtimestamp(quote['data']['quote']['timestamp']/1000)
    df = crawl_data_from_wencai("美股市场，非ETF，交易市场不是NYSE Arca，成交额>1000万，向上跳空缺口")
    dfNewsLen=[]
    for symbol in df['股票代码']:
        nws = yNews.get_yf_rss(symbol.split(".")[0])
        news=[x['link'] for x in nws if datetime.utcfromtimestamp(mktime(x['published_parsed'])).date()==tradeDate.date()]
        dfNewsLen.append(len(news))
    df = df[['股票代码', '股票简称', '美股@成交额', '美股@振幅', '美股@最新价', '美股@最新涨跌幅', 'hqCode']]
    df['美股@振幅'] = pd.to_numeric(df['美股@振幅'], errors='coerce')
    df['美股@最新涨跌幅'] = pd.to_numeric(df['美股@最新涨跌幅'], errors='coerce')
    df['NewsLen']=dfNewsLen
    df=df.loc[(df['NewsLen']>0)&(df['美股@振幅']>2.5)&(df['美股@最新涨跌幅']>2.5)]
    df=df.sort_values('NewsLen',ascending=False)
    df['股票代码'] = df.apply(
        lambda x: '<a href="https://finance.yahoo.com/quote/{hqcode}/news/">{symbol}</a>'.format(hqcode=x['hqCode'],
                                                                                        symbol=x['股票代码']), axis=1)
    df['股票简称'] = df.apply(
        lambda x: '<a href="https://xueqiu.com/S/{hqcode}">{name}</a>'.format(hqcode=x['hqCode'],
                                                                                                 name=x['股票简称']),
        axis=1)
    df['NewsLen'] = df.apply(
        lambda x: '<a href="https://feeds.finance.yahoo.com/rss/2.0/headline?s={hqcode}">{newsLen}</a>'.format(hqcode=x['hqCode'],
                                                                              newsLen=x['NewsLen']),
        axis=1)
    renderHtml(df,'../CMS/source/Quant/wc_us_%s.html' % tradeDate.weekday(),tradeDate.strftime("%Y-%m-%d"))
