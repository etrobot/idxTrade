import pandas as pd

from QuotaUtilities import *

def getLimits():
    szzs = eastmoneyK('SZ000001')
    # print(szzs.index[-1460])
    filename='limit/limits.json'
    cols=['symbol','name','max','industry','region','city','ipodate','limits','times','latest']#代码，名称，最高板,行业,省份,城市，上市日，≥3连板纪录，次数，最后连板日期
    end = 0
    if os.path.isfile(filename):
        start=end-1
        lmDict = json.loads(open(filename, "r").read())
        limitDf = pd.read_csv('limit/limits.csv', index_col='symbol')
    else:
        start = -1460
        lmDict = {}
        limitDf=pd.DataFrame([],columns=cols)
    infos={}
    if not os.path.isfile('info.csv'):
        getAllInfo()
    all = pd.read_csv('info.csv',dtype={'股票代码': str})
    all.set_index('股票代码',inplace=True)
    for i in range(start,end):
        szIdx = szzs.index[i].strftime("%Y%m%d")
        df = getLimit(szzs.index[i])
        for idx,row in df.iterrows():
            # print(szIdx,row['代码'],row['名称'])
            if row['代码'] not in infos.keys() and row['代码'] not in limitDf.index:
                infos[row['代码']] = getInfo(row['代码'],all)
            if row['代码'] not in lmDict.keys():
                lmDict[row['代码']]=[[szIdx]]
            elif len(lmDict[row['代码']])>0:
                if lmDict[row['代码']][-1][-1]==szzs.index[i-1].strftime("%Y%m%d"):
                    lmDict[row['代码']][-1].append(szIdx)
                elif lmDict[row['代码']][-1][-1]!=szzs.index[i].strftime("%Y%m%d"):
                    lmDict[row['代码']].append([szIdx])

    maxDates=[]
    for k in lmDict.keys():
        info=infos.get(k,{})
        name=limitDf['name'].get(k,info.get('股票简称',None))
        if name is None:
            continue
        ipodate=limitDf['ipodate'].get(k,info.get('上市时间',None))
        industry=limitDf['industry'].get(k,info.get('行业',None))
        region=limitDf['region'].get(k,info.get('region',None))
        city=limitDf['city'].get(k,info.get('city',None))
        lmDict[k] = [x for x in lmDict[k] if str(ipodate) != x[0][:8] or ((k.startswith('SZ300') and int(x[0][:8])>20200823))]
        if len(lmDict[k])==0:
            continue
        counts=[]
        for dates in lmDict[k]:
            counts.append(len(dates))
        print(k,info,lmDict[k])
        records=[x[0].replace('-','')+"-%s"%len(x) for x in lmDict[k] if len(x)>2]
        if len(records)>0:
            maxDates.append([k,name.replace(' ',''),max(counts),industry,region,city,ipodate,', '.join(records),len(records),records[-1]])

    df=pd.DataFrame(maxDates,columns=cols)
    df=df[~df['name'].str.contains('\*|退')]
    df=df.sort_values(by=['latest','max'],ascending=False)
    df.to_csv('limit/limits.csv',index=False)
    df['symbol'] = df['symbol'].apply(
        lambda x: '<a href="https://xueqiu.com/S/{fundcode}">{fundcode}</a>'.format(fundcode=x))
    renderHtml(df[df['max']>2], '../CMS/source/Quant/limits.html', '连板统计')
    string = json.dumps(lmDict)
    with open('limit/limits.json', 'w') as f:
        f.write(string)

def limitStatistic(idxdate:datetime,mode=None):
    print(idxdate.strftime('%Y%m%d'))
    cookies = {
        'Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1': '1640619309,1642582805',
        'hxmPid': '',
        'v': 'A0aSl97zW6psJw9OiWEn2CdlkTfNp4vvXOm-xTBvMghEJ-jpmDfacSx7DtgD',
    }
    params = (
        ('page', '1'),
        ('limit', '1600'),
        ('field', '199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004'),
        ('filter', 'HS,GEM2STAR'),
        ('date', idxdate.strftime('%Y%m%d')),
        ('order_field', '330324'),
        ('order_type', '0'),
        ('_', '1643899326926'),
    )

    response = requests.get('https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool',headers={"user-agent": "Mozilla"}, params=params, cookies=cookies)
    result=json.loads(response.text)
    with open('limit/%s.json' % idxdate.strftime('%Y%m%d'), 'w', encoding='utf-8') as f:
        json.dump(result,f)
    return
    llist=[]
    data = result['data']['info']
    for d in data:
        if d['high_days'] in [None, '首板']:
            continue
        highDays = [int(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", d['high_days'])]
        if len(highDays) == 2 and highDays[0] - highDays[1] < 2 and highDays[1] > 2:
            llist.append([idxdate, d['code'], highDays[0], highDays[1]])
    if mode is not None:
        return pd.DataFrame(llist, columns=['date', 'symbol', 'days', 'highLimit'])
    df=pd.read_csv('limit/limit.csv',dtype={'symbol':str})
    df.append(pd.DataFrame(llist,columns=['date','symbol','days','highLimit']))
    df=df.drop_duplicates(subset='symbol', keep='last', inplace=False)
    df = df.sort_values(by=['date'], ascending=True)
    # gb=df.groupby('date')
    # for k,v in gb:
    #     print(k,v['symbol'].tolist())
    df.to_csv('limit/limit.csv',index=False)

def storeJson():
    idx = eastmoneyK('SZ000001')
    df=pd.DataFrame()
    for i in idx.index[-258:]:
          df=df.append(limitStatistic(i,mode='new'))
    df.to_csv('limit/limit.csv', index=False)


if __name__ == "__main__":
    # storeJson()
    # limitStatistic(eastmoneyK('SZ000001').index[-1])
    getLimits()

