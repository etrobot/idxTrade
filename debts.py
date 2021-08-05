from QuotaUtilities import *
import configparser

if __name__=='__main__':
    pdate=datetime.now()
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    # 获取存储在bmob的雪球cookie
    headersBmob = {
        'X-Bmob-Application-Id': conf['bmob']['X-Bmob-Application-Id'],
        'X-Bmob-REST-API-Key': conf['bmob']['X-Bmob-REST-API-Key'],
        'Connection': 'close'
    }
    bmoburl = 'https://api2.bmob.cn/1/classes/text/'+ conf['bmob']['jsl']
    jslcookie = json.loads(requests.get(bmoburl , headers=headersBmob).text)['text'].replace('\r','')
    debts = ak.bond_cov_jsl(cookie=jslcookie)
    if len(debts)<=30:
        t.sleep(10)
        debts = ak.bond_cov_jsl(cookie=jslcookie)
        if len(debts) <= 30:
            exit()
    debts[['orig_iss_amt', 'year_left', 'force_redeem_price', 'sprice']] = debts[
        ['orig_iss_amt', 'year_left', 'force_redeem_price', 'sprice']].apply(
        pd.to_numeric, errors='coerce')
    debts['stock_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{symbol}">{stnm}</a>'.format(
        symbol=x['stock_id'].upper(), stnm=x['stock_nm']), axis=1)
    debts['距强赎价比'] = debts.apply(lambda x: x['force_redeem_price'] / x['sprice'] - 1, axis=1)
    debts['amp'] = None
    debts['stock_monthK']=None
    debts['bond_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{debcode}">{debname}</a>'.format(
        debcode=x['pre_bond_id'].upper(), debname=x['bond_nm']), axis=1)
    debts['stock_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{symbol}">{stnm}</a>'.format(
        symbol=x['stock_id'].upper(), stnm=x['stock_nm']), axis=1)
    for k,v in tqdm(debts.iterrows(), total=debts.shape[0]):
        bk = eastmoneyK(v['pre_bond_id'])
        amp=[bk['high'][i]/bk['close'][i-1]-1  for i in range(-min(20,len(bk)-1),0)]
        if len(amp)>0:
            debts.loc[k, 'amp']=round(max(amp),4)
    debts = debts.dropna(subset=['amp']).loc[debts['amp']>=0.1]
    t.sleep(60)
    for k, v in tqdm(debts.iterrows(), total=debts.shape[0]):
        sk = eastmoneyK(v['stock_id'])
        if len(sk) > 0:
            sc=sk['close'].values[-22:]
            debts.loc[k, 'stock_monthK']=round(sc[-1]/sc[0]-1,4)
    debts.sort_values(by=['stock_monthK'],ascending=False,inplace=True)
    debts = debts[['bond_nm','year_left','force_redeem_price','sprice','距强赎价比','convert_price_valid_from','volume','premium_rt','orig_iss_amt','amp','stock_nm','stock_monthK']]
    renderHtml(debts, '../CMS/source/Quant/debt.html', '转债' + pdate.strftime('%y%m%d'))
