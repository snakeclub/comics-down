#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
自动分析资源模块
@module auto_analyse
@file auto_analyse.py
"""

import os
import sys
import re
import ssl
import time
import urllib
import copy
from bs4 import BeautifulSoup
from bs4.element import Tag
from html.parser import HTMLParser
import traceback
from HiveNetLib.base_tools.net_tool import NetTool
from selenium.webdriver.chrome.options import Options
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.driver_fw import BaseDriverFW

__MOUDLE__ = 'auto_analyse'  # 模块名
__DESCRIPT__ = u'自动分析资源模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.10.25'  # 发布日期

# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
}


class AnalyzeTool(object):
    """
    分析工具
    """

    @classmethod
    def get_media_url(cls, url: str, type_list: list, **para_dict):
        """
        解析页面中的多媒体资源

        @param {str} url - 要解析的页面url
        @param {list} type_list - 要解析的视频类型, 例如 ['m3u8', 'mp4']
        @param {kwargs}  para_dict - 页面打开的参数配置

        @returns {str} - 解析到的m3u8文件下载地址
        """
        # 生成匹配规则
        _regex = re.compile(
            '\\.%s' % '|\\.'.join(type_list), re.I | re.M
        )

        _html = ''
        try:
            _html = cls._get_web_html_code(url, **para_dict)
        except:
            # 有可能会403错误
            print(traceback.format_exc())

        _is_break = False
        _urls = []
        while True:
            # 对页面信息进行解析
            for _match in _regex.finditer(_html):
                _start_pos = _match.span()[0]
                _end_pos = _match.span()[1]
                # _match_str = _match.group()

                # 要分别向后和向前找
                _is_forward = False
                while True:
                    if not _is_forward:
                        # 先向后找
                        if _html[_end_pos] in ('"', '\'', '<'):
                            # 到结尾了，再向前找
                            _is_forward = True
                            continue

                        _end_pos = _end_pos + 1
                    else:
                        # 向前找
                        _last_pos = _start_pos - 1
                        _temp_url = _html[_start_pos: _end_pos]
                        if _last_pos < 0 or _html[_last_pos] in ('"', '\'', '>') or _temp_url.startswith('http:') or _temp_url.startswith('https:'):
                            # 已经到结束的条件
                            if _temp_url.find('/') < 0 and _temp_url.find('%2F') >= 0:
                                # 如果没有'/'且存在
                                _temp_url = urllib.parse.unquote(_html[_start_pos: _end_pos])

                            _temp_url = HTMLParser().unescape(_temp_url).replace('\\', '')

                            # 处理http在后面的情况
                            _index = _temp_url.rfind('http://')
                            if _index < 0:
                                _index = _temp_url.rfind('https://')
                            if _index > 0:
                                _temp_url = _temp_url[_index:]
                            _urls.append(_temp_url.replace('\\', ''))
                            break

                        _start_pos = _last_pos

            if len(_urls) > 0 or _is_break:
                break

            # 通过源码获取不到资源，改为通过动态代码处理, 再执行一次
            _html = cls._get_web_html_source(url, **para_dict)
            _is_break = True

        if len(_urls) == 0:
            return None
        else:
            # 以有http开头的链接优先处理
            _ret_url = ''
            for _url in _urls:
                if _ret_url == '':
                    _ret_url = _url
                elif _ret_url.startswith('http'):
                    break
                elif _url.startswith('http'):
                    _ret_url = _url

            return _ret_url

    @classmethod
    def get_name_by_config(cls, url: str, config: dict, use_html_code=True, **para_dict) -> str:
        """
        通过查找配置获取资源名

        @param {str} url - 要获取的url
        @param {dict} config - 查找配置字典
            name_selector {str} - 获取资源名的tag元素查找css selector表达式
        @param {bool} use_html_code=True - 是否仅适用页面源码分析（False代表需获取动态页面代码）
        @param {dict} para_dict - 传入的页面下载参数（参考config.xml）

        @return {str} - 返回资源名
        """
        if use_html_code:
            _html = cls._get_web_html_code(url, **para_dict)
        else:
            _html = cls._get_web_html_source(url, **para_dict)

        _soup = BeautifulSoup(_html, 'html.parser')
        _tags = _soup.select(config['name_selector'])
        if len(_tags) == 0:
            raise RuntimeError('Tag not found with selector "%s"' % config['name_selector'])
        elif len(_tags) > 1:
            raise RuntimeError('Found mutiple tags with selector "%s"' % config['name_selector'])

        # 返回结果
        return _tags[0].string

    @classmethod
    def get_name_config(cls, urls: list, check_names: list, use_html_code=True, **para_dict) -> list:
        """
        分析网页智能获取资源名查找配置

        @param {list} urls - 要解析的同一类页面url清单，传入越多url清单匹配的准确性越高
        @param {list} check_names - 辅助分析代码的实际资源名清单，与对应位置的url相对应
        @param {bool} use_html_code=True - 是否仅适用页面源码分析（False代表需获取动态页面代码）
        @param {dict} para_dict - 传入的页面下载参数（参考config.xml）及解析参数，解析参数如下：
            selector_up_level {int} - 从当前元素向父节点查找几层, 默认为0

        @returns {list} - 解析出来的结果列表，每个配置为一个字符串
        """
        # 通过urls[0]进行解析，然后使用所有的urls进行结果的验证和排除
        if use_html_code:
            _html = cls._get_web_html_code(urls[0], **para_dict)
        else:
            _html = cls._get_web_html_source(urls[0], **para_dict)

        # 可用配置结果清单
        _configs = list()

        _soup = BeautifulSoup(_html, 'html.parser')
        _tags = _soup.find_all(text=check_names[0])
        for _i in _tags:
            _tag: Tag = _i.parent
            _selectors = cls._get_bs4_tag_selectors(_tag, **para_dict)
            print(_selectors)
            for _selector in _selectors:
                _check_tags = _soup.select(_selector[1])
                # 只有匹配到1个的情况，才认为是可用的
                if len(_check_tags) == 1 and _check_tags[0].string == check_names[0]:
                    _configs.append(_selector[1])

        # 从第二个开始验证
        _temp = copy.deepcopy(_configs)
        for _i in range(1, len(urls)):
            _url = urls[_i]
            if use_html_code:
                _html = cls._get_web_html_code(_url, **para_dict)
            else:
                _html = cls._get_web_html_source(_url, **para_dict)

            _soup = BeautifulSoup(_html, 'html.parser')

            for _config in _temp:
                _check_tags = _soup.select(_config)
                if not (len(_check_tags) == 1 and _check_tags[0].string == check_names[0]):
                    # 移除规则
                    _configs.remove(_config)

        return _configs

    @classmethod
    def get_col_config(cls, urls: list, check_names: list, use_html_code=True, **para_dict)-> list:
        """
        分析网页智能获取资源分卷查找配置

        @param {list} urls - 要解析的同一类页面url清单，传入越多url清单匹配的准确性越高
        @param {list} check_names - 辅助分析代码的实际卷名清单，与对应位置的url相对应
            每一个url对应传入两个相邻的显示卷名，例如('第01集', '第02集')
        @param {bool} use_html_code=True - 是否仅适用页面源码分析（False代表需获取动态页面代码）
        @param {dict} para_dict - 传入的页面下载参数（参考config.xml）及解析参数，解析参数如下：
            selector_up_level {int} - 从当前元素向父节点查找几层, 默认为0
            max_find_col_parent_level {int} - 从当前元素向上找共同父节点，最多找几层，默认为3

        @returns {list} - 解析出来的结果列表，每个配置为一个字典
        """
        # 通过urls[0]进行解析，然后使用所有的urls进行结果的验证和排除
        if use_html_code:
            _html = cls._get_web_html_code(urls[0], **para_dict)
        else:
            _html = cls._get_web_html_source(urls[0], **para_dict)

        # 可用配置结果清单
        _configs = list()

        _soup = BeautifulSoup(_html, 'html.parser')
        _tags = _soup.find_all(text=check_names[0][0])

        _max_find_col_parent_level = int(para_dict.get('max_find_col_parent_level', '3'))
        for _tag in _tags:
            # 尝试找相邻的卷信息
            _level = 0
            _parent = None
            _tag: Tag
            if (_tag.next_sibling is not None and _tag.next_sibling.string == check_names[0][1]) or (_tag.previous_sibling is not None and _tag.previous_sibling.string == check_names[0][1]):
                # 找到配置了
                _parent = _tag.parent

            _text_selector = ''
            _href_selector = _tag.name
            _temp_tag: Tag = _tag
            while _level <= _max_find_col_parent_level:
                _next_sibling = _temp_tag.next_sibling
                if _text_selector == ''
                if _temp_tag. is not None

    #############################
    # 内部工具
    #############################
    @classmethod
    def _get_web_html_code(cls, url: str, **para_dict) -> str:
        """
        获取页面的静态html代码

        @param {str} url - 页面url
        @param {kwargs}  para_dict - 页面打开的参数配置

        @returns {str} - 返回的html代码
        """
        # 生成Request对象
        _request = urllib.request.Request(url, headers=headers)
        return NetTool.get_web_page_code(
            _request, timeout=float(para_dict.get('overtime', '300.0')),
            encoding=para_dict.get('encoding', 'utf-8'), retry=int(para_dict.get('connect_retry', '3')),
        )

    @classmethod
    def _get_web_html_source(cls, url: str, **para_dict) -> str:
        """
        获取页面的动态html代码

        @param {str} url - 页面url
        @param {kwargs}  para_dict - 页面打开的参数配置

        @returns {str} - 返回的html代码
        """
        CHROME_OPTIONS = Options()

        # webdriver模式禁止图片和CSS下载的参数
        CHROME_OPTIONS.add_experimental_option(
            "prefs",
            {
                "profile.managed_default_content_settings.images": 2,
                'permissions.default.stylesheet': 2
            }
        )
        # 防止网站检测出Selenium的window.navigator.webdriver属性
        CHROME_OPTIONS.add_experimental_option('excludeSwitches', ['enable-automation'])
        CHROME_OPTIONS.add_argument("--no-sandbox")
        CHROME_OPTIONS.add_argument("--lang=zh-CN")

        # 使用代理
        if para_dict.get('proxy', '') != '':
            CHROME_OPTIONS.add_argument(
                "--proxy-server==%s" %
                para_dict.get('proxy', 'http://127.0.0.1:9000')
            )

        DRIVER_OPTIONS = {
            'chrome_options': CHROME_OPTIONS
        }

        _browser = NetTool.get_webdriver_browser(
            common_options={
                'timeout': float(para_dict.get('wd_overtime', '30')),
                'headless': (para_dict.get('wd_headless', 'n') == 'y'),
                'wait_all_loaded': True,
                'size_type': ('min' if para_dict.get('wd_min', 'n') == 'y' else '')
            },
            webdriver_type=BaseDriverFW.get_webdriver_type(para_dict.get('webdriver', 'Chrome')),
            driver_options=DRIVER_OPTIONS
        )
        _retry = 0
        while True:
            try:
                _html_source = NetTool.get_web_page_dom_code(
                    url,
                    browser=_browser,
                    common_options={
                        'timeout': float(para_dict.get('wd_overtime', '30')),
                        'headless': (para_dict.get('wd_headless', 'n') == 'y'),
                        'wait_all_loaded': True,
                        'quit': False,
                        'size_type': ('min' if para_dict.get('wd_min', 'n') == 'y' else '')
                    },
                    webdriver_type=BaseDriverFW.get_webdriver_type(
                        para_dict.get('webdriver', 'Chrome')),
                    driver_options=DRIVER_OPTIONS
                )
                # 成功执行，跳出循环
                break
            except:
                if _retry <= int(para_dict.get('connect_retry', '3')):
                    _retry += 1
                    continue
                else:
                    raise

        # 等待10秒让页面加载完成
        time.sleep(float(para_dict.get('chrome_load_time', '10')))

        # 获取iframe代码
        _html_source = cls._get_iframe_source(_browser, _html_source)

        # 关闭浏览器
        _browser.quit()

        # 返回结果
        return _html_source

    @classmethod
    def _get_iframe_source(cls, browser, merge_html: str) -> str:
        """
        根据浏览器获取iframe文本并合并到html文件中

        @param {webdriver.browser} browser - 浏览器对象
        @param {str} merge_html - 需要合并的文本

        @returns {str} - 合并后的文本（注意只是单纯在最后面添加）
        """
        _html = merge_html
        # 检查是否有iframe页面
        _iframes = []
        _iframes = browser.find_elements_by_tag_name("iframe")
        for _iframe in _iframes:
            browser.switch_to.frame(_iframe)
            _html = '%s%s' % (_html, browser.page_source)

            # 处理嵌套
            _html = cls._get_iframe_source(browser, _html)

            # 切换为上一父frame
            browser.switch_to.parent_frame()

        return _html

    @classmethod
    def _get_bs4_tag_selectors(cls, tag: Tag, current_level: int = 0, **para_dict) -> list:
        """
        获取bs4标签元素的查找css selector清单

        @param {Tag} tag - 要解析的标签元素
        @param {int} current_level=0 - 当前查找层数
        @param {dict} para_dict - 查找参数
            selector_up_level {int} - 从当前元素向父节点查找几层

        @returns {list[(level, str)]} - selector清单, (所处层, 查找表达式)
        """
        _selectors = []
        # 通过id查找, 如果有id，则直接通过id处理
        if 'id' in tag.attrs.keys():
            _selectors.append((current_level, '%s #%s' % (tag.name, tag.attrs['id'])))
            return _selectors

        if 'class' in tag.attrs.keys():
            # 通过标签名 + css类查找
            _class_list = tag.attrs['class']
            _selectors.append((current_level, '%s.%s' % (tag.name, '.'.join(_class_list))))

        # 直接tag标签获取
        _selectors.append((current_level, tag.name))

        # 找父节点
        _up_level = int(para_dict.get('selector_up_level', '0'))
        if current_level < _up_level:
            _parent_selectors = cls._get_bs4_tag_selectors(
                tag.parent, current_level=current_level+1, **para_dict
            )
            # 增加组合查找
            _cur_len = len(_selectors)  # 当前选择器的长度
            for _up_selector in _parent_selectors:
                for _index in range(_cur_len):
                    _selectors.append((
                        _up_selector[0],
                        '%s > %s' % (_up_selector[1], _selectors[_index][1])
                    ))

        return _selectors


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    # _url = AnalyzeTool.get_media_url(
    #     'http://javhdus.com/vod-play-id-109318-src-1-num-1.html',
    #     ['m3u8', 'mp4'], **{'proxy': 'http://127.0.0.1:9000'}
    # )
    # print(_url)

    # _configs = AnalyzeTool.get_name_config(
    #     ['http://www.edddh.com/vod/sishen/', ], ['死神', ],
    #     **{
    #         'selector_up_level': '3'
    #     }
    # )

    print(
        AnalyzeTool.get_name_by_config(
            'http://www.edddh.com/vod/sishen/', {'name_selector': 'div #zanpian-score > h1.text-overflow'})
    )
