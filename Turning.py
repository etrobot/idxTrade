from weekly import *
from pyecharts.globals import ThemeType
from pyecharts import options as opts
from pyecharts.charts import HeatMap
from pyecharts.commons.utils import JsCode


def xueqiuMonthK(symbol='.IXIC',cookie=''):
    url="https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=month&type=before&count=-284&indicator=kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"%(symbol,int((datetime.now()-timedelta(hours=8)).timestamp()*1000))
    idxyear=json.loads(getUrl(url,cookie))['data']
    df= pd.DataFrame(data=idxyear['item'],columns=idxyear['column'])
    df.set_index(['timestamp'], inplace=True)
    df.index = pd.to_datetime(df.index, unit='ms', utc=True)
    df['date'] = df.index.date
    return df

def getSymbols(filename='html/turning.csv'):
    all = ak.stock_us_spot_em().rename(
        columns={'总市值': 'mktValue'})
    all.dropna(inplace=True)
    all['代码'] = [x.split('.')[1] for x in all['代码']]
    all = all[['mktValue', '代码']]
    all.set_index('代码', inplace=True)
    df = invesco('QQQ')[['Holding Ticker', 'Sector']]
    df.columns = ['Ticker', 'Sector']
    df = df.append(ssga('SPY')[['Ticker', 'Sector']])
    df = df.append(ssga('DIA')[['Ticker', 'Sector']])
    df.dropna(inplace=True)
    df.drop_duplicates(subset='Ticker', keep='last', inplace=True)
    df.set_index('Ticker', inplace=True)
    df = df[~df.index.str.contains('_')]
    df = df[(df.index != 'GOOG')]
    df = df.join(all)
    futuSymbols = pd.read_csv("futuSymbols.csv", index_col='股票简称')[['股票名称']]
    df = df.join(futuSymbols)
    sector = list(df.groupby('Sector').groups.keys())
    sectorCN = translate(','.join(sector)).split('，')
    sector2CN = {sector[x]: sectorCN[x] for x in range(len(sector))}
    df['Sector'] = [sector2CN[x] for x in df['Sector']]
    df.to_csv(filename)
    return filename

def getK(filename='html/turning.csv'):
    xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    symbols=pd.read_csv(filename,index_col='Ticker')
    kDf=pd.DataFrame()
    for symbol, item in symbols.iterrows():
        print(symbol)
        tempK = xueqiuMonthK(symbol,cookie=xq_a_token)[['date','amount','percent']]
        tempK['symbol']=symbol
        tempK['name']=item['股票名称']
        tempK['Sector'] = item['Sector']
        kDf=kDf.append(tempK)
    kDf.to_csv(filename,index=False)
    return filename

def heatmap(filename='html/turning.csv'):
    df = pd.read_csv(filename, parse_dates=['date'])
    df = df[df['date'] > pd.Timestamp(2021, 12, 31)]
    df = df.sort_values('amount', ascending=False).drop_duplicates(['date', 'Sector'])
    df = df.sort_values('date')
    gdf = df.pivot_table('percent', 'date', 'Sector')
    gdf=gdf.reindex(columns=['信息技术', '公用事业', '医疗保健', '房地产', '材料', '能源', '通讯服务', '金融',
       '非必需消费品','工业', '必需消费品'])
    gdf_s=df.pivot_table(index=['date'], columns=['Sector'], values='symbol', aggfunc=np.sum)
    gdf_s = gdf_s.reindex(columns=['信息技术', '公用事业', '医疗保健', '房地产', '材料', '能源', '通讯服务', '金融',
                               '非必需消费品', '工业', '必需消费品'])
    gdf_n = df.pivot_table(index=['date'], columns=['Sector'], values='name', aggfunc=np.sum)
    gdf_n = gdf_n.reindex(columns=['信息技术', '公用事业', '医疗保健', '房地产', '材料', '能源', '通讯服务', '金融',
                                   '非必需消费品', '工业', '必需消费品'])
    gdf=gdf.transpose()
    gdf_s = gdf_s.transpose()
    gdf_n = gdf_n.transpose()
    print(gdf.columns)
    gdfList = gdf.values.tolist()
    gdfSList = gdf_s.values.tolist()
    gdfNList = gdf_n.values.tolist()

    # print(gdf.index, len(gdf), len(gdf.columns), len(gdfList), len(gdfList[0]))
    rangeNum = max(abs(df['percent'].min()), df['percent'].max())
    # gdf.to_csv('html/TurningBySectorAndDate.csv')
    c = (
        HeatMap(init_opts=opts.InitOpts(theme=ThemeType.DARK))
            .add_xaxis(gdf.columns.date.tolist())
            .add_yaxis(
            "涨跌幅",
            gdf.index.tolist(),
            [{"value":[i, j, gdfList[j][i]],"name":gdfNList[j][i],"symbol":gdfSList[j][i]} for i in range(len(gdf.columns)) for j in range(len(gdfList))],
            tooltip_opts=opts.TooltipOpts(formatter=JsCode("""function(params) {return params.data.name+'<br>'+params.data.symbol+'<br>'+(params.data.value[2]>0?'+'+params.data.value[2]:params.data.value[2])+'%';}""")),
            label_opts=opts.LabelOpts(is_show=True, position="inside"),
        )
            .set_series_opts(zlevel=-1)
            .set_global_opts(
            legend_opts=opts.LegendOpts(is_show=True),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=30),
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(width=1,color="#2d2d2d")),
                # position="top"
            ),
            yaxis_opts=opts.AxisOpts(
                position="right",
                axislabel_opts=opts.LabelOpts(),
                splitline_opts=opts.SplitLineOpts(is_show=True,
                                                  linestyle_opts=opts.LineStyleOpts(width=5, color="#2d2d2d")),
            ),
            visualmap_opts=opts.VisualMapOpts(
                min_=-rangeNum,
                max_=rangeNum,
                range_color=['#269f3c', '#aaa', '#942e38'],
                is_calculable=True,
                pos_top="center"
            ),
        )
            .render("html/heatmap_with_label_show.html")
    )

if __name__=='__main__':
    filename = heatmap(getK(getSymbols('html/turning.csv')))

