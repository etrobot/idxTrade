import os
import requests
import time as t
import re,csv
from sign_text_js import sign_text_js
from zhconv import convert
from bs4 import BeautifulSoup

class BaiduTranslateSpider:
    def __init__(self):
        self.url = 'https://fanyi.baidu.com/v2transapi?from=zh&to=en'
        self.index_url = 'https://fanyi.baidu.com/'
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": "PSTM=1605584756; BAIDUID=621509D1EDB1556EC71CC68C1A5E304C:FG=1; BIDUPSID=1AEB19AD6C78D3C7A1EFF1AEF6482602; REALTIME_TRANS_SWITCH=1; FANYI_WORD_SWITCH=1; HISTORY_SWITCH=1; SOUND_SPD_SWITCH=1; SOUND_PREFER_SWITCH=1; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; __yjs_duid=1_cab112ddffaa4af33775ae7d7dfa029c1608807397345; BAIDUID_BFESS=621509D1EDB1556EC71CC68C1A5E304C:FG=1; delPer=0; PSINO=1; H_PS_PSSID=1443_33223_33306_31660_32971_33350_33313_33312_33169_33311_33310_33339_33309_26350_33308_33307_33145_33389_33370; BCLID=8765896679250944447; BDSFRCVID=L9-OJexroG3SwVJrTfwCjurRFtc7jnQTDYLEqQKg3tugmU4VJeC6EG0Ptj35efA-EHtdogKK0gOTH6KF_2uxOjjg8UtVJeC6EG0Ptf8g0M5; H_BDCLCKID_SF=tR3h3RrX26rDHJTg5DTjhPrM2HrJWMT-MTryKKORQnrjqxbSqqo85JDwQRnfKx-fKHnRhlRNtqTjHtJ4bM4b3jkZyxomtfQxtNRJQKDE5p5hKq5S5-OobUPUDMJ9LUkqW2cdot5yBbc8eIna5hjkbfJBQttjQn3hfIkj2CKLtCvHjtOm5tOEhICV-frb-C62aKDs2IIEBhcqJ-ovQTb65pKpKROh-MJBb6rNKtbJJbc_VfbeWfvpKq_UbNbJ-4bLQRnpaJ5nJq5nhMJmM6-hbtKFqto7-P3y523ion3vQpP-OpQ3DRoWXPIqbN7P-p5Z5mAqKl0MLPbtbb0xXj_0-nDSHH-fqT_q3D; BCLID_BFESS=8765896679250944447; BDRCVFR[S4-dAuiWMmn]=I67x6TjHwwYf0; BA_HECTOR=a084852k2k0l00ah2s1fubldu0r; Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1608855621,1608855625,1608858163,1608897985; Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1608899822; ab_sr=1.0.0_ZDYxNDU1MTNjNDBjOTkwOGMwYzc4Zjk0MDc5NmRjOGU1MDU2YTBjNjkyYWU5ZTIwNTg5Yzc2YjMyZDRhNDJiZDA3ZTdlNGNmNjljODNlYjk5MmE2ZGM4OGJhMzk4ODM1; __yjsv5_shitong=1.0_7_36bddc638f8abe26b68d5c474b5aa7d1bf8b_300_1608899822168_43.254.90.134_bed0d9ad; yjs_js_security_passport=52a6024d37461c03b90ffc37c07f84492340e8cd_1608899823_js",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36", }
        self.token=''
        self.gtk=0

    def get_gtk_token(self):
        """获取gtk和token"""
        html = requests.get(url=self.index_url,
                            headers=self.headers).text
        self.gtk = re.findall('window.gtk = "(.*?)"', html, re.S)[0]
        self.token = re.findall("token: '(.*?)'", html, re.S)[0]
        return self.gtk,self.token

    def get_sign(self, word):
        """功能函数:生成sign"""
        # 先获取到gtk和token
        # gtk, token = self.get_gtk_token()
        sign = sign_text_js.hash(word, self.gtk)
        return sign

    def attack_bd(self, word):
        """爬虫逻辑函数"""
        gtk, token = self.get_gtk_token()
        sign = self.get_sign(word)
        data = {
            "from": "en",
            "to": "zh",
            "query": word,
            "transtype": "realtime",
            "simple_means_flag": "3",
            "sign": sign,
            "token": self.token,
            "domain": "common",
        }
        # json():把json格式的字符串转为python数据类型
        html = requests.post(url=self.url,
                             data=data,
                             headers=self.headers).json()
        print(html)
        result = html['trans_result']['data'][0]['dst']
        return result