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
    debts = debts[['pre_bond_id', 'bond_nm', 'stock_id', 'convert_price_valid_from', 'stock_nm', 'orig_iss_amt','volume','premium_rt','year_left','force_redeem_price','sprice']]
    debts['amp']=None
    tqdmRange = tqdm(debts.iterrows(), total=debts.shape[0])
    for k,v in tqdmRange:
        dk= eastmoneyK(v['pre_bond_id'])
        amp=[dk['high'][i]/dk['close'][i-1]-1  for i in range(-min(20,len(dk)-1),0)]
        if len(amp)>0:
            v['amp']=max(amp)
    debts['bond_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{debcode}">{debname}</a>'.format(
        debcode=x['pre_bond_id'].upper(), debname=x['bond_nm']), axis=1)
    debts['stock_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{symbol}">{stnm}</a>'.format(
        symbol=x['stock_id'].upper(), stnm=x['stock_nm']), axis=1)
    debts[['orig_iss_amt', 'year_left', 'force_redeem_price', 'sprice']] = debts[
        ['orig_iss_amt', 'year_left', 'force_redeem_price', 'sprice']].apply(
        pd.to_numeric, errors='coerce')
    debts['stock_nm'] = debts.apply(lambda x: '<a href="https://xueqiu.com/S/{symbol}">{stnm}</a>'.format(
        symbol=x['stock_id'].upper(), stnm=x['stock_nm']), axis=1)
    debts['距强赎价比'] = debts.apply(lambda x: x['force_redeem_price'] / x['sprice'] - 1, axis=1)
    debts = debts.dropna(subset=['amp']).sort_values(by=['amp'],ascending=False)
    renderHtml(debts, '../CMS/source/Quant/debt.html', '转债强赎现价比' + pdate.strftime('%y%m%d'))
