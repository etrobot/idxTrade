from QuotaUtilities import *

def getlimit(idxdate:datetime,mode=None):
    print(idxdate.strftime('%Y%m%d'))
    cookies = {
        'Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1': '1640619309,1642582805',
        'hxmPid': '',
        'v': 'A0aSl97zW6psJw9OiWEn2CdlkTfNp4vvXOm-xTBvMghEJ-jpmDfacSx7DtgD',
    }

    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
        'Accept': 'application/json, text/plain, */*',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        'sec-ch-ua-platform': '"macOS"',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html?client_userid=nM9Y3&back_source=hyperlink&share_hxapp=isc&fontzoom=no',
        'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
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
          df=df.append(getlimit(i,mode='new'))
    df.to_csv('limit/limit.csv', index=False)


if __name__ == "__main__":
    # storeJson()
    getlimit(eastmoneyK('SZ000001').index[-1])

