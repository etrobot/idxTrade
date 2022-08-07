# coding=utf-8
# from idxTrade import *

import sys,configparser,os
import json
import requests
from lxml import etree
import pandas as pd
import akshare as ak

import mplfinance as mpf
import matplotlib as mpl  # 用于设置曲线参数
import matplotlib.pyplot as plt
from cycler import cycler  # 用于定制线条颜色

from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus

import cv2
from tqdm import tqdm
from mutagen.mp3 import MP3
from moviepy.editor import VideoFileClip, AudioFileClip

IMG_FOLDER='Quotation/'

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

    save_file = "error.txt" if has_error else 'result.' + FORMAT
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
    df['dateText'] = html.xpath('//ul[@class="xb_list"]//span[@class="xb_list_r"]/text()')
    df['title'] = html.xpath('//ul[@class="xb_list"]//a/text()')
    df['url'] = html.xpath('//ul[@class="xb_list"]//a/@href')
    df=df[~df['title'].str.contains("美股", na=False)]
    df = df[df['url'].str.contains("2022", na=False)]
    return df

def draw(df:pd.DataFrame, info:str, news:str):
    # 导入数据
    # 导入股票数据
    # 格式化列名，用于之后的绘制
    df.rename(
        columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        },
        inplace=True)
    df = df[-60:]
    # dt = df.loc[df.index.isin(boardDates)].copy().index.to_list()
    '''
    设置marketcolors
    up:设置K线线柱颜色，up意为收盘价大于等于开盘价
    down:与up相反，这样设置与国内K线颜色标准相符
    edge:K线线柱边缘颜色(i代表继承自up和down的颜色)，下同。详见官方文档)
    wick:灯芯(上下影线)颜色
    volume:成交量直方图的颜色
    inherit:是否继承，选填
    '''
    marketcolors = {'candle': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'edge': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'wick': {'up': 'hotpink', 'down': 'aquamarine'},
                    'ohlc': {'up': '#f64769', 'down': 'mediumaquamarine'},
                    'volume': {'up': 'firebrick', 'down': 'seagreen'},
                    'vcdopcod': False,  # Volume Color Depends On Price Change On Day
                    'alpha': 1.0
                    }
    # 设置图形风格
    # gridaxis:设置网格线位置
    # gridstyle:设置网格线线型
    # y_on_right:设置y轴位置是否在右
    # rcpdict = {'font.family': 'Source Han Sans CN'}
    mystyle = mpf.make_mpf_style(
        base_mpf_style='mike',
        # rc=rcpdict,
        gridaxis='both',
        gridstyle='-',
        gridcolor='#393f52',
        y_on_right=True,
        marketcolors=marketcolors,
        figcolor='#20212A',
        facecolor='#20212A',
        edgecolor='#393f52',
    )
    '''
    设置基本参数
    type:绘制图形的类型，有candle, renko, ohlc, line等
    此处选择candle,即K线图
    mav(moving average):均线类型,此处设置7,30,60日线
    volume:布尔类型，设置是否显示成交量，默认False
    title:设置标题
    y_label:设置纵轴主标题
    y_label_lower:设置成交量图一栏的标题
    figratio:设置图形纵横比
    figscale:设置图形尺寸(数值越大图像质量越高)
    '''
    kwargs = dict(
        style=mystyle,
        type='candle',
        volume=True,
        mav=(5, 10, 20),
        title=info,
        # title=info + '60天' + str(
        #     round(df['Close'][-1] / df['Close'][0] * 100 - 100, 2)) + '% 最新' + str(
        #     round(df['percent'][-1] * 100, 2)) + '% 额' + str(round(df['amount'][-1] / 100000000, 2)) + '亿',
        ylabel='OHLCV',
        ylabel_lower='Shares\nTraded Volume',
        savefig=info,
        figratio=(8, 5),
        figscale=1,
        tight_layout=True,
        # vlines=dict(vlines=dt, linewidths=8, alpha=0.2, colors='khaki')
    )

    # 设置均线颜色，配色表可见下图
    # 建议设置较深的颜色且与红色、绿色形成对比
    # 此处设置七条均线的颜色，也可应用默认设置
    mpl.rcParams['axes.prop_cycle'] = cycler(
        color=['dodgerblue', 'deeppink',
               'navy', 'teal', 'maroon', 'darkorange',
               'indigo'])

    # 图形绘制
    # show_Uontrading:是否显示非交易日，默认False
    # savefig:导出图片，填写文件名及后缀
    mpf.plot(df, **kwargs, scale_width_adjustment=dict(volume=0.5, candle=1, lines=0.5),returnfig=True)
    plt.show()

# 合成视频
def get_video(count:int,imageFile:str,videoFile:str):
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
def get_audio(videoFile:str):
    video = VideoFileClip(videoFile)
    videos = video.set_audio(AudioFileClip('result.mp3'))  # 音频文件
    videos.write_videofile('sound.mp4', audio_codec='aac')  # 保存合成视频，注意加上参数audio_codec='aac'，否则音频无声音


# 计算每个音频的时间（秒）
def get_time_count():
    audio = MP3("result.mp3")
    time_count = int(audio.info.length)
    return time_count

def futuComInfo(symbol:str):
    url='https://www.futunn.com/stock/%s-US/company-profile'%symbol
    html=etree.HTML(requests.get(url=url, headers={"user-agent": "Mozilla"}).text.replace(', ','，'))
    info= html.xpath('//div[@class="value"]/text()')
    if len(info)>0 and '。' in info[-1]:
        comInfo=info[-1].split('。')[0]
        if info[1]==comInfo[:len(info[1])]:
            return comInfo
        else:
            return info[1] + comInfo
    return ''


if __name__ == '__main__':
    # preparePlot()
    text = "『超越量化』轧(ga2)空策略今日精选:今日排名第一的股票是，AMC，筛选股票池为，全市场空头持仓比例排名前一百的股票，筛选条件为：回踩五日线大涨,日涨幅为过去二十日最大，五日线低于二十日线，按日涨幅和近一周涨幅的差距从大到小排列。"
    symbol='REV'
    newsDf=getSinaNews(symbol)
    imageFile=IMG_FOLDER+symbol+'.png'
    videoFile=symbol+'.mp4'
    #futu begin
    if os.path.isfile("futuSymbols.csv"):
        futuSymbols=pd.read_csv("futuSymbols.csv")
    else:
        futuSymbols=ak.stock_us_code_table_fu()
        futuSymbols.to_csv("futuSymbols.csv")
    kline = ak.stock_us_hist_fu(symbol=futuSymbols[futuSymbols['股票简称']==symbol].代码)
    kline.rename(columns = {"日期": "date", "今开":"open", "今收":"close", "最高":"high", "最低":"low", "成交量":"volume", "成交额":"amount"},  inplace=True)
    kline.set_index(pd.to_datetime(kline['date'],format="%Y-%m-%d"),inplace=True)
    for col in ["open", "close", "high", "low"]:
        kline[col]=kline[col]/10
    #futu end
    draw(kline,imageFile,'\n'.join(newsDf['title'].to_list()))
    # get_video(get_time_count(),imageFile,videoFile)
    # get_audio(videoFile)
