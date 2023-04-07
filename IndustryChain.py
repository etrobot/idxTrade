import requests,json
import pandas as pd
import time as t
from QuotaUtilities import renderHtml

if __name__=='__main__':
    FILEPATH='html/'
    url='https://m.lbkrs.com/api/forward/industrial/chain/topic?limit=100'
    resp=requests.get(url,headers={"user-agent": "Mozilla"})
    with open(FILEPATH+'industryChain.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(resp.text), f)
    resultList=json.loads(resp.text)['data']['items']
    df=pd.DataFrame()
    for v in resultList:
        for id in v['items']:
            indUrl='https://m.lbkrs.com/api/forward/industrial/chain/id?id='+id['id']
            print(indUrl,v['name']+id['id']+id['name'])
            indjtxt=requests.get(indUrl, headers={"user-agent": "Mozilla"}).text
            indjson=json.loads(indjtxt)
            for x in indjson['data']['items']:
                for y in x['items']:
                    idf=pd.DataFrame(y['stocks'])
                    if len(idf.columns)==0:
                        continue
                    idf = idf.loc[idf['market'] == 'CN']
                    idf['year_chg'] = pd.to_numeric(idf['year_chg'], errors='coerce')
                    idf['month_chg'] = pd.to_numeric(idf['month_chg'], errors='coerce')
                    idf['last_day_chg'] = pd.to_numeric(idf['last_day_chg'], errors='coerce')
                    idf['Ind']=v['name']
                    idf['Chain']='<a href="%s">%s</a>'%('https://app.longbridgehk.com/community/industrial-chains/'+id['id'],id['name'])
                    idf['Part'] = y['name']
                    idf['Part_pct'] = idf['month_chg'].mean()
                    idf = idf.sort_values(by=['month_chg'], ascending=False)
                    idf.reset_index(inplace=True)
                    idf['sort']=idf.index
                    df = pd.concat([df, idf])
            with open(FILEPATH + v['name']+id['id']+id['name'].replace('/','|')+'.json', 'w', encoding='utf-8') as f:
                json.dump(indjson, f)
        # break
        t.sleep(10)
    df=df.sort_values(by=['sort','Part_pct'],ascending=False)
    df.drop_duplicates(subset='counter_id', keep='first', inplace=True)
    df = df.sort_values(by=['Part_pct'], ascending=False)
    df[['year_chg','month_chg','last_day_chg','Part_pct']] = df[['year_chg','month_chg','last_day_chg','Part_pct']].applymap("{0:.2%}".format)
    df=df[['Ind', 'Chain',  'Part', 'Part_pct','market', 'counter_id','name', 'year_chg', 'month_chg','last_day_chg']]
    df.to_csv('test.csv')
    df['counter_id'] = df['counter_id'].apply(
        lambda x: '<a href="https://xueqiu.com/S/{stockCode}">{stockCode}</a>'.format(stockCode=(''.join(x.split('/')[1:])).replace('US','').replace('HK','')))
    renderHtml(df,'html/industryChain.html','产业链')