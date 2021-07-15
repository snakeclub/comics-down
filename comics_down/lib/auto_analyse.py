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
import html
import traceback
from HiveNetLib.html_parser import HtmlElement, HtmlParser
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import Tools
from comics_down.lib.webdriver_tool import WebDriverTool

__MOUDLE__ = 'auto_analyse'  # 模块名
__DESCRIPT__ = u'自动分析资源模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.10.25'  # 发布日期

# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
}


class AnalyzeTool(object):
    """
    分析工具
    """

    @classmethod
    def get_media_url(cls, url: str, type_list: list = None, back_all: bool = False, **para_dict):
        """
        解析播放页面中的多媒体资源

        @param {str} url - 要解析的页面url
        @param {list} type_list=None - 要解析的视频类型, 例如 ['m3u8', 'mp4']
        @param {bool} back_all=False - 返回全部可能url清单
        @param {kwargs}  para_dict - 页面打开的参数配置
            除download的通用参数外，增加以下参数：
            loaded_wait_time - 等待页面加载视频的时间，单位为秒，默认为10秒

        @returns {str|list} - 解析到的视频文件下载地址，如果back_all为False优先返回http开头的url，否则返回列表
        """
        if type_list is None:
            type_list = ['m3u8', 'mp4']

        # 生成匹配规则, 在页面中查找带有指定视频扩展名后缀的字符串位置 .m3u8 或 .mp4
        _regex = re.compile(
            '\\.%s' % '|\\.'.join(type_list), re.I | re.M
        )

        _html = ''
        try:
            _html = cls._get_web_html_code(url, **para_dict)
        except:
            # 有可能会403错误, 不用抛出异常，后面会用selenium浏览器重新执行一次
            print(traceback.format_exc())

        # 查找步骤
        # 1. 向后找到结束字符： ", ', < ，找到代表当前文件的查找结束
        # 2. 向前找到开始字符串：", ', >, 'http:', 'https:'
        _is_break = False
        _urls = []  # 获取到可能是视频文件的url
        _webdriver: WebDriverTool = None  # 动态获取的浏览器对象
        while True:
            # 对页面信息进行解析, 获取特定后缀名的内容
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
                                # 如果没有'/'且存在URL传参转义符'%2F'(/的转义编码)，解码转回正常文本格式
                                _temp_url = urllib.parse.unquote(_html[_start_pos: _end_pos])

                            # 将html编码转义符替换回正常的文本格式，同时把js情况下的字符转义符'\'也去掉
                            _temp_url = html.unescape(_temp_url).replace('\\', '')

                            # 查找http://及https://的位置，如果发现不在字符串开头，则以该位置开始截取字符串
                            _index = _temp_url.rfind('http://')
                            if _index < 0:
                                _index = _temp_url.rfind('https://')
                            if _index > 0:
                                _temp_url = _temp_url[_index:]

                            _urls.append(_temp_url.replace('\\', ''))  # 添加到url清单
                            break  # 跳出向前向后的查找循环

                        _start_pos = _last_pos

            # 尝试获取特定播放器的场景，比如dplayer
            _parser = HtmlParser(_html, use_xpath2=False)

            # dplayer 播放器
            _class_xpath = '[@class="{0}" or starts-with(@class, "{0} ") or contains(@class, " {0} ") or substring(@class, string-length(@class) - string-length(" {0}") +1) = " {0}"]'.format(
                'dplayer-video')
            _els = _parser.find_elements([
                ['xpath', '//div[@class="dplayer-video-wrap"]/video%s' % _class_xpath],
            ])
            for _el in _els:
                _url = _el.get_attribute('src')
                if _url is not None:
                    _urls.append(_url)

            if len(_urls) > 0 or _is_break:
                # 如果静态页面已经能查到视频文件，则不再通过动态页面代码进行处理
                break

            if _webdriver is None:
                # 通过源码获取不到资源，改为通过动态代码处理, 再用同样的逻辑查找一次
                _webdriver, _html = cls._get_web_html_source(url, **para_dict)
            else:
                # 动态代码也查找不到，尝试点击页面的播放按钮，然后再执行查找
                # dplayer 播放器
                _xpath = '//button[@class="{0}" or starts-with(@class, "{0} ") or contains(@class, " {0} ") or substring(@class, string-length(@class) - string-length(" {0}") +1) = " {0}"]'.format(
                    'dplayer-play-icon')
                _els = _parser.find_elements([
                    ['xpath', _xpath],
                ])
                if len(_els) > 0:
                    # 找到按钮，进行点击处理, 注意操作可能在iframe底下，需要特殊处理
                    _ret = cls._do_script_with_iframe(
                        _webdriver, [
                            ['find', 'xpath', _xpath],
                            ['click']
                        ]
                    )
                    if len(_ret) > 0:
                        # 等待页面加载
                        time.sleep(float(para_dict.get('loaded_wait_time', '5')))
                        _html = _webdriver.get_current_dom()
                        _html = cls._get_iframe_source(_webdriver, _html)
                    else:
                        # 没有找到按钮
                        break
                else:
                    # 找不到按钮，直接退出
                    break

                # 最后一次查找
                _is_break = True

        # 关闭浏览器
        if _webdriver is not None:
            del _webdriver

        if back_all:
            return _urls
        else:
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
    def get_contents_by_config(cls, url: str, config: dict, attr_name: dict = {},
                               use_html_code=True, error_on_not_exists: bool = False, **para_dict) -> dict:
        """
        通过xpath配置字典获取指定的网页信息

        @param {str} url - 要获取的url
        @param {dict} config - 查找配置字典
            key {str} - 内容标识
            value {list} - 匹配上的xpath清单
        @param {dict} attr_name={} - 设定对应check_contents的属性配置字典
            key {str} - 内容标识
            value {str} - 内容属性名，如果不指定代表内容来自显示的text
        @param {bool} use_html_code=True - 是否仅使用页面源码分析（False代表需获取动态页面代码）
        @param {bool} error_on_not_exists=False - 遇到查找不到时是否抛出异常
        @param {dict} para_dict - 传入的页面下载参数（参考config.xml）及解析参数

        @returns {dict} - 获取到的网页信息
            key {str} - 内容标识
            value {str} - 内容值，获取不到值为None
        """
        _para_dict = copy.deepcopy(para_dict)
        _para_dict['url'] = url
        if use_html_code:
            _html = WebDriverTool.get_web_page_code(_para_dict)
        else:
            _html = WebDriverTool.get_web_page_dom(_para_dict)

        _parser = HtmlParser(_html)

        _web_infos = dict()
        # 遍历获取信息
        for _id, _configs in config:
            _els = _parser.find_elements([['xpath', _configs[0]]])
            if len(_els) == 0:
                if error_on_not_exists:
                    raise ModuleNotFoundError(
                        'content id[%s] not exists: xpath[%s]' % (_id, _configs[0]))
                else:
                    _val = None
            else:
                _attr_name = attr_name.get(_id, '')
                if _attr_name == '':
                    _val = _els[0].text
                else:
                    _val = _els[0].get_attribute(_attr_name)

            _web_infos[_id] = _val

        return _web_infos

    @classmethod
    def get_contents_config(cls, urls: list, check_contents: dict, attr_name: dict = {}, is_tail: bool = False,
                            use_html_code=True, search_dict: dict = {}, **para_dict) -> dict:
        """
        尝试解析获取单个内容对应的xpath清单

        @param {list} urls - 要解析的同一类页面url清单，传入越多url清单匹配的准确性越高
        @param {dict} check_contents - 辅助分析代码的实际内容信息字典
            key {str} - 内容标识，例如name, author, ...
            value {list} - 与urls一一对应的内容信息清单
        @param {dict} attr_name={} - 设定对应check_contents的属性配置字典
            key {str} - 内容标识
            value {str} - 内容属性名，如果不指定代表内容来自显示的text
        @param {bool} is_tail=False - text情况，指示是否子对象的tail部分(<li><span>xx</span>要搜索的内容</li>)
        @param {bool} use_html_code=True - 是否仅使用页面源码分析（False代表需获取动态页面代码）
        @param {dict} search_dict - 查找参数
            selector_up_level {int} - 从当前元素向父节点查找几层, 默认0层, -1代表一直往上追索
            split_class {bool} - 将类拆开单个获取（将会增加需匹配的xpath数量, 降低效率），默认为False
        @param {dict} para_dict - 传入的页面下载参数（参考config.xml）及解析参数

        @returns {dist} - 匹配上的xpath列表字典
            key {str} - 内容标识
            value {list} - 匹配上的xpath清单
        """
        # 通过urls[0]进行解析，然后使用所有的urls进行结果的验证和排除
        _para_dict = copy.deepcopy(para_dict)
        _para_dict['url'] = urls[0]
        if use_html_code:
            _html = WebDriverTool.get_web_page_code(_para_dict)
        else:
            _html = WebDriverTool.get_web_page_dom(_para_dict)

        _parser = HtmlParser(_html)

        # 逐个内容标识通过第一个url获取匹配xpath
        _match_dict = dict()  # 最后匹配的配置字典
        for _id, _contents in check_contents.items():
            # 初始的搜索
            _attr_name = attr_name.get(_id, '')
            if _attr_name == '':
                _attr_name = 'text()'
            else:
                _attr_name = '@' + _attr_name

            # 查找对象
            _els = _parser.find_elements(
                [['xpath', './/*[%s="%s"]' % (_attr_name, _contents[0])]]
            )

            if len(_els) == 0:
                raise ModuleNotFoundError(
                    'element not found: attr_name[%s], content["%s"], url[%s]' % (
                        _attr_name, _contents[0], urls[0]
                    )
                )

            _configs = list()
            for _element in _els:
                _xpaths = cls.get_element_xpath(
                    _parser, _element, check_xpath=True, **search_dict
                )
                _configs.extend(_xpaths)

            _match_dict[_id] = _configs

        # 逐个内容标识通过比较对象进行匹配xpath的验证
        for _id, _contents in check_contents.items():
            _configs = _match_dict[_id]
            # 逐个比较对象进行验证处理
            for _index in range(1, len(urls)):
                if len(_configs) == 0:
                    # 没有找到任何需要验证的xpath，直接退出不处理
                    break

                # 获取比较对象页面信息
                _para_dict['url'] = urls[_index]
                if use_html_code:
                    _html_check = WebDriverTool.get_web_page_code(_para_dict)
                else:
                    _html_check = WebDriverTool.get_web_page_dom(_para_dict)

                _parser_check = HtmlParser(_html_check)
                _attr_name = attr_name.get(_id, '')

                # 逐个xpath进行比较确认是否通过
                _check_ok_xpaths = list()
                for _xpath in _configs:
                    _els_check = _parser_check.find_elements([['xpath', _xpath]])
                    if len(_els_check) != 1:
                        continue

                    if _attr_name == '':
                        if is_tail:
                            _childs = _els_check[0].element.getchildren()
                            if not(len(_childs) > 0 and _childs[0].tail == _contents[_index]):
                                continue
                        else:
                            if _els_check[0].text != _contents[_index]:
                                continue
                    else:
                        if _els_check[0].get_attribute(_attr_name) != _contents[_index]:
                            continue

                    # 检查通过
                    _check_ok_xpaths.append(_xpath)

                # 当前对象比较完成，更新xpath清单，继续比较下一个对象
                _configs = _check_ok_xpaths

            # 更新处理结果
            _match_dict[_id] = _configs

        return _match_dict

    @classmethod
    def get_element_xpath(cls, html_parser: HtmlParser, element: HtmlElement, check_xpath: bool = False,
                          current_level: int = 0, **search_dict) -> list:
        """
        获取查找指定元素的可用xpath selector清单

        @param {HtmlParser} html_parser - html解析器
        @param {HtmlElement} element - 要查找的元素对象
        @param {bool} check_xpath=False - 是否进行最终的xpath校验
        @param {int} current_level=0 - 当前查找层数
        @param {dict} search_dict - 查找参数
            selector_up_level {int} - 从当前元素向父节点查找几层, 默认0层, -1代表一直往上追索
            split_class {bool} - 将类拆开单个获取（将会增加需匹配的xpath数量, 降低效率），默认为False


        @returns {list[[level, str]]} - selector清单, [所处层, 查找表达式]
        """
        _selectors = []

        _end = False
        # 通过id查找, 如果有id，则直接通过id处理
        if element.get_attribute('id') is not None:
            _selectors.append([current_level, '/%s[@id="%s"]' % (element.tag_name, element.id)])
            _end = True

        # 通过name名查找a
        _name = element.get_attribute('name')
        if not _end and _name is not None:
            _selectors.append([current_level, '/%s[@name="%s"]' % (element.tag_name, _name)])
            _end = True

        if not _end:
            # 通过标签名 + css类查找
            _class_list = element.get_attribute('class')
            if _class_list is not None:
                _selectors.append(
                    [current_level, '/%s[@class="%s"]' % (element.tag_name, _class_list)]
                )
                if search_dict.get('split_class', False):
                    for _class in _class_list.split(' '):
                        if _class != '':
                            _selectors.append(
                                [current_level, '/{1}[@class="{0}" or starts-with(@class, "{0} ") or contains(@class, " {0} ") or ends-with(@class, " {0}")]'.format(
                                    _class, element.tag_name)]
                            )

            # 直接通过标签获取
            _selectors.append([current_level, '/%s' % element.tag_name])

            # 找父节点, 并进行组合处理
            _up_level = int(search_dict.get('selector_up_level', '0'))
            if (_up_level == -1 or current_level < _up_level) and element.parent is not None:
                _parent_selectors = cls.get_element_xpath(
                    html_parser, element.parent, current_level=current_level + 1, **search_dict
                )
                # 增加组合查找
                _cur_len = len(_selectors)  # 当前选择器的长度
                for _up_selector in _parent_selectors:
                    for _index in range(_cur_len):
                        _selectors.append([
                            _up_selector[0],
                            '%s%s' % (_up_selector[1], _selectors[_index][1])
                        ])

        # 处理最后的返回结果, 第0层增加/形成//开头，遍历所有层级
        if current_level == 0:
            _check_list = list()
            for _index in range(len(_selectors)):
                _selectors[_index][1] = '/%s' % _selectors[_index][1]
                if check_xpath:
                    # 逐个xpath进行验证
                    _find_el = html_parser.find_elements([['xpath', _selectors[_index][1]]])
                    if len(_find_el) == 1 and element.is_same_with(_find_el[0], with_path=True):
                        _check_list.append(_selectors[_index][1])

            if check_xpath:
                return _check_list

        return _selectors

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
        _para_dict = Tools.get_correct_para_dict(para_dict)
        _para_dict['url'] = url
        return WebDriverTool.get_web_page_code(_para_dict, headers=HEADERS)

    @classmethod
    def _get_web_html_source(cls, url: str, **para_dict) -> str:
        """
        获取页面的动态html代码(包含iframe的代码)

        @param {str} url - 页面url
        @param {kwargs}  para_dict - 页面打开的参数配置

        @returns {(WebDriverTool,str)} - 浏览器对象，返回的html代码
        """
        _para_dict = Tools.get_correct_para_dict(para_dict)
        _para_dict['url'] = url

        _webdriver: WebDriverTool = None

        _retry = 0
        while True:
            try:
                _webdriver = WebDriverTool(_para_dict)
                _html_source = _webdriver.get_current_dom()
                # 成功执行，跳出循环
                break
            except:
                if _retry <= int(_para_dict.get('connect_retry', '3')):
                    _retry += 1
                    continue
                else:
                    raise

        # 等待5秒让页面加载完成
        time.sleep(float(para_dict.get('loaded_wait_time', '5')))

        # 获取iframe代码
        _html_source = cls._get_iframe_source(_webdriver, _html_source)

        # 关闭浏览器
        # del _webdriver

        # 返回结果
        return _webdriver, _html_source

    @classmethod
    def _get_iframe_source(cls, webdriver_tool: WebDriverTool, merge_html: str) -> str:
        """
        根据浏览器获取iframe文本并合并到html文件中

        @param {WebDriverTool} webdriver_tool - webdriver工具实例
        @param {str} merge_html - 需要合并的文本

        @returns {str} - 合并后的文本（注意只是单纯在最后面添加）
        """
        _html = merge_html

        # 遍历iframe页面获取代码并合并
        _iframes = webdriver_tool.find_elements([['xpath', '//iframe']])
        for _iframe in _iframes:
            webdriver_tool.switch_to_frame(_iframe)
            _html = '%s%s' % (_html, webdriver_tool.get_current_dom())

            # 处理iframe嵌套的情况
            _html = cls._get_iframe_source(webdriver_tool, _html)

            # 切换回上一层iframe
            webdriver_tool.switch_to_parent_frame()

        return _html

    @classmethod
    def _do_script_with_iframe(cls, webdriver_tool: WebDriverTool, steps: list) -> list:
        """
        遍历iframe执行动作，直到遇到可正常执行的情况

        @param {WebDriverTool} webdriver_tool - webdriver工具实例
        @param {list} steps - 要执行的动作数组

        @returns {list} - 返回执行后的元素列表
        """
        # 先执行当前frame页自身
        _ret = webdriver_tool.do_script(steps)
        if len(_ret) > 0:
            return _ret

        # 自身frame页没有执行成功，遍历iframe页面
        _iframes = webdriver_tool.find_elements([['xpath', '//iframe']])
        for _iframe in _iframes:
            webdriver_tool.switch_to_frame(_iframe)

            # 处理iframe嵌套的情况
            _ret = cls._do_script_with_iframe(webdriver_tool, steps)
            if len(_ret) > 0:
                return _ret

            # 切换回上一层iframe
            webdriver_tool.switch_to_parent_frame()

        return _ret


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    print(
        AnalyzeTool.get_media_url(
            'http://www.edddh.net/vod/juchangbanxiamuyourenzhangyuanjiekongchan/1-1.html',
            **{'loaded_wait_time': '1'}
        )
    )
