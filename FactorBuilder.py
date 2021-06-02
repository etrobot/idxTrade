from QuotaUtilities import *
import os

class fatcor01:
    def __init__(self,fname:str,test=1):
        self.test=test
        self.fname=fname
        self.xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies[
            'xq_a_token'] + ';'
        self.rK={}
        self.rKm={}

    def ramK(self,symbol:str):
        if symbol not in self.rK.keys():
            self.rK[symbol] = getK(symbol, test=self.test, xq_a_token=self.xq_a_token)
        return self.rK[symbol]

    def ramKMin(self,symbol:str):
        if symbol not in self.rKm.keys():
            filename = 'Quotation/minute/' + symbol + '.csv'
            if os.path.isfile(filename) and self.test==1:
                minDf = pd.read_csv(filename, parse_dates=['day'])
                minDf.set_index('day', inplace=True)
            else:
                stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=symbol, period='1', adjust="qfq")
                minDf = stock_zh_a_minute_df.astype({'day': 'datetime64[ns]', 'close': 'float'}).set_index('day')
                minDf.to_csv('Quotation/minute/' + symbol + '.csv', index_label='day')
            self.rKm[symbol]=minDf
        return self.rKm[symbol]

    def checkMinute(self,k:pd.DataFrame,pdate:datetime):
        c=k[k.index.date==pdate]['close'].values
        if len(c)>0 and min(c[-60:])>c[-238:].mean() and max(c)>max(c[10:120]):
            return True
        return False

    def signal(self)->dict:
        result=dict()
        flist=[x for x in os.listdir('md') if 'limit' in x]
        limit=pd.DataFrame()
        dealed=[]
        for f in flist:
            lmdf=pd.read_csv('md/' + f)
            lmdf['date']=datetime.strptime(f[-12:-4],"%Y%m%d")
            limit=limit.append(lmdf)
        limit=limit[~limit['名称'].str.contains("N|ST", na=False)]
        for s in tqdm(limit['代码']):
            if s in dealed:
                continue
            kLmDates=limit[limit['代码']==s]['date']
            k = getK(s, test=1, xq_a_token=self.xq_a_token).reset_index()
            idxs=[]
            for x in k.loc[k['date'].isin(kLmDates)].index.to_list():
                for i in range(1,7):
                    if x+i not in idxs and x+i<len(k):
                        idxs.append(x+i)
            mk=self.ramKMin(s)
            result[s]=[k['date'][x].date() for x in idxs if self.checkMinute(mk,k['date'][x].date())]
            dealed.append(s)
        return result

    def test(self,symbol:str,datesByfactor:list):
        k=self.ramK(symbol).reset_index()
        idxs=k.loc[k['date'].isin(datesByfactor)].index.to_list()
        idxs=[x+1 for x in idxs]
        result=k.loc[k.index.isin(idxs)][['date','percent']]
        if idxs[-1]>k.index[-1]:
            result.loc[len(result)]=[datetime.now(),np.nan]
        result['symbol']=symbol
        print(result)
        return result

    def run(self):
        result=pd.DataFrame()
        for k,v in self.signal().items():
            result = result.append(self.test(k,v))
        result[['symbol', 'date', 'percent']].to_csv('plotimage/%s.csv' % self.fname)



if __name__ == '__main__':
    # test=test('SH603348',[date(2021,5,13),date(2021,5,20)])
    g=fatcor01('test2021n',0)
    g.run()

