# comics-down
download comics from website

## 简介

comics-down是一个下载动漫资源的爬虫框架，目前已实现了部分网站的支持，也可以通过开发新的网站驱动和下载驱动来扩展支持各类网站资源的下载。



## 安装

1、框架库安装

在命令行输入以下命令：

```
pip install comics-down
```



2、安装谷歌浏览器及对应的webdriver，部分网站需要通过浏览器进行资源解析

(1)直接执行安装包安装谷歌浏览器；

(2)下载谷歌浏览器的webdriver后，解压后放本地目录，例如"d:/webdriver/chromedriver.exe"，然后在将在环境变量path中增加相应目录“d:/webdriver/”，确保可直接找到该执行文件。

谷歌浏览器下载地址：https://www.google.cn/intl/zh-CN/chrome/

webdriver下载地址：http://npm.taobao.org/mirrors/chromedriver/

注意：必须下载跟您安装的谷歌浏览器相同版本的webdriver，否则可能执行会出现问题。



4、安装you-get，部分视频网站资源需要该库进行下载**（如果不需要下载视频可以不安装）**

在命令行执行以下命令

```
pip install you-get
```

开源地址：https://github.com/soimort/you-get



5、安装FFmpeg，部分网站的视频需要通过该工具进行合并转换**（如果不需要下载视频可以不安装）**

下载后解压缩到本地目录，例如“d:/ffmpeg/”，然后在将在环境变量path中增加相应目录“d:/ffmpeg/bin”，确保可直接找到对应的执行文件。

下载地址：https://ffmpeg.zeranoe.com/builds/



6、安装rtmpdump，you-get需要通过该工具进行视频流处理**（如果不需要下载视频可以不安装）**

下载后解压缩到本地目录，例如“d:/rtmpdump/”，然后在将在环境变量path中增加相应目录“d:/frtmpdump/”，确保可直接找到对应的执行文件。

下载地址：http://rtmpdump.mplayerhq.hu/download/



## 基础配置(config)

安装后，在命令行执行 “comicsdown” 命令可以启动控制台，在控制台执行命令进行配置：

1、修改语言（Change language）

修改为英文

```
comics-down />setlanguage en
```

修改为中文

```
comics-down />setlanguage zh_ch
```

2、设置默认保存路径

```
comics-down />set_default_save_path d:\test\
```

3、设置网站驱动的搜索路径（需要使用第三方网站驱动时可放入该目录中）

```
comics-down />set_driver_path d:\test\
```

4、设置下载驱动的搜索路径（需要使用第三方下载驱动时可放入该目录中）

```
comics-down />set_down_driver_path d:\test\
```



## 如何使用

### 通过控制台执行

可以在命令行执行 “comicsdown” 命令启动控制台，进入控制台后，输入命令有相应提示信息，更便于使用。

1、查看帮助信息

查看所有支持的命令

```
comics-down />help
```

查看某命令的帮助

```
comics-down />help download
```

2、查看支持的网站

```
comics-down />support
www.edddh.com : EDD动漫-E站(视频, 请传入播放页url)
list.youku.com : YouKu播单(视频)
v.youku.com : YouKu播放页(视频)
www.ccdm13.com : CC漫画网
www.gufengmh.com : 古风漫画网
www.mangabz.com : Mangabz(下载需频繁打开页面处理,效率低)
www.manhuagui.com : 漫画柜 - 无效，未解决文件下载问题
www.177mh.net : 新新漫画
```

3、下载指定资源

(1)单个资源下载：

```
comics-down />download url=https://www.77mh.net/colist_245115.html
```

注意：传入的url地址需要根据对应网站驱动的要求，一般来说都是传入漫画的章节列表页；download的其他执行参数帮助可使用"help download"获取。



(2)批量资源获取

可以建立批量下载清单文件，文件每一行为一个需下载的资源，每行的格式为：url|存储漫画名，其中存储漫画名如果不传则会自动从网页中解析出来，例如：

```
https://www.77mh.net/colist_245115.html|我的漫画1
https://www.77mh.net/colist_245116.html
https://www.77mh.net/colist_245117.html|我的漫画2
```

然后执行下载命令进行批量下载

```
comics-down />download job_file=D:\动漫下载\批量下载.txt
```



注意事项：多线程下载漫画可能会导致您的IP被网站封掉，因此建议不要开太多的并行，通过以下两个参数控制：

job_worker : 多任务并行下载的工作数量(与job_file配套使用), 默认只启动一个线程

job_down_worker : 每个任务开启的文件并行下载工作数量，默认为10



### 操作系统命令行执行

可以直接通过操作系统执行下载命令，参数与控制台一致，例如：

```
d:>comicsdown url=https://www.77mh.net/colist_245115.html job_down_worker=3
```

 

## 如何开发自己的驱动

可以基于框架开发自己所需下载的网站的网站驱动和下载驱动，实现默认驱动不支持的网站的下载，扩展工具所支持的网站清单。

### 框架原理

**网站驱动**：用于解析所需要下载的网页url，获取当前资源的名字（漫画名）、章节列表（卷或话）、每个章节对应的文件清单（漫画图片清单）

**下载驱动**：用于支持不同类型的资源文件下载，例如普通的http下载，特殊的m3u8视频清单下载等，默认已支持的下载驱动包括

- http：http或https的url下载
- ftp：ftp服务器下载
- m3u8：基于m3u8文件的视频下载
- you-get：使用you-get的视频下载
- Mangabz：Mangabz网站通过浏览器形式的下载

**框架处理流程**：

1、启动时搜索网站驱动路径（set_driver_path）和下载驱动路径（set_down_driver_path），装载第三方所提供的驱动文件上的驱动类（可以一个文件上放多个驱动类），以支持相关网站的解析和下载处理；

2、通过download命令下载时，先解析资源url的域名，获取对应域名的网站驱动类，执行类方法解析资源页面的html，获取资源名字；

3、执行网站驱动类的方法从资源页面的html中解析该资源的章节列表清单，并获得每个章节对应的浏览url；

4、针对每个章节执行网站驱动类的方法，获取章节中每个文件的下载url；

5、将解析到的所有地址存入保存路径的down.xml文件中；

6、基于down.xml中的章节信息和文件地址信息，调用对应的下载驱动类进行文件下载，并在down.xml中登记每个文件的下载情况；

7、当down.xml中的文件全部下载成功，下载任务完成。



### 开发网站驱动

网站驱动的脚本文件必须放入set_driver_path指定的路径中，网站驱动类必须继承 "comics_down.lib.driver_fw.BaseDriverFW" 类，并实现类中要求的4个方法（解析html的方法可以参考“comics-down/comics_down/driver”中的默认网站驱动）：

```
class MyWebDriver(BaseDriverFW):
    """
    网站驱动
    """
    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_supports(cls):
        """
        返回该驱动支持的网站清单
        (需继承类实现)

        @return {dict} - 支持的清单:
            key - 网站域名
            value - 网站说明
        """
        return {
            'list.youku.com': 'YouKu播单(视频)'
        }

    @classmethod
    def get_name_by_url(cls, **para_dict):
        """
        根据url获取下载漫画名
        (需继承类实现)

        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            url - 漫画所在目录索引页面的url

        @return {str} - 漫画名
        """
        # 解析获取漫画名
        _html_code = NetTool.get_web_page_code(
            para_dict['url'], timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        # 返回漫画名
        return _soup.find_all('div', attrs={'class': 'pl-title'})[0].string

    @classmethod
    def _get_vol_info(cls, index_url: str, **para_dict):
        """
        获取漫画的卷列表信息
        (需继承类实现)

        @param {str} index_url - 漫画所在目录索引的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @return {list} - 卷信息数组
            [0] - vol_next_url，传入下一页的url，如果没有下一页，传空
            [1] - 卷信息字典(dict), key为卷名，value为浏览该卷漫画的url
            注：应用会根据vol_next_url判断要不要循环获取卷信息
        """
        # 解析并获取卷信息
        _voldict = {}
        for .. in ..:
        	...
        	# 添加卷名和浏览url
        	_voldict[卷名] = url
        return ['', _voldict]

    @classmethod
    def _get_file_info(cls, vol_url: str, last_tran_para: object, **para_dict):
        """
        获取对应卷的下载文件清单

        @param {str} vol_url - 浏览该卷漫画的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @return {list} - 返回文件清单
            [0] - 要传入下一次执行的参数对象（实现类自定义）
            [1] - 下载文件信息字典(dict), key为文件名，value为文件信息数组:
                [文件url, 下载类型]
            注：目前下载类型支持http、ftp
        """
        # 解析并获取卷信息
        _filedict = {}
        for .. in ..:
        	...
        	# 添加文件名和文件信息数组
        	_filedict[文件名] = [下载地址, 下载类型]
        	
        return [None, _filedict]
```

**注意：**

- **\_get_vol_info的返回数组如果第1个值不是''，则会使用这个传递的url继续执行一次\_get_vol_info获取下一个卷的信息，以支持多个卷信息需要从多个url中获取的情况；**
- **\_get_file_info的返回数组的第一个值可以作为下一次执行\_get_file_info的入参last_tran_para，可以利用该机制让一些只需做一次解析的内容只在第一次执行处理，结果传递至下一次执行，提升执行效率；**
- **para_dict参数会将download的所有参数传入，因此也可以在命令中使用自定义参数传入进行控制。**

### 开发下载驱动

正常情况无需开发下载驱动，只有在所需下载的资源需要特殊下载功能支持时，才需要开发自己的驱动。下载驱动的脚本文件必须放入set_down_driver_path指定的路径中，下载驱动类必须继承 "comics_down.lib.down_driver_fw.BaseDownDriverFW" 类，并实现类中要求的4个方法（解析html的方法可以参考“comics-down/comics_down/down_driver”中的默认下载驱动）：

```
class MyDownDriver(BaseDownDriverFW):
    """
    普通http连接的图片下载驱动
    """
    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_supports(cls):
        """
        返回该驱动支持的类型

        @return {str} - 支持的类型字符串，如http
        """
        return 'http'

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        NetTool.download_http_file(
            file_url, filename=save_file, is_resume=(para_dict['use_break_down'] == 'y'),
            headers={'User-agent': 'Mozilla/5.0'},
            connect_timeout=float(para_dict['overtime']),
            retry=int(para_dict['connect_retry']),
            verify=(para_dict['verify'] == 'y'),
            show_rate=(para_dict['show_rate'] == 'y')
        )

```

**注：download如果正常实行完成则代表下载成功，如果需要返回下载失败的信息，请通过抛出异常的方式中断。**



## 遗留问题

这个框架还有一些遗留问题没有解决，由于个人工作原因能投入的时间有限，欢迎大家fork出来解决或开发不同资源网站的网站驱动和下载驱动。

存在的大问题包括：

1、网站驱动没有支持登录模式的案例；

2、http的下载比较初级，存在以下情况：

- 无session传递，有些网站会进行session校验，这样直接通过简单的request方式下载；
- 不支持登录后的下载（与session传递问题类似）；
- 无法控制连接超时
- 所使用的线程池（HiveNetLib提供）估计还有bug，下载函数没有超时hang住后线程得不到释放，无法生成新的下载线程，导致整个下载卡住，需要结束任务重新再处理

