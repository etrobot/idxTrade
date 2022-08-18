# coding=utf-8
# from idxTrade import *
import shlex
import sys,configparser,os,json,re
from datetime import *
import requests,demjson
from lxml import etree
import pandas as pd
import akshare as ak

import asyncio
from pyppeteer import launch

from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus

import cv2
from tqdm import tqdm
from mutagen.mp3 import MP3
from moviepy.editor import VideoFileClip, AudioFileClip,concatenate_videoclips

from XueqiuPortfolio import *
from iwencai import crawl_data_from_wencai
from QuotaUtilities import renderHtml
from translate import *

FOLDER='video/'
MAXHOLDING=4

IS_PY3 = sys.version_info.major == 3
conf = configparser.ConfigParser()
conf.read('config.ini')
API_KEY = conf['baidu']['API_KEY']
SECRET_KEY = conf['baidu']['SECRET_KEY']


# 发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美
PER = 0
# 语速，取值0-15，默认为5中语速
SPD = 6
# 音调，取值0-15，默认为5中语调
PIT = 2
# 音量，取值0-9，默认为5中音量
VOL = 5
# 下载的文件格式, 3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav
AUE = 3

FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
FORMAT = FORMATS[AUE]

CUID = "123456PYTHON"

TTS_URL = 'http://tsn.baidu.com/text2audio'

"""  TOKEN start """

TOKEN_URL = 'http://aip.baidubce.com/oauth/2.0/token'
SCOPE = 'audio_tts_post'  # 有此scope表示有tts能力，没有请在网页里勾选


class DemoError(Exception):
    pass

def fetch_token():
    print("fetch token begin")
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    if (IS_PY3):
        post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print('token http response http code : ' + str(err.code))
        result_str = err.read()
    if (IS_PY3):
        result_str = result_str.decode()

    print(result_str)
    result = json.loads(result_str)
    print(result)
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not SCOPE in result['scope'].split(' '):
            raise DemoError('scope is not correct')
        print('SUCCESS WITH TOKEN: %s ; EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
        return result['access_token']
    else:
        raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')
"""  TOKEN end """


def text2voice(text:str,audioFile='result'):
    token = fetch_token()
    tex = quote_plus(text)  # 此处TEXT需要两次urlencode
    print(tex)
    params = {'tok': token, 'tex': tex, 'per': PER, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
              'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数

    data = urlencode(params)
    print('test on Web Browser' + TTS_URL + '?' + data)

    req = Request(TTS_URL, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()

        headers = dict((name.lower(), value) for name, value in f.headers.items())

        has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
    except  URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_str = err.read()
        has_error = True

    save_file = FOLDER+"error.txt" if has_error else FOLDER+audioFile+'.' + FORMAT
    with open(save_file, 'wb') as of:
        of.write(result_str)

    if has_error:
        if (IS_PY3):
            result_str = str(result_str, 'utf-8')
        print("tts api  error:" + result_str)

    print("result saved as :" + save_file)
    return FOLDER+audioFile+'.' + FORMAT

def is_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def getSinaNews(symbol:str):
    url='http://biz.finance.sina.com.cn/usstock/usstock_news.php?pageIndex=1&symbol=%s&type=1'%symbol
    print(url)
    resp=requests.get(url=url, headers={"user-agent": "Mozilla"})
    resp.encoding = 'GB18030'
    html = etree.HTML(resp.text.replace(' | ','|'))
    df=pd.DataFrame()
    df['title'] = html.xpath('//ul[@class="xb_list"]//a/text()')
    df['url'] = html.xpath('//ul[@class="xb_list"]//a/@href')
    dateTxt= html.xpath('//ul[@class="xb_list"]//span[@class="xb_list_r"]/text()')
    df['dateText'] =dateTxt
    df['date']=[datetime.strptime(x.split('|')[1],"%Y年%m月%d日 %H:%S")  for x in dateTxt]
    df=df[~df['title'].str.contains("美股", na=False)]
    df = df[~df['dateText'].str.contains("全景网动态|环球市场播报|环球网快看", na=False)]
    df = df[df['date']>datetime.now()-timedelta(days=180)]
    # df = df[df['url'].str.contains("2022", na=False)]
    return df[['title','dateText']]

# 合成视频
def get_video(count:int,symbol:str,videoFile=FOLDER + 'video.mp4'):
    imageFile = FOLDER + symbol+'.png'
    fps = 1      # 帧率
    img_size = (1920, 1080)      # 图片尺寸
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    videoWriter = cv2.VideoWriter(videoFile, fourcc, fps, img_size)
    for i in tqdm(range(0, count)):
        frame = cv2.imread(imageFile)
        frame = cv2.resize(frame, img_size)  # 生成视频   图片尺寸和设定尺寸相同
        videoWriter.write(frame)  # 将图片写进视频里
    videoWriter.release()  # 释放资源


# 加入音频
def get_audio(symbol:str,videoFile=FOLDER+'video.mp4'):
    video = VideoFileClip(videoFile)
    videos = video.set_audio(AudioFileClip(FOLDER+symbol+'.mp3'))  # 音频文件
    videos.write_videofile(FOLDER+symbol+'.mp4')  # 保存合成视频


# 计算每个音频的时间（秒）
def get_time_count(audioFile='result'):
    audio = MP3(FOLDER+audioFile+".mp3")
    time_count = int(audio.info.length)
    return time_count

def futuComInfo(symbol:str):
    url='https://www.futunn.com/stock/%s-US/company-profile'%symbol
    html=etree.HTML(requests.get(url=url, headers={"user-agent": "Mozilla"}).text.replace(', ','，').replace('Inc.',''))
    info= html.xpath('//div[@class="value"]/text()')
    if len(info)>0 and '。' in info[-1]:
        comInfo=info[-1].split('。')[0]
        if info[1]==comInfo[:len(info[1])]:
            return comInfo
        else:
            return info[1] + comInfo
    return ''

def futuKLine(symbol:str):
    if os.path.isfile("futuSymbols.csv"):
        futuSymbols = pd.read_csv("futuSymbols.csv")
    else:
        futuSymbols = ak.stock_us_code_table_fu()
        futuSymbols.to_csv("futuSymbols.csv",index=False)
    futuSymbol=futuSymbols[futuSymbols['股票简称'] == symbol].代码
    print(futuSymbol)
    kline = ak.stock_us_hist_fu(symbol=futuSymbol)
    kline.rename(columns={"日期": "date", "今开": "open", "今收": "close", "最高": "high", "最低": "low", "成交量": "volume",
                          "成交额": "amount"}, inplace=True)
    kline.set_index(pd.to_datetime(kline['date'], format="%Y-%m-%d"), inplace=True)
    for col in ["open", "close", "high", "low"]:
        kline[col] = kline[col] / 10
    return kline

def genEchartJson(qdf:pd.DataFrame):
    qdf['date']=qdf.index.strftime('%m-%d').tolist()
    transdf = qdf[['date', 'open', 'close', 'low', 'high', 'volume']].copy()
    transdf.T
    with open(FOLDER+'videoQuote.json', 'w', encoding='utf-8') as f:
        json.dump(transdf.values.tolist(), f)

async def browserShot(url:str,symbol:str):
    imageFile = FOLDER + symbol +'.png'
    width, height = 960, 540
    browser = await launch(headless=True, args=['--disable-infobars', f'--window-size={width}, {height}'])
    page = await browser.newPage()
    await page.setViewport({
        'width': width, 'height': height,'deviceScaleFactor':2})
    await page.goto(url)
    # await page.evaluate('document.body.style.zoom=1.2')
    await page.screenshot({'path': imageFile, 'fullPage': False})
    await browser.close()

def latestTradeDate():
    resp = requests.get('https://xueqiu.com/S/.IXIC', headers={"user-agent": "Mozilla"})
    quote = demjson.decode(
        re.search(r'(?<=<script>window.STOCK_PAGE = true;SNB = ).*(?=;</script><script>window.analytics_config = )',
                  resp.text.replace('\n', '')).group())
    latestTradeDate = datetime.utcfromtimestamp(quote['data']['quote']['timestamp'] / 1000)
    return latestTradeDate

def genStockVideo(symbol:str,tradeDate:datetime):
    tradeDateTxt = tradeDate.strftime('%Y/%m/%d')
    newsDf = getSinaNews(symbol)
    companyInfo = futuComInfo(symbol)
    latestNews=newsDf.iloc[0]['title']
    if not is_contain_chinese(latestNews):
        translateInstance=BaiduTranslateSpider()
        latestNews=translateInstance.attack_bd(latestNews)
    readText = '，'.join([companyInfo, '最新一条新闻',latestNews , '来源', newsDf.iloc[0]['dateText']])+'。'
    print(readText)
    newsTable = newsDf[:6].to_html(index=False).replace('<table', '<table class="table"')
    with open("Template/quoteTemp.xhtml", "r") as fin:
        with open(FOLDER + "quote.html", "w") as fout:
            fout.write(
                fin.read().replace('{{title}}', symbol + ' ' + tradeDateTxt).replace('{{news}}', newsTable).replace(
                    '{{companyInfo}}', companyInfo))
    # futu begin

    # futu end
    genEchartJson(futuKLine(symbol))
    genVideo('http://127.0.0.1:5500/quote.html',readText,symbol)

def genVideo(targetUrl:str,readText:str,symbol='symbol'):
    asyncio.get_event_loop().run_until_complete(browserShot(targetUrl,symbol))
    text2voice(readText,symbol)
    get_video(get_time_count(symbol),symbol)
    get_audio(symbol)

def trade(xueqiuCfg:dict,symbols=()):
    if len(symbols) ==0:
        return
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xqPp = xueqiuP.getPosition()['idx']
    cash = xqPp['cash']
    position = xqPp['holding']
    kurl = 'https://xueqiu.com/service/v5/stock/batch/quote?symbol=' + ','.join(x['stock_symbol'] for x in xqPp['holding'])
    quotes = json.loads(requests.get(url=kurl, headers={"user-agent": "Mozilla"}).text.replace('null','0'))['data']['items']
    if len(position) >= MAXHOLDING:
        sortedHoldings = sorted([[x['quote']['symbol'], x['quote']['symbol'] not in symbols[:10], float(x['quote']['percent'])] for x in quotes],key=lambda x: (x[1], x[2]))
        for p in position:
            if p['stock_symbol'] == sortedHoldings[-1][0]:
                cash = max(cash, int(p['weight']))
                p['weight'] = 0
                p["proactive"] = True
                break
    print(symbols[0])
    position.append(xueqiuP.newPostition('us', symbols[0], min(100/MAXHOLDING, cash)))
    xueqiuP.trade('us', 'idx', position)
    return xqPp['holding']


def genTradeVideo(tradeDate:datetime,xueqiuCfg:dict):
    tradeDateTxt = tradeDate.strftime('%Y/%m/%d')
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xqPp= xueqiuP.getPosition()['idx']
    latest=pd.DataFrame(xqPp['latest']['rebalancing_histories'])[['stock_symbol','stock_name','prev_target_weight','target_weight']]
    latestDf=latest.rename(columns={'stock_symbol':'股票代码','stock_name':'企业名称','prev_target_weight':'调仓前','target_weight':'目标仓位'}).to_html(index=False).replace('<table','<table class="table"')
    holding=pd.DataFrame(xqPp['last']['holdings'])[['stock_symbol','stock_name','weight']]
    holdingDf=holding.rename(columns={'stock_symbol':'股票代码','stock_name':'企业名称','weight':'持仓百分比'}).to_html(index=False).replace('<table','<table class="table"')
    data=xueqiuP.getCube()
    with open(FOLDER+'cube.json', 'w') as outfile:
        json.dump(data, outfile)
    with open("Template/portfolioTemp.xhtml", "r") as fin:
        with open(FOLDER + "portfolio.html", "w") as fout:
            fout.write(
                fin.read().replace('{{title}}', tradeDateTxt+' 组合月收益%s%% 累计收益%s%%'%(xqPp['monthly_gain'],xqPp['total_gain'])).replace('{{rebalancing}}',latestDf).replace(
                    '{{position}}', holdingDf))
    readText='策略组合月收益为百分之'+str(xqPp['monthly_gain'])+'，累计收益百分之'+str(xqPp['total_gain'])+'，当前持仓股票共'+str(len(holding))+'个，'+'，'.join(' '.join(x['stock_symbol'])+' '+x['stock_name']+'占百分之'+str(x['weight']) for x in xqPp['last']['holdings'])+'。调(tiao2)仓计划为卖出日涨幅最高个股并买入策略排名第一个股：'+'，'.join(' '.join(x['stock_symbol'])+' '+x['stock_name']+'从百分之'+str(x['prev_target_weight'])+'调(tiao2)到百分之'+str(x['target_weight']) for x in xqPp['latest']['rebalancing_histories'])+'，预计开盘时成交。'
    print(readText)
    genVideo('http://127.0.0.1:5500/portfolio.html',readText,'Trade')

def wencai(sentence:str,tradeDate:pd.DataFrame):
    blacklist=['KIM']
    df=crawl_data_from_wencai(sentence)
    df=df.loc[~df['hqCode'].isin(blacklist)]
    print(df.columns)
    df = df[['股票代码', '股票简称','美股@最新价', '美股@成交额', '美股@区间振幅', '美股@最新涨跌幅', 'hqCode']][:50]
    # df['美股@振幅'] = pd.to_numeric(df['美股@振幅'], errors='coerce')
    # df['美股@最新涨跌幅'] = pd.to_numeric(df['美股@最新涨跌幅'], errors='coerce')
    dfNewsLen = []
    noNews = getSinaNews('ZZZZZZZ')
    for symbol in df['hqCode']:
        t.sleep(1)
        nws=getSinaNews(symbol)
        if nws['title'].values.all()==noNews['title'].values.all():
            dfNewsLen.append(0)
            continue
        dfNewsLen.append(len(nws))
    df['NewsLen'] = dfNewsLen
    df = df.loc[df['NewsLen'] > 2]
    dfH5 = df.sort_values('NewsLen', ascending=False)
    dfH5['股票代码'] = dfH5.apply(
        lambda x: '<a href="https://finance.yahoo.com/quote/{hqcode}/news/">{symbol}</a>'.format(hqcode=x['hqCode'],
                                                                                        symbol=x['股票代码']), axis=1)
    dfH5['股票简称'] = dfH5.apply(
        lambda x: '<a href="https://xueqiu.com/S/{hqcode}">{name}</a>'.format(hqcode=x['hqCode'],
                                                                                                 name=x['股票简称']),
        axis=1)
    dfH5['NewsLen'] = dfH5.apply(
        lambda x: '<a href="http://biz.finance.sina.com.cn/usstock/usstock_news.php?pageIndex=1&symbol={hqcode}&type=1">{newsLen}</a>'.format(hqcode=x['hqCode'],
                                                                              newsLen=x['NewsLen']),
        axis=1)
    renderHtml(dfH5,'../CMS/source/Quant/wc_us_%s.html' % tradeDate.day,tradeDate.strftime("%Y-%m-%d"))
    readText='策略思路讲解请查看往期视频，今日策略条件为：'+sentence+'。策略选出三个股票是：'
    if not os.path.isfile('strategy.mp3'):
        text2voice(readText,'strategy')
    if not os.path.isfile('strategy.mp4'):
        with open("Template/strategyTemp.xhtml", "r") as fin:
            with open(FOLDER + "strategy.html", "w") as fout:
                fout.write(
                    fin.read().replace('{{mktInfo}}',  tradeDate.strftime("%Y-%m-%d")).replace(
                        '{{strategy}}', '\n'.join('<p class="notification is-dark">%s</p>'%x for x in sentence.split('，'))))
        genVideo('http://127.0.0.1:5500/strategy.html', readText,'strategy')
    symbols=df['hqCode'].to_list()
    print(symbols)
    symbols.reverse()
    return symbols

def combineFinal(symbols:list,tradeDate:pd.DataFrame):
    for symbol in symbols:
        if os.path.isfile(FOLDER+symbol+'.mp4'):
            continue
        genStockVideo(symbol.upper(),tradeDate)
    videolist=[VideoFileClip(FOLDER+x+'.mp4') for x in symbols]
    videolist.append(VideoFileClip(FOLDER+'Trade.mp4'))
    videolist.insert(0,VideoFileClip(FOLDER + 'strategy.mp4'))
    final_clip = concatenate_videoclips(videolist, method='compose')
    final_clip.write_videofile(FOLDER+tradeDate.strftime('%m%d')+'_'+'_'.join(symbols)+".mp4")

def run(xConfig:dict,symbols=[]):
    tradeDate = latestTradeDate()
    if len(symbols)==0:
        symbols=wencai(xConfig['strategy'],tradeDate)[-3:]
        trade(xConfig,symbols)
        genTradeVideo(tradeDate,xConfig)
    combineFinal(symbols,tradeDate)


if __name__ == '__main__':
    with open('Template/config.json') as fr:
        run(json.loads(fr.read()),sys.argv[1:])