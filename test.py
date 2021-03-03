import random,hashlib
from xq_backup_lite import *
import lxml

def _create_random_tmp(salt_count, seed):
    """
    从seed种子字符池中随机抽取salt_count个字符，返回生成字符串,
    注意抽取属于有放回抽取方法
    :param salt_count: 生成的字符序列的长度
    :param seed: 字符串对象，做为生成序列的种子字符池
    :return: 返回生成字符串
    """
    # TODO random.choice有放回抽取方法, 添加参数支持无放回抽取模式
    sa = [random.choice(seed) for _ in range(salt_count)]
    salt = ''.join(sa)
    return salt

def create_random_with_num(salt_count):
    """
    种子字符池 = "0123456789", 从种子字符池中随机抽取salt_count个字符, 返回生成字符串,
    :param salt_count: 生成的字符序列的长度
    :return: 返回生成字符串
    """
    seed = "0123456789"
    return _create_random_tmp(salt_count, seed)


def create_random_with_alpha(salt_count):
    """
    种子字符池 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    从种子字符池中随机抽取salt_count个字符, 返回生成字符串,
    :param salt_count: 生成的字符序列的长度
    :return: 返回生成字符串
    """
    seed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return _create_random_tmp(salt_count, seed)


def create_random_with_num_low(salt_count):
    """
    种子字符池 = "abcdefghijklmnopqrstuvwxyz0123456789",
    从种子字符池中随机抽取salt_count个字符, 返回生成字符串,
    :param salt_count: 生成的字符序列的长度
    :return: 返回生成字符串
    """
    seed = "abcdefghijklmnopqrstuvwxyz0123456789"
    return _create_random_tmp(salt_count, seed)

def random_from_list(array):
    """从参数array中随机取一个元素"""
    # 在array长度短的情况下，测试比np.random.choice效率要高
    return array[random.randrange(0, len(array))]

def md5_from_binary(binary):
    """对字符串进行md5, 返回md5后32位字符串对象"""
    m = hashlib.md5()
    m.update(binary.encode('utf-8'))
    return m.hexdigest()

def tencentQuotaAbu(mkt,symbol):
    # 预先设置模拟手机请求的device
    K_DEV_MODE_LIST = ["A0001", "OPPOR9", "OPPOR9", "VIVOX5",
                       "VIVOX6", "VIVOX6PLUS", "VIVOX9", "VIVOX9PLUS"]
    # 预先设置模拟手机请求的os version
    K_OS_VERSION_LIST = ["4.3", "4.2.2", "4.4.2", "5.1.1"]
    # 预先设置模拟手机请求的屏幕大小
    K_PHONE_SCREEN = [[1080, 1920]]

    cuid = create_random_with_num_low(40)
    cuid_md5 = md5_from_binary(cuid)
    random_suffix = create_random_with_num(5)
    dev_mod = random_from_list(K_DEV_MODE_LIST)
    os_ver = random_from_list(K_OS_VERSION_LIST)
    screen = random_from_list(K_PHONE_SCREEN)
    if mkt=='us':
        symbol = mkt + symbol + '.' + re.findall(re.compile(r'~%s\.(.*?)~' % symbol.lower(), re.S),
                                             requests.get('http://smartbox.gtimg.cn/s3/?q=%s&t=us' % symbol).text)[0]
    elif mkt=='cn':
        mkt=''

    K_NET_BASE = "http://ifzq.gtimg.cn/appstock/app/%sfqkline/get?p=1&param=%s,day,,,%d," \
                 "qfq&_appName=android&_dev=%s&_devId=%s&_mid=%s&_md5mid=%s&_appver=4.2.2&_ifChId=303&_screenW=%d" \
                 "&_screenH=%d&_osVer=%s&_uin=10000&_wxuin=20000&__random_suffix=%d"% (
                mkt, symbol, 100,K_DEV_MODE_LIST[0], cuid, cuid, cuid_md5, screen[0], screen[1], os_ver, int(random_suffix, 10))

    print(K_NET_BASE)
    data = requests.get(K_NET_BASE, timeout=5).text
    print(data)

if __name__=='__main__':
    # print(list({'abc':'cccc'}).values()[0])
    # xq_a_token = 'xq_a_token=' + requests.get("https://xueqiu.com", headers={"user-agent": "Mozilla"}).cookies['xq_a_token'] + ';'
    # usHot(xq_a_token)
    # print(xueqiuK('.ixic',startDate='2020',cookie=xq_a_token))
    # checkTradingDay()
    # mthk=cmsK('SZ300638')
    # print(mthk['close'][-1],min(mthk['close'][-60:]),mthk.index[-60],round(mthk['close'][-1]/min(mthk['close'][-60:])-1,4))
    # print(eastmoneyK('sz300141',quota_type='yk'))
    # print(pd.read_csv('md/us20201022.txt',index_col=0))
    # NB. Original query string below. It seems impossible to parse and
    # reproduce query strings 100% accurately so the one below is given
    # in case the reproduced version is not "correct".
    # response = requests.get('https://hq.cmschina.com/market/json?funcno=20050&version=1&stock_list=SZ%3A300419&count=10000&type=1&field=1%3A2%3A3%3A4%3A5%3A6%3A7%3A8%3A9%3A10%3A11%3A12%3A13%3A14%3A15%3A16%3A18%3A19&date=20201020&FQType=1', headers=headers)
    #
    # idxtrade = idxTrade('hk', 0)
    # idxtrade.run()
    # df=pd.read_csv('md/cn20201113.txt', dtype=str)
    # print(df.dropna(subset=['_U']).sort_values(by=['_U'], ascending=True).iloc[:10])
    # for symbol in df['symbol'][:10]:
    #     print(symbol)
    # #
    # print(round(1.55))
    # mkt='cn'
    # calKey='_U'
    # pdate=datetime.now().date()
    # qdf = qdf = xueqiuK(symbol='00410', startDate=(pdate - timedelta(days=250)).strftime('%Y%m%d'), cookie=xq_a_token)
    # draw(qdf, '../upknow/5/hk/hk_地产_00410_SOHO中国.png')
    # toBuy = pd.read_csv('md/cn20201117.txt', dtype={'symbol': str})
    # toBuy.dropna(subset=['_U'], inplace=True)
    # toBuy.sort_values(by='_U', ascending=True, inplace=True)
    # k='sh000001'
    # print(k.upper()[:2] in ['SH','SZ'] and k.upper()[2:].isdigit() and len(k)==8)
    # print(getLimit(getK('SH000001', date(2021,1,22)).index[-2])['代码'].tolist())
    # for f in os.listdir('../CMS/source/Fund'):
    #     if '.html' in f:
    #         symbol=f[:-5]
    #         print(symbol)
    #         mkt='cn'
    #         if len(symbol)==5:
    #             mkt='hk'
    #         fundDf = heldBy(symbol, datetime.now().date()-timedelta(days=1),mkt)
    #         if fundDf is not None:
    #             print(fundDf)
    #             renderHtml(fundDf,'../CMS/source/Fund/%s.html'%symbol,symbol)
    #             t.sleep(2)
    # df = ak.fund_em_open_fund_rank()
    # df = df[df['基金简称'].str.contains('港')]
    # print(df['基金简称'].values[0])
    # print(heldBy('00700',datetime(2021,2,19),'hk')['基金简称'])
    # getFundHoldingHK(datetime(2021,2,22))
    # pdate=datetime(2021,2,24)
    # updateFund(pdate)
    # debts = ak.bond_cov_comparison()
    # debts.set_index('正股代码', inplace=True)
    # print(debts.columns)
    thsIndustry('cn',datetime.now().date())



