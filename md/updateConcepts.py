import pandas as pd
import datetime,re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import codecs, markdown

def loadMd(filename,update=False):
    indDf = pd.read_csv('concepts10jqka.csv', encoding='gb18030', dtype=str)
    # indDf.drop(indDf.columns[:1], axis=1,inplace=True)
    # indDf['雪球行业'] = indDf['雪球行业'].str.replace(r"[A-Za-z0-9\!\%\[\]\,\。]", '')
    # indDf.dropna(subset=['雪球代码'],inplace=True)
    # indDf['所属概念'] = indDf['所属概念'].str.replace(r"[A-Za-z0-9\!\%\[\]\。]", '')
    # indDf['要点'] = indDf['要点'].str.replace("要点", '')
    indDf.set_index('雪球代码',inplace=True)
    indDf['BAK']=indDf['要点']
    with open (filename,'r',encoding='GBK') as f:
        line=f.read().split('***')
        print('入选数量：',len(line))
        for l in line:
            #0:'',1:'股票简称',2:'雪球代码',3:'要点',4:'本地图片链接'
            stock=l.split('\n<br>')
            code=stock[2].split(' ')[0]
            hashTag=re.findall(r'<span.*?>(.*?)</span>', l)
            if len(hashTag)>0:
                print(hashTag[0])
            indDf.at[code,'要点']=stock[3]
    if update:
        indDf.to_csv('concepts10jqka.csv',encoding='GBK')
    return

if __name__=='__main__':
    # loadMd('us动量V20200806.md',update=True)
    # loadMd('us动量√20200806.md', update=True)

    indDf = pd.read_csv('concepts10jqkaBAK.csv', encoding='gb18030', dtype=str)
    indDf.set_index('雪球代码', inplace=True)

    indDf2 = pd.read_csv('concepts10jqka.csv', encoding='gb18030', dtype=str)
    indDf2.set_index('雪球代码', inplace=True)

    indDf['要点']=indDf2['要点'].values
    indDf.to_csv('concepts10jqkaBAK2.csv', encoding='gb18030')
