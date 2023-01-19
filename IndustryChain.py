import requests,json
import time as t

if __name__=='__main__':
    FILEPATH='html/'
    url='https://m.lbkrs.com/api/forward/industrial/chain/topic?limit=100'
    resp=requests.get(url,headers={"user-agent": "Mozilla"})
    with open(FILEPATH+'industryChain.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(resp.text), f)
    resultList=json.loads(resp.text)['data']['items']
    for v in resultList:
        for id in v['items']:
            indUrl='https://m.lbkrs.com/api/forward/industrial/chain/id?id='+id['id']
            print(indUrl,v['name']+id['id']+id['name'])
            indjson=requests.get(indUrl, headers={"user-agent": "Mozilla"}).text
            with open(FILEPATH + v['name']+id['id']+id['name'].replace('/','|')+'.json', 'w', encoding='utf-8') as f:
                json.dump(json.loads(indjson), f)
        t.sleep(10)