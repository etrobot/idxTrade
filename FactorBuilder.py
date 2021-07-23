from QuotaUtilities import *
import os,sys

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
            if os.path.isfile(filename) and self.test>0:
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
        # c=c[30:len(c)-30]
        if len(c)>0 and c[-1]!=c[0]:
            return 1-min(c[0],c[-1])/max(c[0],c[-1])#*[1, -1][c[-1]-c[0]<0]
        # print(c)
        return np.nan

    def signal(self)->dict:
        result=dict()
        idxDates=getK('SH000001').index[-self.test:]
        flist=['limit'+x.strftime("%Y%m%d")+'.csv' for x in idxDates]
        flist.reverse()
        limit=pd.DataFrame()
        dealed=[]
        for f in flist:
            fdate=datetime.strptime(f[-12:-4],"%Y%m%d").date()
            if not os.path.isfile(f):
                getLimit(fdate)
            lmdf=pd.read_csv('md/' + f)
            lmdf['date']=fdate
            lmdf=lmdf[~lmdf['名称'].str.contains("N|ST", na=False)]
            tqdmRange = tqdm(lmdf.iterrows(), total=lmdf.shape[0])
            for k,v in tqdmRange:
                s=v['代码']
                if s in dealed:
                    continue
                k = getK(s, test=self.test, xq_a_token=self.xq_a_token).reset_index()
                if len(k)<20:
                    continue
                data=np.transpose([[k['date'].values[x],abs(k['close'].values[x]/k['open'].values[x]-1)] for x in range(-self.test,0)])
                if len(data)==0:
                    continue
                df=pd.DataFrame({'date':data[0],'value':data[1]})
                df['symbol'] = s
                df['name'] = v['名称']
                result[s] = df
                # result[s]=df[~df['date'].isin(kLmDates)]
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


def iwenCai():
    cookies = {
        'cid': '8817705f14c45d78c7cc16cde099c2381626082768',
        'user': 'MDpteF8zNTEzMzM3OTE6Ok5vbmU6NTAwOjM2MTMzMzc5MTo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoxNjo6OjM1MTMzMzc5MToxNjI2MDgyNzk1Ojo6MTQ3MjI3MDEwMDo4NjQwMDowOjE5MTA4MDg2OGUyZjU0MzFlNzVhYTAwMGY5YTQyZTE3ZTpkZWZhdWx0XzQ6MA%3D%3D',
        'userid': '351333791',
        'u_name': 'mx_351333791',
        'escapename': 'mx_351333791',
        'ticket': '3948239a03292ac6cb7c5f64c5a5d99e',
        'user_status': '0',
        'utk': '6aef4ce07f00a2192c00f7d8adeaffa5',
        'v': 'AxbWLAkkahTPHF6wqsRY3SkXYccbt10lrPiOR4B_AgGQzrhx6EeqAXyL3nxT',
    }

    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Origin': 'http://www.iwencai.com',
        'Referer': 'http://www.iwencai.com/',
        'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
    }

    params = (
        ('iwcpro', '1'),
    )

    data = {
        'query': '\u975E\u9000\u5E02\uFF0C\u975Est\uFF0C\u8FD160\u65E5\u6DA8\u505C<10\uFF0C\u8FD130\u65E5\u9F99\u864E\u699C>1\uFF0C\u6700\u65B0\u4EF7>5\u65E5\u6700\u4F4E\u4EF7,\u6210\u4EA4\u91CF>5\u65E5\u6700\u4F4E\u6210\u4EA4\u91CF,ma5>ma20',
        'urp_sort_way': 'desc',
        'urp_sort_index': '{(}\u6536\u76D8\u4EF7:\u4E0D\u590D\u6743[20210719]{-}\u533A\u95F4\u6700\u4F4E\u4EF7:\u524D\u590D\u6743[20210713-20210719]{)}',
        'page': '1',
        'perpage': '100',
        'condition': '[{"chunkedResult":"\u975E\u9000\u5E02,_&_\u975Est,_&_\u8FD160\u65E5\u6DA8\u505C<10,_&_\u8FD130\u65E5\u9F99\u864E\u699C>1,_&_\u6700\u65B0\u4EF7>5\u65E5\u6700\u4F4E\u4EF7,_&_\u6210\u4EA4\u91CF>5\u65E5\u6700\u4F4E\u6210\u4EA4\u91CF,_&_ma5>ma20","opName":"and","opProperty":"","sonSize":18,"relatedSize":0},{"indexName":"\u80A1\u7968\u7B80\u79F0","indexProperties":["\u4E0D\u5305\u542B\u9000,st"],"source":"new_parser","type":"index","indexPropertiesMap":{"\u4E0D\u5305\u542B":"\u9000,st"},"reportType":"null","valueType":"_\u80A1\u7968\u7B80\u79F0","domain":"abs_\u80A1\u7968\u9886\u57DF","uiText":"\u80A1\u7968\u7B80\u79F0\u4E0D\u5305\u542B\u9000","sonSize":0,"queryText":"\u80A1\u7968\u7B80\u79F0\u4E0D\u5305\u542B\u9000","relatedSize":0,"tag":"\u80A1\u7968\u7B80\u79F0"},{"opName":"and","opProperty":"","sonSize":16,"relatedSize":0},{"indexName":"\u80A1\u7968\u7B80\u79F0","indexProperties":["\u4E0D\u5305\u542B\u9000,st"],"source":"new_parser","type":"index","indexPropertiesMap":{"\u4E0D\u5305\u542B":"\u9000,st"},"reportType":"null","valueType":"_\u80A1\u7968\u7B80\u79F0","domain":"abs_\u80A1\u7968\u9886\u57DF","uiText":"\u80A1\u7968\u7B80\u79F0\u4E0D\u5305\u542Bst","sonSize":0,"queryText":"\u80A1\u7968\u7B80\u79F0\u4E0D\u5305\u542Bst","relatedSize":0,"tag":"\u80A1\u7968\u7B80\u79F0"},{"opName":"and","opProperty":"","sonSize":14,"relatedSize":0},{"dateText":"\u8FD160\u65E5","indexName":"\u6DA8\u505C\u6B21\u6570","indexProperties":["\u8D77\u59CB\u4EA4\u6613\u65E5\u671F 20210421","\u622A\u6B62\u4EA4\u6613\u65E5\u671F 20210719","<10"],"dateUnit":"\u65E5","source":"new_parser","type":"index","indexPropertiesMap":{"\u8D77\u59CB\u4EA4\u6613\u65E5\u671F":"20210421","\u622A\u6B62\u4EA4\u6613\u65E5\u671F":"20210719","<":"10"},"reportType":"TRADE_DAILY","dateType":"+\u533A\u95F4","valueType":"_\u6574\u578B\u6570\u503C(\u6B21|\u4E2A)","domain":"abs_\u80A1\u7968\u9886\u57DF","uiText":"\u8FD160\u65E5\u7684\u6DA8\u505C\u6B21\u6570<10\u6B21","sonSize":0,"queryText":"\u8FD160\u65E5\u7684\u6DA8\u505C\u6B21\u6570<10\u6B21","relatedSize":0,"tag":"[\u8FD160\u65E5]\u6DA8\u505C\u6B21\u6570"},{"opName":"and","opProperty":"","sonSize":12,"relatedSize":0},{"dateText":"\u8FD130\u65E5","indexName":"\u533A\u95F4\u4E0A\u699C\u6B21\u6570","indexProperties":["\u8D77\u59CB\u4EA4\u6613\u65E5\u671F 20210604","\u622A\u6B62\u4EA4\u6613\u65E5\u671F 20210716","(1"],"dateUnit":"\u65E5","source":"new_parser","type":"index","indexPropertiesMap":{"(":"1","\u8D77\u59CB\u4EA4\u6613\u65E5\u671F":"20210604","\u622A\u6B62\u4EA4\u6613\u65E5\u671F":"20210716"},"reportType":"TRADE_DAILY","dateType":"+\u533A\u95F4","valueType":"_\u6574\u578B\u6570\u503C(\u5BB6|\u6B21)","domain":"abs_\u80A1\u7968\u9886\u57DF","uiText":"\u8FD130\u65E5\u7684\u533A\u95F4\u4E0A\u699C\u6B21\u6570>1\u5BB6","sonSize":0,"queryText":"\u8FD130\u65E5\u7684\u533A\u95F4\u4E0A\u699C\u6B21\u6570>1\u5BB6","relatedSize":0,"tag":"[\u8FD130\u65E5]\u533A\u95F4\u4E0A\u699C\u6B21\u6570"},{"opName":"and","opProperty":"","sonSize":10,"relatedSize":0},{"opName":"-","opProperty":"(0","uiText":"\u6536\u76D8\u4EF7>5\u65E5\u7684\u533A\u95F4\u6700\u4F4E\u4EF7","sonSize":2,"queryText":"\u6536\u76D8\u4EF7>5\u65E5\u7684\u533A\u95F4\u6700\u4F4E\u4EF7","relatedSize":2},{"reportType":"TRADE_DAILY","dateType":"\u4EA4\u6613\u65E5\u671F","indexName":"\u6536\u76D8\u4EF7:\u4E0D\u590D\u6743","indexProperties":["nodate 1","\u4EA4\u6613\u65E5\u671F 20210719"],"valueType":"_\u6D6E\u70B9\u578B\u6570\u503C(\u5143|\u6E2F\u5143|\u7F8E\u5143|\u82F1\u9551)","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"source":"new_parser","tag":"\u6536\u76D8\u4EF7:\u4E0D\u590D\u6743","type":"index","indexPropertiesMap":{"\u4EA4\u6613\u65E5\u671F":"20210719","nodate":"1"}},{"dateText":"5\u65E5","indexName":"\u533A\u95F4\u6700\u4F4E\u4EF7:\u524D\u590D\u6743","indexProperties":["\u8D77\u59CB\u4EA4\u6613\u65E5\u671F 20210713","\u622A\u6B62\u4EA4\u6613\u65E5\u671F 20210719"],"dateUnit":"\u65E5","source":"new_parser","type":"index","indexPropertiesMap":{"\u8D77\u59CB\u4EA4\u6613\u65E5\u671F":"20210713","\u622A\u6B62\u4EA4\u6613\u65E5\u671F":"20210719"},"reportType":"TRADE_DAILY","dateType":"+\u533A\u95F4","valueType":"_\u6D6E\u70B9\u578B\u6570\u503C(\u5143|\u6E2F\u5143|\u7F8E\u5143|\u82F1\u9551)","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"tag":"[5\u65E5]\u533A\u95F4\u6700\u4F4E\u4EF7:\u524D\u590D\u6743"},{"opName":"and","opProperty":"","sonSize":6,"relatedSize":0},{"opName":"-","opProperty":"(0","uiText":"\u6210\u4EA4\u91CF>5\u65E5\u7684\u533A\u95F4\u6700\u4F4E\u6210\u4EA4\u91CF","sonSize":2,"queryText":"\u6210\u4EA4\u91CF>5\u65E5\u7684\u533A\u95F4\u6700\u4F4E\u6210\u4EA4\u91CF","relatedSize":2},{"reportType":"TRADE_DAILY","dateType":"\u4EA4\u6613\u65E5\u671F","indexName":"\u6210\u4EA4\u91CF","indexProperties":["nodate 1","\u4EA4\u6613\u65E5\u671F 20210719"],"valueType":"_\u6D6E\u70B9\u578B\u6570\u503C(\u80A1)","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"source":"new_parser","tag":"\u6210\u4EA4\u91CF","type":"index","indexPropertiesMap":{"\u4EA4\u6613\u65E5\u671F":"20210719","nodate":"1"}},{"dateText":"5\u65E5","indexName":"\u533A\u95F4\u6700\u4F4E\u6210\u4EA4\u91CF","indexProperties":["\u8D77\u59CB\u4EA4\u6613\u65E5\u671F 20210713","\u622A\u6B62\u4EA4\u6613\u65E5\u671F 20210719"],"dateUnit":"\u65E5","source":"new_parser","type":"index","indexPropertiesMap":{"\u8D77\u59CB\u4EA4\u6613\u65E5\u671F":"20210713","\u622A\u6B62\u4EA4\u6613\u65E5\u671F":"20210719"},"reportType":"TRADE_DAILY","dateType":"+\u533A\u95F4","valueType":"_\u6D6E\u70B9\u578B\u6570\u503C(\u80A1)","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"tag":"\u6210\u4EA4\u91CF"},{"opName":"-","opProperty":"(0","uiText":"5\u65E5\u7684\u5747\u7EBF>20\u65E5\u7684\u5747\u7EBF","sonSize":2,"queryText":"5\u65E5\u7684\u5747\u7EBF>20\u65E5\u7684\u5747\u7EBF","relatedSize":2},{"reportType":"TRADE_DAILY","dateType":"\u4EA4\u6613\u65E5\u671F","indexName":"\u5747\u7EBF","indexProperties":["nodate 1","n\u65E5 5\u65E5","\u4EA4\u6613\u65E5\u671F 20210719"],"valueType":"_\u6D6E\u70B9\u578B\u6570\u503C","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"source":"new_parser","tag":"[5\u65E5]\u5747\u7EBF","type":"tech","indexPropertiesMap":{"\u4EA4\u6613\u65E5\u671F":"20210719","n\u65E5":"5\u65E5","nodate":"1"}},{"reportType":"TRADE_DAILY","dateType":"\u4EA4\u6613\u65E5\u671F","indexName":"\u5747\u7EBF","indexProperties":["nodate 1","n\u65E5 20\u65E5","\u4EA4\u6613\u65E5\u671F 20210719"],"valueType":"_\u6D6E\u70B9\u578B\u6570\u503C","domain":"abs_\u80A1\u7968\u9886\u57DF","sonSize":0,"relatedSize":0,"source":"new_parser","tag":"[20\u65E5]\u5747\u7EBF","type":"tech","indexPropertiesMap":{"\u4EA4\u6613\u65E5\u671F":"20210719","n\u65E5":"20\u65E5","nodate":"1"}}]',
        'codelist': '',
        'indexnamelimit': '',
        'logid': '6c12a67f2a0c00046ef13b8007222c54',
        'ret': 'json_all',
        'sessionid': 'b1027e25dd49ee9675a7a84ae01a702f',
        'date_range[0]': '20210421',
        'date_range[1]': '20210719',
        'iwc_token': '0ac952ad16266754796622873',
        'urp_use_sort': '1',
        'user_id': 'Ths_iwencai_Xuangu_pk6oblkz5ckj6c8f8qwrxwl7nenz7dge',
        'uuids[0]': '24087',
        'query_type': 'stock',
        'comp_id': '5722297',
        'business_cat': 'soniu',
        'uuid': '24087'
    }

    response = requests.post('http://ai.iwencai.com/urp/v7/landing/getDataList', headers=headers, params=params, cookies=cookies, data=data, verify=False)

    # NB. Original query string below. It seems impossible to parse and
    # reproduce query strings 100% accurately so the one below is given
    # in case the reproduced version is not "correct".
    # response = requests.post('http://ai.iwencai.com/urp/v7/landing/getDataList?iwcpro=1', headers=headers, cookies=cookies, data=data, verify=False)

    result=json.loads(response.text)
    for k,v in result.items():
        print(k,v)


if __name__ == '__main__':
    # g=fatcor01('test2021ttt',int(sys.argv[1]))
    # g.run()
    iwenCai()