import requests,json,re
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import markdown
import time as t
from datetime import *
import configparser

def xqStockInfo(mkt, code:str, s, h):  # 雪球股票信息
    code=code.upper()
    data = {
        'code': str(code),
        'size': '30',
        # 'key': '47bce5c74f',
        'market': mkt,
    }
    r = s.get("https://xueqiu.com/stock/p/search.json", headers=h, params=data)
    stocks = json.loads(r.text)
    stocks = stocks['stocks']
    stock = None
    if len(stocks) > 0:
        for info in stocks:
            if info['code']==code:
                return info
    return stock

def send_email(subject,content):
    if len(content)==0:
        return
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    mycoded='gb18030'
#     input_file = codecs.open(subject, mode="r", encoding=mycoded,errors='ignore')
#     text = input_file.read()
    html = markdown.markdown(content)
    sender = conf['mail']['sender']#发送的邮箱
    receiver = [conf['mail']['receiver']]  #要接受的邮箱（注:测试中发送其他邮箱会提示错误）
    smtpserver = 'smtp.163.com'
    username = conf['mail']['username'] #你的邮箱账号
    password = conf['mail']['password'] #你的邮箱密码

    msg = MIMEText(html,'html',mycoded) #中文需参数‘utf-8'，单字节字符不需要
    msg['Subject'] = Header(subject, mycoded) #邮件主题
    msg['from'] = sender    #自己的邮件地址

    smtp = smtplib.SMTP()
    try :
        smtp.connect('smtp.163.com') # 链接
        smtp.login(username, password) # 登陆
        smtp.sendmail(sender, receiver, msg.as_string()) #发送
        print('邮件%s发送成功'%(subject))
    except smtplib.SMTPException:
        print('邮件%s发送失败'%(subject))
    smtp.quit() # 结束
    t.sleep(10)

class xueqiuPortfolio():
    def __init__(self,mkt,config):
        self.mkt = mkt
        self.cfg = config
        self.position = dict()
        self.holdnum = 5
        self.session = requests.Session()
        self.session.cookies.update(self.getXueqiuCookie())
        self.p_url = 'https://xueqiu.com/P/'
        self.headers = {
            "Connection": "close",
             "user-agent": "Mozilla",
        }


    def getXueqiuCookie(self):
        conf = configparser.ConfigParser()
        conf.read('config.ini')
        # 获取存储在bmob的雪球cookie
        headersBmob = {
            'X-Bmob-Application-Id': conf['bmob']['X-Bmob-Application-Id'],
            'X-Bmob-REST-API-Key': conf['bmob']['X-Bmob-REST-API-Key'],
            'Connection': 'close'
        }
        bmoburl = 'https://api2.bmob.cn/1/classes/text/'
        sbCookie = json.loads(requests.get(bmoburl + self.cfg['bmob'], headers=headersBmob).text)['text']
        cookie_dict = {}
        for record in sbCookie.split(";"):
            key, value = record.strip().split("=", 1)
            cookie_dict[key] = value
        for item in cookie_dict:
            if 'expiry' in item:
                del item['expiry']
        return cookie_dict

    def trade(self,mkt,mode,position_list=None):  # 调仓雪球组合
        portfolio_code = self.cfg['xueqiu'][mode]
        if position_list is None:
            return
        remain_weight = 100 - sum(i.get('weight') for i in position_list)
        cash = round(remain_weight, 2)
        data = {
            "cash": cash,
            "holdings": str(json.dumps(position_list)),
            "cube_symbol": str(portfolio_code),
            'segment': 'true',
            'comment': ""
        }
        try:
            resp = self.session.post("https://xueqiu.com/cubes/rebalancing/create.json", headers=self.headers, data=data)
        except Exception as e:
            print('调仓失败: %s ' % e)
            send_email('调仓失败', '%s' % e)
        else:
            print(resp.text)
            with open('md/xueqiu' + mkt + datetime.now().strftime('%Y%m%d_%H ：%M') + '.json', 'w', encoding='utf-8') as f:
                json.dump(json.loads(resp.text), f)

    def getPosition(self):
        if len(self.position)>0:
            return self.position
        self.position['cash']=dict()
        self.position['last'] = dict()
        for mode,portfolio_code in self.cfg['xueqiu'].items():
            resp = self.session.get(self.p_url + portfolio_code, headers=self.headers).text
            portfolio_info = json.loads(re.search(r'(?<=SNB.cubeInfo = ).*(?=;\n)', resp).group())
            asset_balance = float(portfolio_info['net_value'])
            position = portfolio_info['view_rebalancing']
            cash = asset_balance * float(position['cash'])  # 可用资金
            market = asset_balance - cash
            p_info = [{
                'asset_balance': asset_balance,
                'current_balance': cash,
                'enable_balance': cash,
                'market_value': market,
                'money_type': u'CNY',
                'pre_interest': 0.25
            }]
            self.position[mode]=position['holdings']
            self.position['cash'][mode]=int(cash)
            self.position['last'][mode]=portfolio_info['last_success_rebalancing']['holdings']
        return self.position

    def newPostition(self,mkt,symbol,wgt):
        stock = xqStockInfo(mkt, symbol, self.session, self.headers)
        return {
            "code": stock['code'],
            "name": stock['name'],
            "enName": stock['enName'],
            "hasexist": stock['hasexist'],
            "flag": stock['flag'],
            "type": stock['type'],
            "current": stock['current'],
            "chg": stock['chg'],
            # "nav": str(stock['nav']),
            "stock_id": stock['stock_id'],
            "ind_id": stock['ind_id'],
            "ind_name": stock['ind_name'],
            "ind_color": stock['ind_color'],
            "textname": stock['name'],
            "segment_name": stock['ind_name'],
            "weight": wgt,  # 在这里自定义买入仓位,范围0.01到1
            "url": "/S/" + stock['code'],
            "proactive": True,
            "price": str(stock['current'])
        }
