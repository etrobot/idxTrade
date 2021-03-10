import datetime as dt
import os,json


text=[]
mkt={'cn':'A股持仓','hk':'港股持仓','us':'美股持仓'}
for filename in os.listdir('md'):
    if dt.datetime.now().strftime('%Y%m%d') in filename and '.json' in filename:
        with open('md/'+filename) as json_file:
            config = json.load(json_file)
            text.extend([mkt[filename[6:8]],config['comment']])

msg=('\n\n'.join(text)).replace('\n@交易量化派 ','')
print(msg)