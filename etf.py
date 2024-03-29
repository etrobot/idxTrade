from QuotaUtilities import *
import sys

def etfHolding():
    rdate=reportDate()
    all = ak.fund_em_etf_fund_daily()
    etf=all[all['类型']=='指数型-股票']
    etf.set_index('基金代码',inplace=True)
    df=pd.DataFrame()
    for k,v in tqdm(etf.iterrows(), total=etf.shape[0]):
        holding=ak.fund_em_portfolio_hold(code=k, year=rdate.year)
        if len(holding)==0:
            continue
        holding=holding[holding['季度']==holding['季度'].values[0]]
        holding['etf_code']=k
        holding['etf']=v['基金简称']
        etfK=ak.fund_em_etf_fund_info(fund=k)
        etfK['累计净值'] = pd.to_numeric(etfK['累计净值'], errors='coerce')
        holding['etf_ma20/60']=etfK['累计净值'][-20:].mean()/etfK['累计净值'][-60:].mean()
        df = df.append(holding)
    df.drop(labels=['序号'],axis=1,inplace=True)
    df.to_csv('etf.csv',index=False)

def dealFundCode(code:str):
    if code.startswith('5'):
        return 'SH'+code
    else:
        return 'SZ'+code

def etfStocks():
    etf=pd.read_csv('etf.csv',dtype={'股票代码':str,'etf_code':str})
    es=etf[etf['占净值比例']<0.1].copy()
    es=es.sort_values(by=['占净值比例'],ascending=False)
    es.drop_duplicates(subset='股票代码', keep='first',inplace=True)
    ah=ak.stock_hk_spot_em().set_index('代码')
    for k,v in es.iterrows():
        symbol=v['股票代码']
        if '.' in symbol:
            es.loc[k,'股票代码'] = symbol.split('.')[0]
        elif symbol[-5:] in ah.index and ah.loc[symbol[-5:],'名称']==v['股票名称']:
            es.loc[k,'股票代码'] = symbol[-5:]
        else:
            if symbol.startswith('6'):
                es.loc[k,'股票代码'] = 'SH'+symbol
            else:
                es.loc[k,'股票代码'] = 'SZ'+symbol
    es.set_index('股票代码', inplace=True)
    es['Percent']=None
    es['ma20/ma60'] = None
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    for k, v in tqdm(es.iterrows(), total=es.shape[0]):
        kk = getK(k, xq_a_token=xq_a_token)
        if len(kk)>0:
            cls=kk['close'].values
            es.loc[k, 'Percent'] = round(cls[-1]/cls[-2]-1,4)
            es.loc[k, 'ma20/ma60'] = round(cls[-20:].mean() / cls[-60:].mean(),4)
    es['股票名称'] = es.apply(lambda x: '<a href="https://xueqiu.com/S/{stock_code}">{stock_name}</a>'.format(
        stock_code=x.name, stock_name=x['股票名称']), axis=1)
    es['etf'] = es.apply(
        lambda x: '<a href="https://xueqiu.com/S/{fundcode}">{fundname}</a>'.format(fundcode=dealFundCode(x['etf_code']),fundname=x['etf']), axis=1)
    es=es[['股票名称','Percent','ma20/ma60','etf','占净值比例']]
    es.sort_values(by=['ma20/ma60'],ascending=False,inplace=True)
    renderHtml(es, '../CMS/source/Quant/etf.html', 'etf')

if __name__=='__main__':
    if len(sys.argv) > 1:
        etfHolding()
    etfStocks()