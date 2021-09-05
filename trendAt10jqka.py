import requests,json
import pandas as pd

def hot10jqka():
    headers = {
        'Accept': 'application/json',
        'Origin': 'https://eq.10jqka.com.cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'ai.iwencai.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
        'Accept-Language': 'zh-cn',
        'Referer': 'https://eq.10jqka.com.cn/',
        'Connection': 'keep-alive',
    }

    params = (
        ('tag', '同花顺热榜_每小时热股_新版'),
        ('userid', '0'),
        ('appName', 'thsHotList'),
        ('hexin-v', 'A7SRabINadOsnv0flt5ctI-qg3Anjdh3GrFsu04VQD_CuV6ndp2oB2rBPEmd'),
    )
    response = requests.get('https://ai.iwencai.com/index/urp/getdata/basic', headers=headers, params=params)
    rj=pd.DataFrame(json.loads(response.text)['answer']['components'][1]['data']['datas'])
    return rj

if __name__ == "__main__":
    rj=hot10jqka()
    concepts=dict()
    exclude=['机构重仓','上海金改', '央视财经50', '融资融券', '深股通', '沪股通', '转融券标的', '富时罗素概念', '富时罗素概念股', 'MSCI概念', '标普道琼斯A股', '同花顺漂亮100','半年报预增']
    for k,v in rj.iterrows():
        cpts=v['所属概念'].split(';')
        for cpt in cpts :
            if cpt in exclude:
                continue
            if cpt not in concepts.keys():
                concepts[cpt]={'概念':cpt,'个股':[],'个股数':0,'热度累加':0,'平均热度':0}
            concepts[cpt]['个股'].append(v['股票名称'])
            concepts[cpt]['个股数']=len(concepts[cpt]['个股'])
            concepts[cpt]['热度累加']+=int(v['个股热度'])
            concepts[cpt]['平均热度']=int(concepts[cpt]['热度累加']/concepts[cpt]['个股数'])
    df=pd.DataFrame(data=concepts.values())
    df=df[df['个股数']>=7]
    print(df['平均热度'].mean())
    df.sort_values(by=['平均热度'],ascending=False,inplace=True)
    df.to_csv('hotConcept10jqka.csv',index=False)