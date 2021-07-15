#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
webdriver工具
@module webdriver_tool
@file webdriver_tool.py
"""

import os
import sys
import json
import time
import datetime
import urllib.request
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.simple_webdriver import SimpleWebDriver
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import Tools


__MOUDLE__ = 'webdriver_tool'  # 模块名
__DESCRIPT__ = u'webdriver工具'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2021.06.15'  # 发布日期


class WebDriverTool(object):
    """
    webdriver工具类
    """

    #############################
    # 静态工具函数
    #############################
    @classmethod
    def get_common_options(cls, para_dict: dict, roll_to_end: bool = False, until: str = '',
                           session_id: str = None, executor_url: str = None) -> dict:
        """
        根据参数获取webdriver的执行参数配置

        @param {dict} para_dict - 任务扩展参数
            url - 页面的url
            wd_no_image - 禁止图片和CSS下载
            website_proxy - 访问网站的代理
            wd_headless -
            wd_wait_all_loaded -
            wd_min -
        @param {bool} roll_to_end=False - 是否滚动到页面结尾(加载更多的情况), 必须跟until_menthod结合判断
        @param {str} until='' - 如果不等待所有页面加载完，通过xpath判断元素是否存在
            例如: '//img[@id="dracga" and @style]' - 查找id为dracga且包含style属性的img对象
        @param session_id {str} - 上一次调用的浏览器session id (browser.session_id)，需要在同一个浏览器打开下一个页面时使用
        @param executor_url {str} - 上一次调用的执行url (browser.command_executor._url)，需要在同一个浏览器打开下一个页面时使用

        @returns {dict} - webdriver执行参数选项
        """
        _common_options = {
            'timeout': float(para_dict['wd_overtime']),
            'headless': (para_dict['wd_headless'] == 'y'),
            'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
            'roll_to_end': roll_to_end,
            'size_type': ('min' if para_dict['wd_min'] == 'y' else ''),
            'feign_browser': True,
            'disable_security': True
        }

        if until != '':
            _common_options['until_menthod'] = EC.presence_of_element_located((By.XPATH, until))

        if session_id is not None:
            _common_options['session_id'] = session_id
        if executor_url is not None:
            _common_options['executor_url'] = executor_url

        # webdriver模式禁止图片和CSS下载的参数
        if para_dict.get('wd_no_image', 'n') == 'y':
            _common_options['no_image'] = True
            _common_options['no_css'] = True

        # 设置默认下载路径（附带不弹提示框）
        if para_dict.get('wd_default_down_path', '') != '':
            _common_options['default_download_path'] = para_dict['wd_default_down_path']

        # 代理
        if para_dict.get('website_proxy', '') != '':
            _proxy = Tools.get_proxy(para_dict['website_proxy'])
            _scheme = list(_proxy.keys())[0]
            _common_options['proxy'] = _proxy[_scheme]

        return _common_options

    @classmethod
    def get_web_page_code(cls, para_dict: dict, headers: dict = None) -> str:
        """
        获取网页代码(静态代码)

        @param {dict} para_dict - 任务扩展参数
            url - 页面的url
            overtime - 超时时间
            encoding - 网页编码
            connect_retry - 自动重连次数
        @param {dict} headers - 指定网站访问的协议头字典，例如：
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
            }

        @returns {str} - 网页的静态代码
        """
        # 访问代理
        _proxy = None
        if para_dict.get('website_proxy', '') != '':
            _proxy = Tools.get_proxy(para_dict['website_proxy'])

        # 设置访问对象
        _url = para_dict['url']
        if headers is not None:
            _url = urllib.request.Request(para_dict['url'], headers=headers)

        _html = NetTool.get_web_page_code(
            _url, timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry']),
            proxy=_proxy
        )
        if para_dict.get('debug_path', '') != '':
            # 记录网页的信息
            _filename = '%s.html' % datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            Tools.save_file(
                os.path.join(para_dict['debug_path'], _filename),
                'URL: %s\n%s' % (_url, _html)
            )

        return _html

    @classmethod
    def get_web_page_dom(cls, para_dict: dict, roll_to_end: bool = False, until: str = '') -> str:
        """
        获取页面加载后的动态html

        @param {dict} para_dict - 任务扩展参数
            url - 页面的url
            wd_no_image - 禁止图片和CSS下载
            website_proxy - 访问网站的代理
            wd_headless -
            wd_wait_all_loaded -
            wd_min -
        @param {bool} roll_to_end=False - 是否滚动到页面结尾(加载更多的情况), 必须跟until_menthod结合判断
        @param {str} until='' - 如果不等待所有页面加载完，通过xpath判断元素是否存在
            例如: '//img[@id="dracga" and @style]' - 查找id为dracga且包含style属性的img对象

        @returns {str} - 页面加载后的动态html
        """
        # 浏览器参数
        _common_options = cls.get_common_options(para_dict, roll_to_end=roll_to_end, until=until)

        # cookie
        _cookie = None
        if para_dict.get('website_cookie', '') != '':
            _cookie = Tools.get_cookie_from_file(para_dict['website_cookie'])

        _html = SimpleWebDriver.get_web_page_dom(
            para_dict['url'], common_options=_common_options,
            webdriver_type=Tools.get_webdriver_type(para_dict['webdriver']), cookie=_cookie
        )

        if para_dict.get('debug_path', '') != '':
            # 记录网页的信息
            _filename = '%s.html' % datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            Tools.save_file(
                os.path.join(para_dict['debug_path'], _filename),
                'URL: %s\n%s' % (para_dict['url'], _html)
            )

        return _html

    #############################
    # 如果要支持多次交互的动态html获取，需要实例化对象
    #############################
    def __init__(self, para_dict: dict, roll_to_end: bool = False, until: str = '',
                 session_id: str = None, executor_url: str = None) -> None:
        """
        初始化webdriver工具对象，并打开默认页面，可支持多次交互

        @param {dict} para_dict - 任务扩展参数
            url - 页面的url
            wd_no_image - 禁止图片和CSS下载
            website_proxy - 访问网站的代理
            wd_headless -
            wd_wait_all_loaded -
            wd_min -
        @param {bool} roll_to_end=False - 是否滚动到页面结尾(加载更多的情况), 必须跟until_menthod结合判断
        @param {str} until='' - 如果不等待所有页面加载完，通过xpath判断元素是否存在
            例如: '//img[@id="dracga" and @style]' - 查找id为dracga且包含style属性的img对象
        @param session_id {str} - 上一次调用的浏览器session id (browser.session_id)，需要在同一个浏览器打开下一个页面时使用
        @param executor_url {str} - 上一次调用的执行url (browser.command_executor._url)，需要在同一个浏览器打开下一个页面时使用
        """
        # 处理参数
        self.para_dict = para_dict
        self.common_options = self.get_common_options(
            para_dict, roll_to_end=roll_to_end, until=until, executor_url=executor_url,
            session_id=session_id
        )

        # cookie
        _cookie = None
        if para_dict.get('website_cookie', '') != '':
            _cookie = Tools.get_cookie_from_file(para_dict['website_cookie'])

        # 创建浏览器对象
        self.simple_driver = SimpleWebDriver(
            self.para_dict['url'], common_options=self.common_options,
            webdriver_type=Tools.get_webdriver_type(para_dict['webdriver']),
            cookie=_cookie
        )

    def __del__(self):
        """
        析构函数
        """
        del self.simple_driver

    #############################
    # 处理工具
    #############################
    def get_current_dom(self) -> str:
        """
        获取当前动态html页面

        @returns {str} - 动态html页面
        """
        return self.simple_driver.get_current_dom()

    def get_url_dom(self, url: str, roll_to_end: bool = False, until: str = '',
                    cookie: dict = None) -> str:
        """
        在当前窗口打开新url并获取动态html

        @param {str} url - 要打开的新url
        @param {bool} roll_to_end=False - 是否滚动到页面结尾(加载更多的情况), 必须跟until_menthod结合判断
        @param {str} until='' - 如果不等待所有页面加载完，通过xpath判断元素是否存在
            例如: '//img[@id="dracga" and @style]' - 查找id为dracga且包含style属性的img对象
        @param {dict} cookie=None - 要设置的cookie字典


        @returns {str} - 页面加载后的动态html
        """
        # 更新参数
        _common_options = {
            'wait_all_loaded': (self.para_dict['wd_wait_all_loaded'] == 'y'),
            'roll_to_end': roll_to_end
        }

        if until == '':
            _common_options['until_menthod'] = None
        else:
            _common_options['until_menthod'] = EC.presence_of_element_located((By.XPATH, until))

        _html = self.simple_driver.get_url_dom(
            url, common_options=_common_options, cookie=cookie
        )

        return _html

    def get_cookies(self) -> dict:
        """
        获取当前页面的cookie字典

        @returns {dict} - cookie字典
        """
        return self.simple_driver.get_cookies()

    def save_cokies_to_file(self, file: str, encoding: str = 'utf-8'):
        """
        保存当前浏览器的cookie到指定文件

        @param {str} file - 要保存到的文件
        @param {str} encoding='utf-8' - 编码
        """
        with open(file, 'w', encoding=encoding) as _f:
            _f.write(json.dumps(
                self.simple_driver.get_cookies(), ensure_ascii=False
            ))

    #############################
    # 下载处理
    #############################
    def set_download_path(self, path: str):
        """
        动态设置下载路径

        @param {str} path - 要设置的下载路径
        """
        _path = path.rstrip(os.sep)
        self.simple_driver.driver.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
        _params = {'cmd': 'Page.setDownloadBehavior',
                   'params': {'behavior': 'allow', 'downloadPath': _path}}
        self.simple_driver.driver.execute("send_command", _params)
        FileTool.create_dir(_path, exist_ok=True)

    def download(self, links: dict, path: str, wait_finish: bool = False, overtime: float = 180.0):
        """
        下载当前页面的文件

        @param {dict} links - 要下载的链接配置，key为保存的文件名，value为文件链接(注意如果不是当前网站的文件，需要完整链接)
        @param {str} path - 保存的文件路径
        @param {bool} wait_finish=False - 是否等待下载完成
        @param {float} overtime=180.0 - 等待下载完成的超时时间，单位为秒

        @param {dict} - 如果不等待下载结束，返回None；如果等待下载结束，返回处理结果字典（包括超时未成功的情况）
            {
                'status': 'downloading',  # 整体状态, done-已完成
                'files': 0,  # 总文件数
                'success': 0,  # 下载成功数
                'details': {
                    'file_name1': 'downloading',  # 文件下载状态，如果文件已存在代表成功
                    ...
                }
            }
        """
        # 思路是在网站上自己通过js添加链接执行下载
        _div_js = '''if(document.getElementById("__WebDriverTool_Download_DIV__")){
            // 存在，清空对象
            document.getElementById("__WebDriverTool_Download_DIV__").innerHTML = "";
        }else{
            // 新建对象
            var down_div = document.createElement("div");
            down_div.setAttribute("id","__WebDriverTool_Download_DIV__");
            down_div.style.position="absolute";
            down_div.style.left="0px";
            down_div.style.top="0px";
            down_div.style.zIndex=99999;
            document.body.appendChild(down_div);
        };
        '''
        _del_div_js = '''var down_div = document.getElementById("__WebDriverTool_Download_DIV__");
        down_div.parentElement.removeChild(down_div);
        '''
        _add_down_link_js = '''var down_div = document.getElementById("__WebDriverTool_Download_DIV__");
        function create_downlink(url,name){
            var a=document.createElement("a");
            a.href=url;
            a.innerHTML=name;
            a.setAttribute("target","_blank");
            a.setAttribute("download", name);
            down_div.appendChild(a);
        };
        '''
        # 遍历下载链接
        for _filename, _url in links.items():
            _add_down_link_js = '%screate_downlink("%s","%s");' % (
                _add_down_link_js, _url, _filename
            )
        # 动态改变下载路径
        self.set_download_path(os.path.realpath(path))

        # 添加下载链接
        self.simple_driver.driver.execute_script(_div_js)
        self.simple_driver.driver.execute_script(_add_down_link_js)

        # 执行下载点击动作
        self.do_script([
            ['find', 'id', '__WebDriverTool_Download_DIV__'],  # 获取下载div
            ['find_child', 'children'],  # 获取所有子元素对象
            ['click']  # 逐个执行点击操作
        ])

        # 处理完成以后删除链接
        self.simple_driver.driver.execute_script(_del_div_js)

        if wait_finish:
            # 通过监控文件是否存在判断是否已完成
            _start_time = datetime.datetime.now()
            while True:
                _down_info = self.check_download_status(links, path)
                if _down_info['status'] == 'done':
                    return _down_info

                # 检查是否超时
                _end_time = datetime.datetime.now()
                _use = (_end_time - _start_time).total_seconds()
                if _use < overtime:
                    # 没有超时，继续处理
                    continue
                else:
                    return _down_info

    def check_download_status(self, links: dict, path: str) -> dict:
        """
        检查下载状态
        注：同步会对命名不对的文件重命名

        @param {dict} links - 要下载的链接配置，key为保存的文件名，value为文件链接(注意如果不是当前网站的文件，需要完整链接)
        @param {str} path - 保存的文件路径

        @returns {dict} - 下载状态信息字典
            {
                'status': 'downloading',  # 整体状态, done-已完成
                'files': 0,  # 总文件数
                'success': 0,  # 下载成功数
                'details': {
                    'file_name1': 'downloading',  # 文件下载状态，如果文件已存在代表成功
                    ...
                }
            }
        """
        _down_info = {
            'status': 'downloading',  # 整体状态, done-已完成
            'files': 0,  # 总文件数
            'success': 0,  # 下载成功数
            'details': {}
        }

        # 逐个文件进行检查
        _path = os.path.realpath(path)
        for _file, _url in links.items():
            _down_info['files'] += 1
            if os.path.exists(os.path.join(_path, _file)):
                # 文件存在
                _down_info['success'] += 1
                _down_info['details'][_file] = 'done'
            else:
                # 检查是不是因为默认文件名的原因
                _url_name = os.path.split(_url)[1]
                if os.path.exists(os.path.join(_path, _url_name)):
                    # 需改名
                    os.rename(
                        os.path.join(_path, _url_name),
                        os.path.join(_path, _file)
                    )
                    _down_info['success'] += 1
                    _down_info['details'][_file] = 'done'
                else:
                    # 文件不存在
                    _down_info['details'][_file] = 'downloading'

        # 确认是否全部完成
        if _down_info['success'] == _down_info['files']:
            _down_info['status'] = 'done'

        return _down_info

    #############################
    # iframe操作处理
    #############################

    def switch_to_frame(self, iframe: WebElement):
        """
        将浏览器当前上下文跳转到iframe元素上
        注：如果不进行跳转，外层元素无法直接访问iframe元素的内容

        @param {WebElement} iframe - 要跳转到的iframe元素对象
        """
        self.simple_driver.switch_to_frame(iframe)

    def switch_to_parent_frame(self):
        """
        将浏览器当前上下文跳转到当前iframe的上级
        """
        self.simple_driver.switch_to_parent_frame()

    def switch_to_default_frame(self):
        """
        将浏览器当前上下文跳转到最外层的页面
        """
        self.simple_driver.switch_to_default_frame()

    #############################
    # 查找元素
    #############################
    def find_elements(self, steps: list, parent: WebElement = None) -> list:
        """
        按步骤逐级查询对象

        @param {list} steps - 要查询的步骤列表，每一个步骤为一个操作列表，第0个为操作类型，后面为操作参数
            [
                ['pos': 0],  # 获取当前清单中指定位置的元素
                ['children'],  # 获取当前清单元素中的所有子元素
                ['id', 'myId'],  # 通过id获取元素
                ['xpath', '//img[@id="dracga" and @style]'],  # 通过xpaht获取元素
                ['name', 'myName'],  # 通过元素的name属性获取
                ['tag_name', 'img'],  # 通过元素的标签名获取
                ['class_name', 'styleClass'],  # 通过元素的class名获取
                ['css_selector', '#kw'],  # 通过css选择器方式获取，id用#kw, class用.s_ipt, 与css的简写方式相同
                ['link_text', 'hao123'],  # 通过超文本链接上的文字信息来定位元素
                ['partial_link_text', 'hao']  # 通过超文本连接上的文字的一部分关键字信息来定位元素
            ]
        @param {WebElement} parent=None - 开始的父节点，如果不传代表重新开始

        @returns {list} - 返回查找到的对象列表
            注：对象类型为selenium.webdriver.remote.webelement.WebElement
        """
        return self.simple_driver.find_elements(steps, parent=parent)

    #############################
    # 执行元素操作
    #############################

    def do_script(self, steps: list, parent: WebElement = None) -> list:
        """
        按步骤对元素执行操作

        @param {list} steps - 要执行步骤数组
            [
                ['save_els', 'var_name'],  # 将当前元素存入指定名称的临时变量
                ['set_els', 'var_name'],  # 将临时变量的元素恢复到当前元素清单
                ['wait', '0.1'],  # 等待指定的秒数
                ['open_window', 'chrome://downloads/'],  # 打开新标签页，参数为要打开的页面url
                ['close_window', 'int/str'],  # 关闭指定页签，如果不传值代表关闭当前页签
                    # 如果第一个参数为int类型，代表关闭指定位置的页签
                    # 如果第一个参数为str类型，代表关闭title为送入参数的页签
                ['switch_to', 'frame/parent_frame/default/alert/window', ...],  # 切换浏览器页面
                    # frame-切换到当前元素清单第1个的frame中，parent_frame-切换到父页面，default-切换到最外层页面
                    # alert-切换到浏览器弹出框，后续可以带对弹出框的操作: 'accept'-点击确认按钮，'dismiss'-点击取消按钮
                    # window-切换到指定页签，后续第一个参数如果为数字，代表切换到指定位置的窗口(开始为0，可以用-1指示最后一个)
                    #   后续第一个参数如果为文本，代表通过窗口标题来获取对应的窗口
                ['scroll_into_view'],  # 将当前元素滚动到可视范围
                ['run_script', 'window.alert(\'这是一个测试Alert弹窗\');']  # 执行js脚本
                ['find', op, para1, ...] # 忽略此前步骤查找到的元素，重新全局搜索元素并设置为当前元素, 数组后面为查找指令和对应的参数，参考find_elements
                ['find_child', op, para1, ...] # 搜索此前元素的子元素并设置为当前元素，数组后面为查找指令和对应的参数，参考find_elements
                ['click'] # 点击元素
                ['send_str', '要输入的文本'] # 元素输入文本
                ['send_keys', 'Keys.CONTROL', 'Keys.SHIFT', 'a', ...]  # 输入按键，传入多个代表同时按下
                    # 特殊按键定义参考 selenium.webdriver.common.keys.Keys
            ]
        @param {WebElement} parent=None - 执行的对象（如果步骤中有查找，则会根据查找情况逐步改变执行对象的值）

        @returns {list} - 返回最后的元素列表
        """
        return self.simple_driver.do_script(steps, parent=parent)


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    # _para_dict = Tools.get_correct_para_dict({
    #     'url': 'https://www.baidu.com',
    #     'wd_overtime': '3'
    # })

    # _web = WebDriverTool(_para_dict)

    # time.sleep(2)

    # _ret = _web.download(
    #     {
    #         '1.jpg': 'https://www.baidu.com/s?wd=%E4%BB%8A%E6%97%A5%E6%96%B0%E9%B2%9C%E4%BA%8B&tn=SE_Pclogo_6ysd4c7a&sa=ire_dl_gh_logo&rsv_dl=igh_logo_pc',
    #         '2.jpg': 'https://img2020.cnblogs.com/blog/2016690/202106/2016690-20210603085240237-1523193838.jpg'
    #     },
    #     '/Users/lhj/downtest/', wait_finish=True
    # )

    # print(_ret)

    # del _web
