# 策略收益计算
from QuotaUtilities import *
import akshare as ak
from matplotlib.font_manager import _rebuild
from tqdm import tqdm
from matplotlib import rcParams
import matplotlib.pyplot as plt

def factor_1(kdf):#计算因子值,越小越好
    if len(kdf['close'].values) < 30:
        return 999
    cls = kdf['close'].values[-30:]
    mtm_1 =[cls[i] / min(cls[0],cls[-1])-1 for i in range(15)]
    mtm_2 = [cls[i] / cls[-1]-1 for i in range(-15,0)]
    return sum(mtm_1)+sum(mtm_2)

def factor_2(kdf):#计算因子值,越小越好
    if len(kdf['close'].values) < 25:
        return 999
    cls = kdf['close'].values[-25:]
    ampl=[abs(kdf['low'][i]-kdf['high'][i]) for i in range(-5,0)]
    amplMinIdx=ampl.index(min(ampl))
    mtm_1 =[cls[i] / max(cls[amplMinIdx:amplMinIdx+10])-1 for i in range(amplMinIdx,amplMinIdx+20)]
    mtm_2 = [cls[i] / cls[-1]-1 for i in range(10-amplMinIdx,5-amplMinIdx)]
    return sum(mtm_1)+sum(mtm_2)

def indexStocksCN(idx):
    print(idx)
    index_stock_cons_df = ak.index_stock_cons(index=idx[2:])
    # print(index_stock_cons_df)
    index_stock_cons_df.drop_duplicates(subset='品种代码', keep='first', inplace=True)
    index_stock_cons_df.set_index('品种代码', inplace=True)
    # 今日全场股票概况（价格、市值等）
    df = ak.stock_zh_a_spot()
    df.set_index('symbol', inplace=True)
    # 按总市值排顺序，只保留指数成份股
    df = df.loc[df.index.isin([dealSymbol(s) for s in index_stock_cons_df.index])].copy()
    df.sort_values(by='mktcap', ascending=True,inplace=True)
    df = df.iloc[:int(len(df)/2)-1]
    # 计算因子值
    days=30
    sortedDf=pd.DataFrame()
    tqdmRange=tqdm(range(len(df)))
    tqdmRange=tqdm([-3,-2,-1])
    for i in tqdmRange:
        symbol = dealSymbol(df.index[i])
        tqdmRange.set_description("cauculating factor value for %s" % symbol)
        factorVaule_1 = []
        factorVaule_2 = []
        stockK = ak.stock_zh_index_daily_tx(symbol=symbol)
        stockK['symbol'] = symbol
        for j in range(0,len(stockK)):
            if j<days:
                factorVaule_1.append(None)
                factorVaule_2.append(None)
                continue
            factorVaule_1.append(factor_1(stockK.iloc[j-days:j]))
            factorVaule_2.append(factor_1(stockK.iloc[j - days:j]))
        stockK['factor_1'] = factorVaule_1
        stockK['factor_2'] = factorVaule_2
        stockK.to_csv('Quotation/'+symbol+'.csv')
        stockK=stockK[['symbol','factor_1','factor_2']].copy()
        stockK.reset_index(inplace=True)
        sortedDf=sortedDf.append(stockK)
    sortedDf.sort_values(by=['date','factor_1'], ascending=True,inplace=True)
    sortedDf.dropna(subset=['factor_1'], inplace=True)
    sortedDf.to_csv(idx+'factor.csv')
    sortedDf['date']=pd.to_datetime(sortedDf['date']).date
    return sortedDf

def idxSignal(kdf,param,days):#指数信号
    signal=[]
    navBySig=[]
    # if param[0]=='signal off':
    #     return signal,navBySig
    cs = kdf['close']
    ma20 = cs.rolling(window=20).mean()
    i = -1
    while i < len(cs) - 1:
        i += 1
        if i < days:
            signal.append(1)
            navBySig.append(1)
            continue
        c,m=cs[i-days:i],ma20[i-days:i]
        if c.index[-1].month == 12 and c.index[-1].day == 25:
            #         print('年')
            signal.append(0)
        elif c.values.argmax() >= param[1] and sum(int(c[j] < m[j]) for j in range(-5, 0)) > param[2]:
            #         print('顶')
            signal.append(0)
        elif c.values.argmin() >= param[3] and sum(int(c[j] > m[j]) for j in range(-5,0)) > param[4]:
            #         print('底')
            signal.append(1)
        else:
            signal.append(signal[-1])
    
        if signal[-1] == 1:
            navBySig.append(navBySig[-1] * cs[i]/cs[i-1])
        else:
            navBySig.append(navBySig[-1])

    return signal,navBySig

def dealSymbol(symbol):#为纯数字代码加上'sh'或'sz'前缀
    if len(str(symbol))==8:
        return symbol
    sbl="%06d" %int(symbol)
    if sbl.startswith('6'):
        return 'sh'+sbl
    return 'sz'+sbl

def preparePlot():
    # print(matplotlib_fname())
    # print(plt.style.available)
    rcParams['font.family'] = ['sans-serif']
    rcParams['font.sans-serif']=['Source Han Sans CN']  # 用来正常显示中文标签
    rcParams['axes.unicode_minus']=False  # 用来正常显示负号
    _rebuild()
    plt.style.use(['fivethirtyeight','seaborn-notebook'])

def idxCompare(mkt,cfg,mode='idx',backtest=0):
    iK = dict()
    ikKeys=list(cfg['paramSet'][mode].keys())
    ikKeys.insert(0,cfg['baseIdx'])
    # 获取行情
    for iCode in tqdm(ikKeys):
        # if backtest and os.path.isfile('Quotation/'+iCode+'.csv'):
        #     iK[iCode] = pd.read_csv('Quotation/'+iCode+'.csv',encoding='GB18030',index_col=0)
        #     iK[iCode].index=pd.to_datetime(iK[iCode].index).date
        # else:
        iK[iCode] = xueqiuK(symbol=iCode,cookie=cfg['xq_a_token'])
    tradeGap = 20
    num = min(len(x) for x in iK.values()) // tradeGap * tradeGap
    if backtest:
        preparePlot()
        fig = plt.figure(0, figsize=(2, 1))
    for iCode in ikKeys:
        print(iCode)
        iK[iCode] = iK[iCode].iloc[-num:]
        cs = iK[iCode]['close']
        iK[iCode][iCode + '_nav'] = [cs[j] / cs[0] for j in range(len(cs))]
        if iCode != cfg['baseIdx']:
            # navs = [1]
            # for j in range(1, len(iK[iCode])):
            #     navs.append(round(navs[-1] * (1 + iK[iCode]['percent'][j] / 100),4))
            # iK[iCode][iCode + '_nav'] = navs
            iK[iCode][iCode + '_sig'], iK[iCode][iCode + '_navBySig'] = idxSignal(iK[iCode], cfg['paramSet'][mode][iCode], 30)
        if backtest:
            if iCode == cfg['baseIdx']:
                iK[iCode][iCode + '_nav'].plot()
            # else:
            #     iK[iCode][iCode + '_nav'].plot()
    # 比对指数
    days = 20
    i = -days
    mix = []
    mixType='nav'
    compare=[]
    while i < len(iK[cfg["baseIdx"]]) - days:
        i += days
        if i < days:
            mix.extend([1.0 for r in range(days)])
            continue
        navForCompare = -999
        for iCode in cfg['paramSet'][mode].keys():
            ctype = iCode + '_'+mixType
            nav20 = iK[iCode][ctype][i] / iK[iCode][ctype][i - days]*(days-iK[iCode][ctype][i-days:i].argmin())
            compare.append((iCode,nav20))
            if nav20 > navForCompare:
                navForCompare = nav20
                gIdx = iCode
                # print(iCode,navForCompare)
        ctype = gIdx + '_'+mixType
        mix.extend([mix[-1] * iK[gIdx][ctype][r] / iK[gIdx][ctype][i] for r in range(i, i+days)])
    iK[cfg['baseIdx']]['mix'] = mix
    compare=sorted (compare, key=lambda x:x[-1],reverse=True)
    if backtest:
        iK[cfg['baseIdx']]['mix'].plot()
        fig.legend()
        plt.show()
    return {'idx':gIdx,'k':iK[gIdx],'list':[x[0] for x in compare[:3]]}

def usETF():
    encode='GB18030'
    paramSetEtf={}
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    df = usETFlist()
    df=df.apply(pd.to_numeric, errors='coerce').fillna(df)
    df = df[df['volume']>0]
    # df.dropna(subset=['symbol','volume','mktcap'],inplace=True)
    df.set_index('symbol', inplace=True)
    df=df[df['category']=='股权']
    # df.to_csv('usETF.csv',encoding=encode)
    # df=pd.read_csv('usETF.csv',encoding=encode)
    daysInMkt,growth,navChange,estimateAmoutAvg,divdDealed=[[] for i in range(5)]
    tqdmRange=tqdm(df.index)
    for symbol in tqdmRange:
        tqdmRange.set_description("US ETF %s" % symbol)
        # etfK=xueqiuK(symbol=symbol,cookie=xq_a_token)
        # etfK=tencentK('us',symbol,KAll=True)
        etfK=pd.read_csv('Quotation/'+symbol+'.csv',encoding=encode)
        # etfK=etfK.apply(pd.to_numeric, errors='coerce').fillna(etfK)
        vol=etfK['volume'].values
        cls,opn,high,low,pct=etfK['close'].values,etfK['open'].values,etfK['high'].values,etfK['low'].values,etfK['percent'].values
        daysInMkt.append(len(etfK))
        divdDealed.append(max(round(cls[j]/cls[j-1]-1-pct[j]/100,4) for j in range(max(len(etfK)-40,0),len(etfK))))
        # divdDealed.append(cls[-1]/cls[-2]-1-pct[-1]/100)
        growth.append(cls[-1]/cls[0])
        navChange.append(max(cls)/min(cls[min(cls.argmax(),cls.argmin())],cls[0]))
        estimateAmoutAvg.append(sum(sum([cls[i],opn[i],high[i],low[i]])/4*vol[i] for i in range(len(cls)))/len(cls))
    df['daysInMkt'],df['growth'],df['navChange'],df['estimateAmoutAvg'],df['divdDealed'] = daysInMkt,growth,navChange,estimateAmoutAvg,divdDealed
    df=df.loc[df['daysInMkt']>=2000]
    df=df.loc[df['estimateAmoutAvg']>df['estimateAmoutAvg'].median()]
    df=df.loc[df['divdDealed']<0.0001]
    df.to_csv('usETF.csv',encoding=encode)
    for f in df.index:
        paramSetEtf[f]=["signal off", 15, 4, 7, 4]
    return paramSetEtf