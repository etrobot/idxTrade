from yahoo_fin import news
from datetime import datetime
from time import mktime
from iwencai import crawl_data_from_wencai


nws = news.get_yf_rss("nflx")
for n in nws:
    print(datetime.fromtimestamp(mktime(n['published_parsed'])),n['link'])