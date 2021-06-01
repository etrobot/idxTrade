from QuotaUtilities import *
import os

def fatcor01():
    result=pd.DataFrame()
    flist=[x for x in os.listdir('md') if 'limit' in x]
    limit=pd.DataFrame()
    dealed=[]
    for f in flist:
        lmdf=pd.read_csv('md/' + f)
        lmdf['date']=datetime.strptime(f[-12:-4],"%Y%m%d")
        limit=limit.append(lmdf)
    limit=limit[~limit['名称'].str.contains("N|ST", na=False)]
    for s in limit['代码']:
        if s in dealed:
            continue
        kLmDates=limit[limit['代码']==s]['date']
        k = getK(s, test=1, xq_a_token=xq_a_token)
        k = k[~k.index.isin(kLmDates)][-20:]
        print(s)
        mk=getMinute(s)
        checkedDates=[x for x in k.index if checkMinute(mk,x)]
        result.append(test(s,checkedDates))
        dealed.append(s)
    result.to_csv('plotimage/testf01.csv')
    return

def test(symbol:str,datesByfactor:list):
    k=getK(symbol,test=1,xq_a_token=xq_a_token).reset_index()
    idxs=k.loc[k['date'].isin(datesByfactor)].index.to_list()
    idxs=[x+1 for x in idxs]
    result=k.loc[k.index.isin(idxs)][['date','percent']]
    result['symbol']=symbol
    print(result)
    return result

def checkMinute(k:pd.DataFrame,pdate:datetime):
    c=k[k.index.date==pdate]['close'].values
    # print(c,pdate)
    if min(c[-60:])>c[-240:].mean():
        return True
    return False


def getMinute(symbol:str):
    filename='Quotation/minute/'+symbol+'.csv'
    if os.path.isfile(filename):
        minDf = pd.read_csv(filename, parse_dates = ['day'])
        minDf.set_index('day',inplace=True)
    else:
        stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=symbol, period='1', adjust="qfq")
        minDf=stock_zh_a_minute_df.astype({'day':'datetime64[ns]','close':'float'}).set_index('day')
        minDf.to_csv('Quotation/minute/'+symbol+'.csv',index_label='day')
    return minDf

if __name__ == '__main__':
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    # test=test('SH603348',[date(2021,5,13),date(2021,5,20)])
    fatcor01()

