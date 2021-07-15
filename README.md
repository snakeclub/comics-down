# comics-down
## 简介

comics-down是一个下载动漫资源的爬虫框架，目前已实现了部分网站的支持，也可以通过开发新的网站驱动和下载驱动来扩展支持各类网站资源的下载。



## 安装

### 安装框架库

在命令行输入以下命令：

```
pip install comics-down
```



### 安装webdriver

安装谷歌浏览器及对应的webdriver，部分网站需要通过浏览器进行资源解析

(1)直接执行安装包安装谷歌浏览器，通过菜单“帮助 -> 关于Google Chrome” 查看当前安装谷歌浏览器的版本（例如：版本 91.0.4472.101（正式版本） (arm64)）；

(2)下载对应谷歌浏览器版本的webdriver后（版本、操作系统要对应上，例如我下载的是：91.0.4472.19/chromedriver_mac64_m1.zip），解压后放本地目录，例如"d:/webdriver/chromedriver.exe"，然后在环境变量path中增加相应目录“d:/webdriver/”，确保可直接找到该执行文件。

谷歌浏览器下载地址：https://www.google.cn/intl/zh-CN/chrome/

webdriver下载地址：http://npm.taobao.org/mirrors/chromedriver/

注意：必须下载跟您安装的谷歌浏览器相同版本的webdriver，否则可能执行会出现问题。

（3）解压放到本地，并设置环境变量保证可以直接命令行执行文件：

**windows示例**

解压到“d:/comics-down-tools/webdriver/chromedriver.exe”，然后在系统环境变量path中增加相应目录“d:/comics-down-tools/webdriver/” 。

**mac示例**

解压到"/Users/xxx/comics-down-tools/webdriver/chromedriver"，需要复制到 usr/local/bin目录下并授权：

```
# 复制
sudo cp -r /Users/xxx/comics-down-tools/webdriver/chromedriver /usr/local/bin/
# 授权
sudo chmod 777 /usr/local/bin/chromedriver
```

此外在mac运行中可能会提示：**无法打开“chromedriver”，因为Apple无法检查其是否包含恶意软件**， 采用以下办法放开权限：

```
1、打开“系统偏好设置”应用；
2、点击“安全性与隐私”；
3、选择“通用”页签，这时候能看到“chromedriver”被阻止的信息，点击仍然允许；
```



### 安装视频处理工具

#### 安装FFmpeg

部分网站的视频需要通过该工具进行合并转换**（如果不需要下载视频可以不安装）**

下载地址：http://www.ffmpeg.org/download.html

Windows：可以直接下载编译后的版本解压到本地目录，例如“d:/comics-down-tools/ffmpeg/”，然后在环境变量path中增加相应目录“d:/comics-down-tools/ffmpeg/bin/”

Mac: 可以使用homebrew进行安装，命令行执行：brew install ffmpeg

```
注：可能有些依赖没有安装全，可以带上以下参数命令进行安装
brew install ffmpeg --with-sdl2 --with-fdk-aac --with-fontconfig --with-frei0r --with-game-music-emu --with-libass --with-libbs2b --with-libcaca --with-libgsm --with-libmodplug --with-librsvg --with-libsoxr --with-libssh --with-libvidstab --with-libvorbis --with-libvpx --with-opencore-amr --with-openh264 --with-openjpeg --with-openssl --with-opus --with-rtmpdump --with-rubberband --with-sdl2 --with-snapp --with-speex --with-srt --with-tesseract --with-theora --with-tools --with-two-lame --with-wavpack --with-webp --with-x265 --with-xz --with-zeromq --with-zimg --with-chromaprint --with-libbluray --with-snappy  --with-freetype
```



### 安装下载工具

#### 安装aria2

aria2c 是一个用来下载文件的实用程序。支持HTTP(S), FTP, SFTP, BitTorrent,和Metalink协议。aria2c可以从多个数据源、协议下载文件，并且会尝试最大限度的利用你的带宽资源。

windows：直接下载解压缩后，在环境变量上配置好对应的目录，可以直接执行命令即可；同时也可以参照mac步骤创建配置文件指定使用

Mac: 可以通过brew进行安装，安装命令如下：brew install aria2

安装完成后可以直接使用，也可以通过配置文件设定一些默认值，步骤如下：

1、配置文件放在 ~/.aria2 下，依次输入命令：

```
cd ~
mkdir .aria2
cd .aria2
touch aria2.conf
```

2、用文本编辑器打开 aria2.conf 进行编辑，参考配置如下（RPC模式）：

```
#用户名
#rpc-user=user
#密码
#rpc-passwd=passwd
#上面的认证方式不建议使用,建议使用下面的token方式
#设置加密的密钥
#rpc-secret=token
#允许rpc
enable-rpc=true
#允许所有来源, web界面跨域权限需要
rpc-allow-origin-all=true
#允许外部访问，false的话只监听本地端口
rpc-listen-all=true
#RPC端口, 仅当默认端口被占用时修改
#rpc-listen-port=6800
#最大同时下载数(任务数), 路由建议值: 3
max-concurrent-downloads=5
#断点续传
continue=true
#同服务器连接数
max-connection-per-server=5
#最小文件分片大小, 下载线程数上限取决于能分出多少片, 对于小文件重要
min-split-size=10M
#单文件最大线程数, 路由建议值: 5
split=10
#下载速度限制
max-overall-download-limit=0
#单文件速度限制
max-download-limit=0
#上传速度限制
max-overall-upload-limit=0
#单文件速度限制
max-upload-limit=0
#断开速度过慢的连接
#lowest-speed-limit=0
#验证用，需要1.16.1之后的release版本
#referer=*
#文件保存路径, 默认为当前启动位置，注意xxx要替换为你自己的用户名
dir=/Users/xxx/Downloads
#文件缓存, 使用内置的文件缓存, 如果你不相信Linux内核文件缓存和磁盘内置缓存时使用, 需要1.16及以上版本
#disk-cache=0
#另一种Linux文件缓存方式, 使用前确保您使用的内核支持此选项, 需要1.15及以上版本(?)
#enable-mmap=true
#文件预分配, 能有效降低文件碎片, 提高磁盘性能. 缺点是预分配时间较长
#所需时间 none < falloc ? trunc << prealloc, falloc和trunc需要文件系统和内核支持
file-allocation=prealloc
```

3、如果要使用的时候，命令行可以指定配置：

```
aria2c --conf-path="/Users/xxx/.aria2/aria2.conf" -D
```

#### 安装you-get

安装you-get，部分视频网站资源需要该库进行下载**（如果不需要下载视频可以不安装）**

直接在命令行执行以下命令安装即可

```
pip install you-get
```

开源地址：https://github.com/soimort/you-get

#### 安装rtmpdump

you-get需要通过该工具进行视频流处理**（如果不需要下载视频可以不安装）**

Window：下载后解压缩到本地目录，例如“d:/rtmpdump/”，然后在将在环境变量path中增加相应目录“d:/rtmpdump/”，确保可直接找到对应的执行文件。

下载地址：http://rtmpdump.mplayerhq.hu/download/

Mac：安装FFmpeg会自动装上该工具，如果没有安装，可以手工执行以下命令安装：brew install rtmpdump



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
www.177mh.net : 新新漫画[www.77mh.co, www.77mh.com, www.77mh.de, www.177mh.net]
www.mangabz.com : Mangabz漫画网站[www.mangabz.com]
www.edddh.net : EDD动漫-E站(请传入介绍页而非播放页)[www.edddh.net]
www.youku.com : YouKu视频[v.youku.com, www.youku.com]
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



## 主要功能介绍

 在控制台输入help命令可以查看支持的所有命令：

```
support                 显示支持的网站列表
start_proxy_server      启动指定的代理服务
stop_proxy_server       停止指定的代理服务
download                下载漫画所有资源
get_down_index          创建下载索引文件，可用于后续下载操作
show_down_index         查看下载索引信息
download_file           下载指定文件
analysis_video_urls     解析指定页面的视频地址
download_webpage_video  解析指定页面并下载视频文件
analysis_xpath          解析指定元素的xpath
```

注：有些网站会屏蔽selenium浏览器，可以通过内置的代理进行伪装处理，方法如下：

1、启动代理：start_proxy_server proxy=lib/proxy/selenium_feign_proxy.py proxy=9000

2、在解析任务命令上增加代理服务器的指定。



## 如何开发自己的驱动

可以基于框架开发自己所需下载的网站的网站驱动和下载驱动，实现默认驱动不支持的网站的下载，扩展工具所支持的网站清单。

### 框架原理

**网站驱动**：用于解析所需要下载的网页url，获取当前资源的名字（漫画名）、章节列表（卷或话）、每个章节对应的文件清单（漫画图片清单）

**下载驱动**：用于支持不同类型的资源文件下载，例如普通的http下载，特殊的m3u8视频清单下载等，默认已支持的下载驱动包括

- http：http或https的url下载
- ftp：ftp服务器下载
- m3u8：基于m3u8文件的视频下载
- you-get：使用you-get的视频下载
- aria2: 基于aria2工具的下载（在conf/config.xml配置中设置了http类型默认使用该驱动下载）

**框架处理流程**：

1、启动时搜索网站驱动路径（set_driver_path）和下载驱动路径（set_down_driver_path），装载第三方所提供的驱动文件上的驱动类（可以一个文件上放多个驱动类），以支持相关网站的解析和下载处理；

2、通过download命令下载时，先解析资源url的域名，获取对应域名的网站驱动类，执行类方法解析资源页面的html，获取资源名字；

3、执行网站驱动类的方法从资源页面的html中解析该资源的章节列表清单，并获得每个章节对应的浏览url；

4、针对每个章节执行网站驱动类的方法，获取章节中每个文件的下载url；

5、将解析到的所有地址存入保存路径的down.xml文件中；

6、基于down.xml中的章节信息和文件地址信息，调用对应的下载驱动类进行文件下载，并在down.xml中登记每个文件的下载情况；

7、当down.xml中的文件全部下载成功，下载任务完成。



### 开发网站驱动（代码方式）

网站驱动的脚本文件必须放入set_driver_path指定的路径中，网站驱动类必须继承 "comics_down.lib.core.BaseWebSiteDriverFW" 类，并实现类中要求的4个方法（解析html的方法可以参考“comics-down/comics_down/website_driver”中的默认网站驱动）：

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
            key - 网站主域名, 比如www.youku.com
            value - dict {
                'remark': '网站说明'
                'subsite': ['子域名', '子域名', ...]
            }
        """
        return {
            'www.youku.com': {
                'remark': 'YouKu视频',
                'subsite': ['v.youku.com']
            }
        }

    @classmethod
    def get_name_by_url(cls, **para_dict):
        """
        根据url获取下载漫画名
        (需继承类实现)

        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            url - 漫画所在目录索引页面的url

        @returns {str} - 返回漫画名
        """
        # 获取页面代码
        _html_code = WebDriverTool.get_web_page_code(para_dict)
        _parser = HtmlParser(_html_code)

        # 返回漫画名
        return _parser.find_elements([['xpath', './/head/meta[@name="irAlbumName"]']])[0].get_attribute('content')

    @classmethod
    def _get_vol_info(cls, index_url: str, **para_dict):
        """
        获取漫画的卷列表信息
        (需继承类实现)

        @param {str} index_url - 漫画所在目录索引的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @returns {dict} - 返回 vols_info 卷信息字典
            vol_next_url {str} - 传入下一页的url，如果没有下一页可以不传或传''
                注：应用会根据vol_next_url判断要不要循环获取卷信息
            vols {dict} - 卷信息字典(dict), key为卷名，value卷信息字典
                    url {str} - 为浏览该卷漫画的url
                注：卷名可以通过标签‘{$path_split$}’来设置卷保存的子目录
        """
        # 解析并获取卷信息
        _voldict = {
            'vol_next_url': '',
            'vols': {}
        }
        for .. in ..:
        	...
        	# 添加卷名和浏览url
        	_voldict[vols]['卷名'] = {'url': 'http://...'}
        return _voldict

    @classmethod
    def _get_file_info(cls, vol_url: str, last_tran_para: object, **para_dict):
        """
        获取对应卷的下载文件清单

        @param {str} vol_url - 浏览该卷漫画的url
        @param {object} last_tran_para=None - 传入上一次文件信息获取完成后传递的自定义参数对象
            注：可以利用这个参数传递上一个卷的文件信息获取所形成的公共变量，减少当前卷文件处理所需计算量
            例如假设所有卷的文件信息都来源于同一个页面，可以通过该参数传递浏览器对象，避免下一个卷处理需要再次打开浏览器
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @returns {dict} - 返回 files_info 文件信息字典
            next_tran_para {object} - 要传入下一次执行的参数对象（实现类自定义）
            files {dict} - 下载文件信息字典(dict), key为文件名, value为文件信息字典
                url {str} - 文件下载url地址
                downtype {str} - 指定文件下载类型（具体支持类型需参考装载的下载驱动, 默认将支持http/ftp）
                extend_json {dict} - 要送入下载驱动的扩展信息字典
            ...
        """
        # 解析并获取卷信息
        _filedict = {
            'next_tran_para': None,
            'files': {}
        }
        
        for .. in ..:
        	...
        	# 添加文件名和文件信息数组
        	_filedict['files']['文件名'] = {
        		'url': 'http://...',
        		'downtype': 'http'
        	}
        	
        return _filedict
```

**注意：**

- **\_get_vol_info的返回数组如果第1个值不是''，则会使用这个传递的url继续执行一次\_get_vol_info获取下一个卷的信息，以支持多个卷信息需要从多个url中获取的情况；**
- **\_get_file_info的返回数组的第一个值可以作为下一次执行\_get_file_info的入参last_tran_para，可以利用该机制让一些只需做一次解析的内容只在第一次执行处理，结果传递至下一次执行，提升执行效率；**
- **para_dict参数会将download的所有参数传入，因此也可以在命令中使用自定义参数传入进行控制。**



### 开发网站驱动（配置方式）

框架中提供了一个通用的网站处理驱动，可以通过配置方式解析网站返回对应的信息，开发方式如下：

1、创建在 comics-down/comics_down/conf/common_website_dirver 目录下创建新的网站驱动xml文件；

2、参考默认网站驱动xml的格式和步骤语法配置解析和获取信息的逻辑；

3、重启框架程序将自动加载驱动信息（可能要重新启动两次）。

**注：实际的解析代码参考 comics-down/comics_down/website_driver/common_website_driver.py**



### 开发下载驱动

正常情况无需开发下载驱动，只有在所需下载的资源需要特殊下载功能支持时，才需要开发自己的驱动。下载驱动的脚本文件必须放入set_down_driver_path指定的路径中，下载驱动类必须继承 "comics_down.lib.core.BaseDownDriverFW" 类，并实现类中要求的2个方法（具体方法可以参考“comics-down/comics_down/down_driver”中的默认下载驱动）：

```
class MyDownDriver(BaseDownDriverFW):
    """
    普通http连接的图片下载驱动
    """
    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_down_type(cls):
        """
        返回该驱动对应的下载类型
        (需继承类实现)

        @returns {str} - 下载类型字符串，如http/ftp
            注：系统加载的下载类型名不能重复
        """
        return 'http'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的自定义扩展信息
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

