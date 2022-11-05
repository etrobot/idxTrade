# -*- coding:utf-8 -*-

import random,hashlib
from QuotaUtilities import *
# from xq_backup_lite import *
from video import *
from translate import *

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
    # print(xq_a_token)
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
    # idxtrade = idxTrade('cn', 0)
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
    # updateFund(pdate)
    # debts = ak.bond_cov_comparison()
    # debts.set_index('正股代码', inplace=True)
    # print(debts.columns)
    # thsIndustry('cn',datetime(2021,3,19))
    # updateAllImg('cn',datetime(2021,4,30), ['_J','_U'], xq_a_token)
    # print(xueqiuConcerned('hk',xq_a_token)['symbol'])
    # heldBy('SZ002463',pdate)
    # getCsvK()
    symbol='test'
    s='''
    显示驱动程序是允许操作系统与图形硬件一起工作的软件。图形硬件控制显示器，可以是计算机中的扩充卡，也可以内置在计算机的主电路板中（如笔记本电脑），也可以驻留在计算机外部（如Matrox remote graphics units）。每种型号的图形硬件都是不同的，需要一个显示驱动程序来与系统的其余部分连接。具有不同特性的较新图形硬件型号不断发布，每种新型号的控制方式往往不同。驱动程序将操作系统函数调用（命令）转换为特定于该设备的调用。对于同一型号的图形硬件，使用不同函数调用的每个操作系统也需要不同的显示驱动程序。例如，Windows XP和Linux需要非常不同的显示驱动程序。但是，同一操作系统的不同版本有时可以使用相同的显示驱动程序。例如，Windows 2000和Windows XP的显示驱动程序通常是相同的。如果未安装特定于计算机图形硬件的显示驱动程序，图形硬件将无法使用或功能有限。如果特定于型号的显示驱动程序不可用，操作系统通常可以使用具有基本功能的通用显示驱动程序。例如，Windows在“安全模式”下使用通用VGA或SVGA显示驱动程序。在这种情况下，大多数特定于模型的功能都不可用。由于图形硬件非常复杂，并且显示驱动程序非常特定于该硬件，因此显示驱动程序通常由硬件制造商创建和维护，甚至操作系统中包含的显示驱动程序也通常最初由制造商提供。制造商可以完全访问有关硬件的信息，并在确保以最佳方式使用其硬件方面拥有既得利益。显示驱动程序对系统资源具有低级（内核级）访问权限，因为显示驱动程序需要直接与图形硬件通信，这种低级别访问使得显示驱动程序的编码更加仔细和可靠。显示驱动程序中的错误比应用程序软件中的错误更有可能使整个操作系统暂时无法使用。幸运的是，某些公司或组织（如Matrox）凭借其对专业用户的传统承诺以及其产品的长期产品生命周期，在制造可靠的显示器驱动程序方面享有盛誉。长生命周期意味着其显示器驱动程序的开发将持续更长的时间，使得悬而未决的问题更有可能得到解决，并且显示驱动程序能够适应不断变化的软件环境。新的操作系统和新的应用软件正在不断发布，每一种都可能需要新的驱动程序版本来保持兼容性或提供新的功能，可用的最新显示驱动程序经常解决此类问题。长的产品生命周期也使得显示驱动程序更有可能添加新的特性和功能，而不考虑操作系统和应用程序软件。对于Linux等开源操作系统，非制造商有时会维护显示驱动程序，操作系统的开源特性使得为此类操作系统编写代码变得更容易（但并不容易）。虽然Matrox为特殊目的维护自己的Linux显示驱动程序，但Matrox Millennium G系列产品提供了基本的开源Linux显示驱动程序，Matrox合作伙伴Xi Graphics（一家在Linux/Unix开发方面有10多年经验的公司）为Matrox产品提供了全功能的Linux显示驱动程序。即使对于相同的操作系统和图形硬件型号，有时也会同时提供不同的显示驱动程序，以满足不同的需求。以下是Matrox图形硬件某些型号可用的不同显示驱动程序的摘要：“HF”驱动程序：此类驱动程序具有丰富的界面，需要Microsoft .NET Framework软件，适用于喜欢此界面或者已有此界面的用户，微软NET软件包含在许多最近安装的Windows和许多其他需要它的应用程序中。“HF”软件仅适用于某些型号的Parhelia系列产品和Millennium P系列产品。Microsoft .NET Framework：是由Microsoft创建的一种编程基础架构，用于构建、部署和运行用户使用的应用程序和服务.NET技术，如我们的HF驱动程序。统一驱动程序：此类驱动程序一次支持多个不同型号的Matrox产品。对于需要一次为许多不同的Matrox产品安装显示驱动程序并希望从一个软件包进行安装的系统管理员非常有用，对于不确定自己的图形硬件型号的用户也很有用。由于统一驱动程序的接口必须支持不同的硬件，Matrox统一驱动程序使用支持更广泛的“SE”接口。XDDM：Windows XP显示驱动程序模型，有时被称为XPDM或XPDDM。WDDM：Windows显示驱动程序模型（WDDM）是Windows Vista、Server 2008和Windows 7支持的显示驱动程序体系结构。“WDM”（Windows驱动程序型号）驱动程序包：此类驱动程序适用于需要视频捕获和实时播放功能的用户，有一个需要Microsoft的丰富界面.NET Framework软件和支持视频的额外功能，微软NET软件包含在许多最近安装的Windows和许多其他需要它的应用程序中。仅适用于某些型号的Parhelia系列产品。WHQL驱动程序：“Windows硬件质量实验室”驱动程序接受Microsoft开发的一系列标准测试，以提高驱动程序的可靠性。Matrox等硬件供应商执行这些测试，并将结果提交给Microsoft进行认证。如果用户安装的驱动程序未通过WHQL认证（即使驱动程序通过其他方式认证），则Windows操作系统的最新版本会向用户发出警告。为了避免此类警告和WHQL流程提供的额外测试，系统管理员通常更喜欢使用WHQL驱动程序。认证驱动程序：Matrox通过领先的专业2D/3D软件认证显示驱动程序，包括用于AEC、MCAD、GIS和P&P（工厂和工艺设计）的软件，这种软件通常要求很高，并广泛使用图形硬件加速。Matrox单独认证此类应用程序，以确保额外的可靠性。该测试是对所有Matrox显示器驱动程序进行的常规测试的补充。ISV认证驱动程序：某些“独立软件供应商”对其应用软件有自己的认证流程，与Matrox认证的驱动程序相似，因为特定图形硬件的显示驱动程序会在特定应用程序中进行额外测试。但是，在这种情况下，Matrox将硬件和显示驱动程序提交给ISV，ISV执行测试。与Matrox认证相比，ISV认证的频率较低，涵盖的应用较少。测试版驱动程序：有时，特殊支持或修复程序首先作为“测试版”驱动程序发布。这类驱动已经接受了一些测试，但不一定完成了整个测试周期，测试版驱动程序可供想要测试或预览重要新功能的用户使用。......设备驱动程序是操作系统内核代码的最大贡献者，Linux内核中有超过500万行代码，并且会导致严重的复杂性、bug和开发成本。近年来，出现了一系列旨在提高可靠性和简化驱动开发的研究。然而，除了用于研究的一小部分驱动程序之外，人们对这一庞大的代码体的构成知之甚少。有学者研究Linux驱动程序的源代码，以了解驱动程序的实际用途、当前的研究如何应用于这些驱动程序以及未来的研究机会，大体上，研究着眼于驱动程序代码的三个方面：驱动程序代码功能的特征是什么，驱动程序研究如何适用于所有驱动程序。驱动程序如何与内核、设备和总线交互。是否存在可抽象为库以减少驱动程序大小和复杂性的相似性？从驱动程序交互研究中，发现USB总线提供了一个高效的总线接口，具有重要的标准化代码和粗粒度访问，非常适合隔离执行驱动程序。此外，不同总线和级别的驱动程序的设备交互水平差异很大，这表明隔离成本将因级别而异。设备驱动程序是在操作系统和硬件设备之间提供接口的软件组件，驱动程序配置和管理设备，并将来自内核的请求转换为对硬件的请求。驱动程序依赖于三个接口：驱动程序和内核之间的接口，用于通信请求和访问操作系统服务。驱动器和设备之间的接口，用于执行操作。驱动器和总线之间的接口，用于管理与设备的通信。下图显示了Linux中驱动程序根据其接口的层次结构，从基本驱动程序类型开始，即char、block和net，可确定72个独特的驱动程序类别。大多数（52%）驱动程序代码是字符驱动程序，分布在41个类中。网络驱动程序占驱动程序代码的25%，但只有6个类。例如，视频和GPU驱动程序对驱动程序代码的贡献很大（近9%），这是因为复杂的设备具有每代都会改变的指令集，但这些设备由于其复杂性，在很大程度上被驱动程序研究所忽视。
    '''
    ss = s.encode('raw_unicode_escape')
    sss = ss.decode()
    baiduTTS(sss,'test')