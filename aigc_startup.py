#coding:utf-8
import pandas as pd
from bs4 import BeautifulSoup
import requests,json
from QuotaUtilities import renderHtml
from video import translate,is_contain_chinese

def cn(keys:list):
    pairs='''productivity,生产力,video-generator,视频生成,search-engine,搜索引擎,seo-assistant,SEO辅助,startup-assistant,创业辅助,copywriting-assistant,文案辅助,logo-generator,LOGO生成,art-generator,艺术生成,storyteller,故事,no-code,无代码,music-generator,音乐生成,education-assistant,教育辅助,image-generator,图像生成,code-assistant,代码辅助,experiments,实验,image-editing,图像编辑,paraphraser,释义,email-assistant,电邮辅助,avatar-generator,头像生成,finance,金融,prompts-assistant,提示辅助,writing-assistant,写作辅助,design-assistant,设计辅助,real-estate,房地产,spreadsheet-assistant,表格辅助,developer-tools,开发工具,research-assistant,研究辅助,3D-generator,3D生成,life-assistant,生活辅助,text-to-speech,文本转语音,sql-assistant,SQL辅助,video-editing,视频编辑,audio-editing,音频编辑,transcriber,转录,social-media-assistant,社交媒体辅助,fun-tools,趣味工具,summarizer,汇总,gift-ideas,礼品创意,legal-assistant,法律辅助,sales-assistant,销售辅助,resources,资源,personalized-videos,个性化视频,human-resources,人力资源,customer-support,客户支持,memory-assistant,记忆辅助,presentations,PPT演示,fashion-assistant,时尚辅助,gaming,游戏,health,健康,Freemium,免费&增值,FreeTrial,免费试用,Paid,付费,ContactforPricing,联系定价,Deals,交易,Free,免费'''
    pairsList=pairs.split(',')
    pairResult=[pairsList[pairsList.index(x.replace(' ',''))+1] for x in keys]
    # pairResult.sort()
    return ','.join(pairResult)

def futureTools():
    cookies = {
        '_ga': 'GA1.1.1619123489.1675652904',
        '_fbp': 'fb.1.1675652905645.2070174151',
        '_ga_0N2M92W58V': 'GS1.1.1675652903.1.1.1675652955.0.0.0',
    }

    headers = {
        'authority': 'www.futuretools.io',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
        # 'cookie': '_ga=GA1.1.1619123489.1675652904; _fbp=fb.1.1675652905645.2070174151; _ga_0N2M92W58V=GS1.1.1675652903.1.1.1675652955.0.0.0',
        'referer': 'https://www.futuretools.io/',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    data=[]
    for pagenum in range(1,8):
        params = {
            'd34f6f6e_page': pagenum,
        }

        response = requests.get('https://www.futuretools.io/', params=params, cookies=cookies, headers=headers)

        soup=BeautifulSoup(response.text)
        divs= soup.findAll(name="div", attrs={"class": "tool-item-columns---new w-rows"})
        for div in divs:
            links=div.findAll(name="a")
            rowss=[links[1].text,links[2]['href'],div.find('div',attrs={"class":'tool-item-description-box---new'}).text,[x.div.text for x in links[3:]]]
            print(rowss)
            data.append(rowss)

    df=pd.DataFrame(data,columns=['名称','url','描述','标签'])
    df.to_csv('html/aigc.csv')
    df['名称'] = df.apply(lambda x: '<a href="{url}">{name}</a>'.format(url=x['url'], name=x['名称']), axis=1)
    renderHtml(df, '../CMS/source/Quant/aigc.html', 'aigc')

def futurepedia():
    cookies = {
        '_ga': 'GA1.1.1297397741.1673584019',
        '_hjSessionUser_3239875': 'eyJpZCI6IjBkYjFiYzc1LTRiMTEtNWUyMS04ZjhkLTAwMmQzNjcyYzg5OSIsImNyZWF0ZWQiOjE2NzM1ODQwMTgzMDIsImV4aXN0aW5nIjp0cnVlfQ==',
        '_hjSession_3239875': 'eyJpZCI6IjdlN2M1MTAxLTYyYzMtNGI5MC04ZTYwLTMyMzJkZmJmMTFiOSIsImNyZWF0ZWQiOjE2NzU2NzY5MjQ4MDgsImluU2FtcGxlIjpmYWxzZX0=',
        '_hjAbsoluteSessionInProgress': '0',
        '_ga_HQ45GJVJVY': 'GS1.1.1675676923.4.1.1675679739.0.0.0',
    }

    headers = {
        'authority': 'kmjaszo0uvp648ygp-1.a1.typesense.net',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja;q=0.5',
        'content-type': 'text/plain',
        'origin': 'https://www.futurepedia.io',
        'referer': 'https://www.futurepedia.io/',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    params = {
        'x-typesense-api-key': 'SRe4Xsci1luFt81plXDH3hIGgwA9rIvq',
    }

    data = '{"searches":[{"infix":"always","facet_by":"","query_by":"toolName","sort_by":"","highlight_full_fields":"toolName","collection":"futurepedia_tool_index_dev_v1","q":"*","page":1}]}'

    response = requests.post('https://kmjaszo0uvp648ygp-1.a1.typesense.net/multi_search', params=params,
                             headers=headers, data=data)

    count=json.loads(response.text)['results'][0]['found']
    end=int((count-count%8)/8+1*(int(count%8>0)))
    print(count,'projects,',end,'pages')
    df=pd.DataFrame()
    for i in range(end-100,end):
        params = {
            'page': i,
            'sort': 'popular',
        }
        response = requests.get('https://www.futurepedia.io/api/tools', params=params, cookies=cookies, headers=headers)
        results=json.loads(response.text)
        # print(results,len(results))
        if len(results)==0:
            break
        rows=[]
        for r in results:
            row=[r['toolName'],cn(r['tagsIndex']),r['toolShortDescription'],cn(r['pricing']),r['websiteUrl']]
            print(row)
            rows.append(row)
        rdf=pd.DataFrame(rows,columns=['网站','标签','简述','收费模式','websiteUrl'])
        df=df.append(rdf)
    df['网站'] = df.apply(lambda x: '<a href="https://{url}">{name}</a>'.format(url=x['websiteUrl'].split('/')[2], name=x['网站']), axis=1)
    df = pd.read_csv('html/aigc.csv').append(df)
    df.drop_duplicates(subset='网站', keep='first', inplace=True)
    df.reset_index(inplace=True)
    df=df[['网站','标签','简述','收费模式']]
    for k,v in df.iterrows():
        if not is_contain_chinese(v['简述']):
            df.at[k, '简述']=translate(v['简述'])
    df.to_csv('html/aigc.csv',index=False)
    renderHtml(df, '../CMS/source/Quant/aigc.html', 'aigc')

if __name__ == '__main__':
    futurepedia()