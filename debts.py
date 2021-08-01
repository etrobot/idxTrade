from QuotaUtilities import *

if __name__=='__main__':
    pdate=datetime(2021,7,31)
    jslcookie='kbz__Session=ha205pagu7mc61ocqvpgb7mm33; kbz__user_login=1ubd08_P1ebax9aX3Nbo0NXn1ZGcoenW3Ozj5tTav9Cjl6nDqd2nn6vS25rXx9fZlqKR2LClnK3Oqcbaw6ytmKOCr6bq0t3K1I2nk6yumqmWlbSivrrK1I3D0O3hzdzCo66jmZmUxMPZyuHs0OPJr5m-1-3R44LDwtaYsMOBzJmmmdidrMGtipO50eDN2dDay8TV65GrlKqmlKaBnMS9vca4o4Liyt7dgbfG1-Tkkpmv39TlztinmqKPpKepnqqhpZOmmJPLwtbC5uKknqyjpZWs; SERVERID=5452564f5a1004697d0be99a0a2e3803|1627698004|1627697578'
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
