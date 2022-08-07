# coding=utf-8
# from idxTrade import *

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
SPD = 5
# 音调，取值0-15，默认为5中语调
PIT = 3
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


def text2voice(text:str):
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

    save_file = FOLDER+"error.txt" if has_error else FOLDER+'result.' + FORMAT
    with open(save_file, 'wb') as of:
        of.write(result_str)

    if has_error:
        if (IS_PY3):
            result_str = str(result_str, 'utf-8')
        print("tts api  error:" + result_str)

    print("result saved as :" + save_file)


def getSinaNews(symbol:str):
    url='http://biz.finance.sina.com.cn/usstock/usstock_news.php?pageIndex=1&symbol=%s&type=1'%symbol
    print(url)
    resp=requests.get(url=url, headers={"user-agent": "Mozilla"})
    resp.encoding = 'GB18030'
    html = etree.HTML(resp.text)
    df=pd.DataFrame()
    df['title'] = html.xpath('//ul[@class="xb_list"]//a/text()')
    df['url'] = html.xpath('//ul[@class="xb_list"]//a/@href')
    df['dateText'] = html.xpath('//ul[@class="xb_list"]//span[@class="xb_list_r"]/text()')
    df=df[~df['title'].str.contains("美股", na=False)]
    df = df[df['url'].str.contains("2022", na=False)]
    return df[['title','dateText']]

# 合成视频
def get_video(count:int,imageFile:str,videoFile:str):
    fps = 1      # 帧率
    img_size = (1920, 1080)      # 图片尺寸
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    videoWriter = cv2.VideoWriter(videoFile, fourcc, fps, img_size)
    for i in tqdm(range(0, count+1)):
        frame = cv2.imread(imageFile)
        frame = cv2.resize(frame, img_size)  # 生成视频   图片尺寸和设定尺寸相同
        videoWriter.write(frame)  # 将图片写进视频里
    videoWriter.release()  # 释放资源


# 加入音频
def get_audio(videoFile:str,symbol:str):
    video = VideoFileClip(videoFile)
    videos = video.set_audio(AudioFileClip(FOLDER+'result.mp3'))  # 音频文件
    videos.write_videofile(FOLDER+symbol+'.mp4', audio_codec='aac')  # 保存合成视频，注意加上参数audio_codec='aac'，否则音频无声音


# 计算每个音频的时间（秒）
def get_time_count():
    audio = MP3(FOLDER+"result.mp3")
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

def genEchartJson(qdf:pd.DataFrame):
    qdf['date']=qdf.index.strftime('%m-%d').tolist()
    transdf = qdf[['date', 'open', 'close', 'low', 'high', 'volume']].copy()
    transdf.T
    with open(FOLDER+'videoQuote.json', 'w', encoding='utf-8') as f:
        json.dump(transdf.values.tolist(), f)

async def browserShot(url,filename):
    width, height = 1366, 768
    browser = await launch(headless=True, args=['--disable-infobars', f'--window-size={width}, {height}'])
    page = await browser.newPage()
    await page.setViewport({
        'width': width, 'height': height})
    await page.goto(url)
    await page.screenshot({'path': filename, 'fullPage': False})
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
    print([companyInfo, '最新一条新闻是', newsDf.iloc[0]['title'], '来源是', newsDf.iloc[0]['dateText']])
    readText = '，'.join([companyInfo, '最新一条新闻是', newsDf.iloc[0]['title'], '来源是', newsDf.iloc[0]['dateText']])
    newsTable = newsDf[:7].to_html(index=False).replace('<table', '<table class="table"')
    with open(FOLDER + "quoteTemp.xhtml", "r") as fin:
        with open(FOLDER + "quote.html", "w") as fout:
            fout.write(
                fin.read().replace('{{title}}', symbol + ' ' + tradeDateTxt).replace('{{news}}', newsTable).replace(
                    '{{companyInfo}}', companyInfo))
    # futu begin
    if os.path.isfile("futuSymbols.csv"):
        futuSymbols = pd.read_csv("futuSymbols.csv")
    else:
        futuSymbols = ak.stock_us_code_table_fu()
        futuSymbols.to_csv("futuSymbols.csv")
    kline = ak.stock_us_hist_fu(symbol=futuSymbols[futuSymbols['股票简称'] == symbol].代码)
    kline.rename(columns={"日期": "date", "今开": "open", "今收": "close", "最高": "high", "最低": "low", "成交量": "volume",
                          "成交额": "amount"}, inplace=True)
    kline.set_index(pd.to_datetime(kline['date'], format="%Y-%m-%d"), inplace=True)
    for col in ["open", "close", "high", "low"]:
        kline[col] = kline[col] / 10
    # futu end
    genEchartJson(kline)
    genVideo('http://127.0.0.1:5500/quote.html',readText)

def genVideo(targetUrl:str,readText:str,symbol='symbol'):
    imageFile = FOLDER + 'videoQuote.png'
    videoFile = FOLDER + 'video.mp4'
    asyncio.get_event_loop().run_until_complete(browserShot(targetUrl, imageFile))
    text2voice(readText)
    get_video(get_time_count(), imageFile, videoFile)
    get_audio(videoFile,symbol)

def trade(xueqiuCfg:dict,symbols=()):
    if symbols is None:
        return
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xqPp = xueqiuP.getPosition()['idx']
    cash = xqPp['cash']
    position = xqPp['holding']
    kurl = 'https://xueqiu.com/service/v5/stock/batch/quote?symbol=' + ','.join(x['stock_symbol'] for x in xqPp['holding'])
    quotes = json.loads(requests.get(url=kurl, headers={"user-agent": "Mozilla"}).text)['data']['items']
    if len(position) >= MAXHOLDING:
        sortedHoldings = sorted(
            [[x['quote']['symbol'], x['quote']['symbol'] not in symbols[:10], float(x['quote']['percent'])]
             for x
             in quotes],
            key=lambda x: (x[1], x[2]))
        for p in position:
            if p['stock_symbol'] == sortedHoldings[-1][0]:
                cash = max(cash, int(p['weight']))
                p['weight'] = 0
                p["proactive"] = True
                break
    position.append(xueqiuP.newPostition('cn', symbols[0], min(100/MAXHOLDING, cash)))
    xueqiuP.trade('us', 'idx', position)
    return xqPp['holding']


def genTradeVideo(tradeDate:datetime,xueqiuCfg:dict):
    prev=trade(xueqiuCfg,crawl_data_from_wencai(''))
    tradeDateTxt = tradeDate.strftime('%Y/%m/%d')
    xueqiuP = xueqiuPortfolio('cn', xueqiuCfg)
    xqPp= xueqiuP.getPosition()['idx']
    last=pd.DataFrame(xqPp['last']['rebalancing_histories'])[['stock_symbol','stock_name','prev_target_weight','target_weight']]
    lastDf=last.rename(columns={'stock_symbol':'股票代码','stock_name':'企业名称','prev_target_weight':'调仓前','target_weight':'目标仓位'}).to_html(index=False).replace('<table','<table class="table"')
    holding=pd.DataFrame(prev)[['stock_symbol','stock_name','weight']]
    holdingDf=holding.rename(columns={'stock_symbol':'股票代码','stock_name':'企业名称','weight':'持仓百分比'}).to_html(index=False).replace('<table','<table class="table"')
    data=xueqiuP.getCube()
    with open(FOLDER+'cube.json', 'w') as outfile:
        json.dump(data, outfile)
    with open(FOLDER + "portfolioTemp.xhtml", "r") as fin:
        with open(FOLDER + "portfolio.html", "w") as fout:
            fout.write(
                fin.read().replace('{{title}}', tradeDateTxt+' 组合月收益%s%% 累计收益%s%%'%(xqPp['monthly_gain'],xqPp['total_gain'])).replace('{{rebalancing}}',lastDf).replace(
                    '{{position}}', holdingDf))
    readText='本组合月收益为百分之'+str(xqPp['monthly_gain'])+'，累计收益百分之'+str(xqPp['total_gain'])+'，当前持仓股票共'+str(len(holding))+'个，'+'，'.join(' '.join(x['stock_symbol'])+' '+x['stock_name']+'占百分之'+str(x['weight']) for x in xqPp['holding'])+'。调(tiao2)仓计划为：'+'，'.join(' '.join(x['stock_symbol'])+' '+x['stock_name']+'从百分之'+str(x['prev_target_weight'])+'调(tiao2)到百分之'+str(x['target_weight']) for x in xqPp['last']['rebalancing_histories'])
    print(readText)
    text2voice(readText)
    genVideo('http://127.0.0.1:5500/portfolio.html',readText,'Trade')

def wencai(sentence:str):
    df=crawl_data_from_wencai(sentence)
    df = df[['股票代码', '股票简称', '美股@成交额', '美股@振幅', '美股@最新价', '美股@最新涨跌幅', 'hqCode']]
    df['美股@振幅'] = pd.to_numeric(df['美股@振幅'], errors='coerce')
    df['美股@最新涨跌幅'] = pd.to_numeric(df['美股@最新涨跌幅'], errors='coerce')
    df['股票代码'] = df.apply(
        lambda x: '<a href="https://finance.yahoo.com/quote/{hqcode}/news/">{symbol}</a>'.format(hqcode=x['hqCode'],
                                                                                        symbol=x['股票代码']), axis=1)
    df['股票简称'] = df.apply(
        lambda x: '<a href="https://xueqiu.com/S/{hqcode}">{name}</a>'.format(hqcode=x['hqCode'],
                                                                                                 name=x['股票简称']),
        axis=1)
    df['NewsLen'] = df.apply(
        lambda x: '<a href="https://feeds.finance.yahoo.com/rss/2.0/headline?s={hqcode}">{newsLen}</a>'.format(hqcode=x['hqCode'],
                                                                              newsLen=x['NewsLen']),
        axis=1)
    renderHtml(df,'../CMS/source/Quant/wc_us_%s.html' % tradeDate.day,tradeDate.strftime("%Y-%m-%d"))
    return df['股票代码'].to_list()

if __name__ == '__main__':
    # text = "『超越量化』轧(ga2)空策略今日精选:今日排名第一的股票是，AMC，筛选股票池为，全市场空头持仓比例排名前一百的股票，筛选条件为：回踩五日线大涨,日涨幅为过去二十日最大，五日线低于二十日线，按日涨幅和近一周涨幅的差距从大到小排列。"
    tradeDate = latestTradeDate()
    symbols=wencai('美股市场，名字不含ETF，交易市场不是NYSE Arca，成交额>1000万，向上跳空缺口，涨幅>2%,振幅>2%，最新涨跌幅/月涨跌幅正序')['股票代码']
    for symbol in symbols:
        genStockVideo(symbol.upper(),tradeDate)
    xueqiuConfig={'vika': 'xueqiu2',"xueqiu":{'idx':'ZH2334621'}}
    genTradeVideo(tradeDate,xueqiuConfig)
    videolist=[VideoFileClip(FOLDER+x+'.mp4') for x in symbols]
    videolist.append(VideoFileClip(FOLDER+'Trade.mp4'))
    # Merge video
    final_clip = concatenate_videoclips(videolist)
    # Save Merged video file
    final_clip.write_videofile("Front_inside_final.mp4")

