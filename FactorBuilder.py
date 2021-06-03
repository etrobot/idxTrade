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

    def ramK(self,symbol:str)->pd.DataFrame:
        if symbol not in self.rK.keys():
            self.rK[symbol] = getK(symbol, test=self.test, xq_a_token=self.xq_a_token)
        return self.rK[symbol]

    def ramKMin(self,symbol:str)->pd.DataFrame:
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
        c=c[30:len(c)-30]
        if len(c)>0 and c[-1]!=c[0]:
            return max(c)/min(c)-max(c[-1],c[0])/min(c[-1],c[0])
        return np.nan

    def signal(self)->dict:
        result=dict()
        flist=['limit'+x.strftime("%Y%m%d")+'.csv' for x in getK('SH000001').index[-7:]]
        limit=pd.DataFrame()
        dealed=[]
        for f in flist:
            fdate=datetime.strptime(f[-12:-4],"%Y%m%d").date()
            if not os.path.isfile(f):
                getLimit(fdate)
            lmdf=pd.read_csv('md/' + f)
            lmdf['date']=fdate
            limit=limit.append(lmdf)
        # dealed=limit.drop_duplicates(subset='代码')['代码'].to_list()[:-2]
        limit=limit[~limit['名称'].str.contains("N|ST", na=False)]
        tqdmRange = tqdm(limit.iterrows(), total=limit.shape[0])
        for k,v in tqdmRange:
            s=v['代码']
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
            data=np.transpose([[k['date'][x].date(),self.checkMinute(mk,k['date'][x].date())] for x in idxs])
            if len(data)==0:
                continue
            df=pd.DataFrame({'date':data[0],'value':data[1]})
            df['symbol'] = s
            df['name'] = v['名称']
            result[s]=df[~df['date'].isin(kLmDates)]
            print(result[s])
            dealed.append(s)
        return result

    def backtest(self,symbol:str,data:pd.DataFrame):
        print(symbol)
        data.set_index('date',inplace=True)
        k=self.ramK(symbol)
        k['percent']=k['percent'].shift(-1)
        k=k[['percent']]
        result = data.join(k)
        result = result[['value','percent','symbol','name']]
        result=result[~result.index.duplicated(keep='first')]
        print(result)
        return result

    def run(self):
        result=pd.DataFrame()
        for k,v in self.signal().items():
            result = result.append(self.backtest(k,v))
        result[['symbol','name', 'value', 'percent']].to_csv('plotimage/%s.csv' % self.fname)



if __name__ == '__main__':
    g=fatcor01('test2021ttt')
    g.run()