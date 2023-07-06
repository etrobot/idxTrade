import asyncio
import re

import requests,json
import pandas as pd
import time as t
from QuotaUtilities import renderHtml,getK
from datetime import datetime
from EdgeGPT import ConversationStyle,Chatbot as bingChat

def crawl():
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
                    idf = idf.loc[idf['market'].isin(['CN','HK','US'])]
                    idf['year_chg'] = pd.to_numeric(idf['year_chg'], errors='coerce')
                    idf['month_chg'] = pd.to_numeric(idf['month_chg'], errors='coerce')
                    idf['last_day_chg'] = pd.to_numeric(idf['last_day_chg'], errors='coerce')
                    idf['Ind']=v['name']
                    idf['chain']=id['name']
                    idf['Chain']='<a href="%s">%s</a>'%('https://app.longbridgehk.com/community/industrial-chains/'+id['id'],id['name'])
                    idf['Part'] = y['name']
                    idf['Part_pct'] = idf['month_chg'].mean()
                    idf = idf.sort_values(by=['month_chg'], ascending=False)
                    idf.reset_index(inplace=True)
                    idf['sort']=idf.index
                    df = pd.concat([df, idf])
            with open(FILEPATH + v['name']+id['id']+id['name'].replace('/','|')+'.json', 'w', encoding='utf-8') as f:
                json.dump(indjson, f)
        t.sleep(10)
    df=df.sort_values(by=['sort','Part_pct'],ascending=False)
    df.drop_duplicates(subset='counter_id', keep='first', inplace=True)
    df = df.sort_values(by=['Part_pct'], ascending=False)
    df[['year_chg','month_chg','last_day_chg','Part_pct']] = df[['year_chg','month_chg','last_day_chg','Part_pct']].applymap("{0:.2%}".format)
    df['counter_id'] = df['counter_id'].apply(
        lambda x: '{stockCode}'.format(
            stockCode=(''.join(x.split('/')[1:])).replace('US', '').replace('HK', '00000'[:5-len(x.split('/')[-1])])))
    df.to_csv('indchain.csv')
    df=df[['Ind', 'Chain',  'Part', 'Part_pct','market', 'counter_id','name', 'year_chg', 'month_chg','last_day_chg']]
    df['counter_id'] = df['counter_id'].apply(
        lambda x: '<a href="https://xueqiu.com/S/{stockCode}">{stockCode}</a>'.format(stockCode=x))
    renderHtml(df,'../CMS/source/Quant/industryChain.html','产业链')

def addPerfomance():
    df=pd.read_csv('indchain.csv',index_col='counter_id')
    lenth=60
    for k,v in df.iterrows():
        print(k)
        quo=getK(k,pdate=datetime.now().date(),xq_a_token=xq_a_token,test=0)
        if len(quo) < 60:
            continue
        quo=quo[-lenth:]
        if not 'percent' in quo.columns:
            percent=[quo['close'][i]/quo['close'][i-1]-1 for i in range(1,len(quo))]
            percent.insert(0,0)
            quo['percent']=percent
        upVol= sum(quo['volume'][x] for x in range(lenth) if quo['percent'][x]<0)
        downVol= sum(quo['volume'][x] for x in range(lenth) if quo['percent'][x]<0)
        perfomance=round(upVol/downVol/quo['close'][-1]*quo['close'][0],4)
        df.at[k,'p_amt']=perfomance
    df.dropna(subset=['p_amt'],inplace=True)
    df.sort_values(by=['p_amt'],ascending=False,inplace=True)
    df.to_csv('indchain.csv',encoding='utf_8_sig')

def writeArts():
    df=pd.read_csv('indchain.csv')
    for mkt in ['CN','US','HK']:
        df=df[df['market']==mkt].iloc[:20]
        stock_counts = df.groupby('chain')['counter_id'].count()
        if len(stock_counts)==0:
            continue
        chain=stock_counts.idxmax()
        stocks='、'.join(df[df['chain']==chain]['name'].tolist())
        bingArticle(chain,stocks)
        t.sleep(10)

def bingArticle(chain,stocks):
    prompt = '写一篇研报，从产业链角度分析『%s』概念（相关个股有%s等）在近未来的前景，包含产值预测和风险，涉及数字的部分请用网络资料' % (
    chain, stocks)
    print(prompt)
    with open('./cookies.json', 'r') as f:
        cookies = json.load(f)
        bingBot = bingChat(cookies=cookies, proxy='http://127.0.0.1:7890')
        response = asyncio.run(bingBot.ask(prompt=prompt, conversation_style=ConversationStyle.creative,
                                           wss_link="wss://sydney.bing.com/sydney/ChatHub"))
        replyTxt: str = response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
        print(replyTxt)

        replyTxt = re.sub(r'\[\^\d+\^\]', '', replyTxt)
        replyTxt = replyTxt.replace('[', '【').replace(']', '】')
        lines = replyTxt.split('\n')
        http_links = []
        output_lines = []
        for line in lines:
            if 'http' in line:
                http_links.append(line)
            elif '？' not in line and '?' not in line:
                output_lines.append(line)
        output = '\n'.join(output_lines) + '\n参考:\n' + '\n'.join(http_links)
        print(output)


if __name__=='__main__':
    crawl()
    global xq_a_token
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    addPerfomance()
    writeArts()
    # bingArticle('ChatGPT','MSFT、NVDA')