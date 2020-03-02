#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
初始化的部分网站下载驱动
@module init_drivers
@file init_drivers.py
"""

import os
import sys
import re
import urllib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from HiveNetLib.base_tools.net_tool import NetTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.driver_fw import BaseDriverFW


__MOUDLE__ = 'init_drivers'  # 模块名
__DESCRIPT__ = u'初始化的部分网站下载驱动'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.03.01'  # 发布日期


class Mh177Driver(BaseDriverFW):
    """
    www.177mh.net漫画网的下载驱动
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
            'www.177mh.net': '新新漫画'
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
        _html_code = NetTool.get_web_page_code(
            para_dict['url'], timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        # 返回漫画名
        return _soup.find_all('ul', attrs={'class': 'ar_list_coc'})[0].li.h1.string

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
        print('get_vol_info: ', index_url)
        _url_info = urlparse(index_url)
        _html_code = NetTool.get_web_page_code(
            index_url, timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        _voldict = dict()
        _vollist = _soup.find_all(
            'ul', attrs={
                'id': 'ar_list_normal ar_rlos_bor',
                'class': 'ar_rlos_bor ar_list_col'
            }
        )[0]
        for _vol in _vollist.children:
            if _vol.name != 'li':
                continue

            _vol_name = _vol.a.string
            _vol_url = '%s://%s/%s' % (
                _url_info.scheme, _url_info.netloc, _vol.a['href']
            )
            _voldict[_vol_name] = _vol_url

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
        # 解析页面代码
        print('get_file_info: ', vol_url)
        _html_code = NetTool.get_web_page_code(
            vol_url, timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        # 需要用动态生成的html dom对象，从第一张图片找真实地址
        _html_source = NetTool.get_web_page_dom_code(
            vol_url,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.ID, "dracga"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver'])
        )
        _soup_source = BeautifulSoup(_html_source, 'html.parser')
        _src = _soup_source.find_all('img', attrs={'id': 'dracga'})[0]['src']
        _src, _src_name = os.path.split(_src)
        _dotindex = _src_name.index('.')
        _src_ext = _src_name[_dotindex:]
        _src_name = _src_name[0: _dotindex]

        # 通过js获取文件名
        _script = _soup.find_all('div', attrs={'id': 'main'})[0].script.string
        _name_list = re.findall('(?!\|)[0-9]{%d,}(?=\|)' % len(_src_name), _script, re.M)

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        for _file in _name_list:
            _name = _file + _src_ext
            _file_url = '%s/%s' % (_src, _name)
            _filedict[_name] = [_file_url, 'http']

        return [None, _filedict]


class Hhxxee99Driver(BaseDriverFW):
    """
    99.hhxxee.com漫画网的下载驱动
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
            '99.hhxxee.com': '久久动漫'
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
        _html_code = NetTool.get_web_page_code(
            para_dict['url'], timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        # 返回漫画名
        return _soup.find_all('div', attrs={'id': 'titleDiv'})[0].h1.a.string

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
        print('get_vol_info: ', index_url)
        _url_info = urlparse(index_url)
        _html_code = NetTool.get_web_page_code(
            index_url, timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        _voldict = dict()
        _vollist = _soup.find_all(
            'div', attrs={
                'class': 'cVolList'
            }
        )
        for _vol in _vollist[0].children:
            _vol_name = _vol.a.string
            _vol_url = '%s://%s/%s' % (
                _url_info.scheme, _url_info.netloc, _vol.a['href']
            )
            _voldict[_vol_name] = _vol_url

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
        # 解析页面代码
        print('get_file_info: ', vol_url)
        _html_code = NetTool.get_web_page_code(
            vol_url, timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')
        _list_text: str = _soup.find_all('link', attrs={'href': '/css/view.css'})[0].next.string
        _list_text = _list_text[12: _list_text.find('";', 12)]

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        _check_src = False
        _src = ''
        _file_url = ''
        _list = _list_text.split('|')
        for _file in _list:
            _name = os.path.split(_file)[1]
            if not _check_src:
                _check_src = True
                # 尝试先用传入来的地址获取图片
                if last_tran_para != '':
                    _file_url = '%s/%s' % (last_tran_para, _file)
                    if cls._check_99_url_ok(_file_url):
                        _src = last_tran_para

                # 传入的src无效
                if _src == '':
                    # 获取图片的真实地址
                    _html_source = NetTool.get_web_page_dom_code(
                        vol_url,
                        common_options={
                            'timeout': float(para_dict['wd_overtime']),
                            'headless': (para_dict['wd_headless'] == 'y'),
                            'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                            'until_menthod': EC.presence_of_element_located((By.ID, "imgCurr"))
                        },
                        webdriver_type=cls.get_webdriver_type(para_dict['webdriver'])
                    )
                    _soup_source = BeautifulSoup(_html_source, 'html.parser')
                    _src = _soup_source.find_all('img', attrs={'id': 'imgCurr'})[0]['src']
                    _src = _src[0: _src.find('/ok-comic') - 1]

            _file_url = '%s/%s' % (
                _src, _file
            )
            _filedict[_name] = [_file_url, 'http']

        return [_src, _filedict]

    #############################
    # 内部函数
    #############################
    @classmethod
    def _check_99_url_ok(cls, url: str):
        try:
            response = urllib.request.urlopen(url)
            if response.length == 5174:
                # 返回一个固定的值
                return False
            return True
        except:
            return False


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    # 测试代码
    _para_dict = {
        'url': '',
        'name': '',
        'path': '',
        'job_worker': '1',
        'auto_redo': 'n',
        'encoding': 'utf-8',
        'force_update': 'n',
        'job_down_worker': '10',
        'down_overtime': '300',
        'use_break_down': 'y',
        'overtime': '30',
        'connect_retry': '3',
        'verify': 'y',
        'remove_wget_tmp': 'y',
        'webdriver': 'Chrome',
        'wd_wait_all_loaded': 'n',
        'wd_overtime': '30',
        'wd_headless': 'n',
        'search_mode': 'n',
        'show_rate': 'n'
    }

    # _vol_info = Mh177Driver._get_vol_info('https://www.177mh.net/colist_244413.html', **_para_dict)
    # print(_vol_info)

    _file_info = Mh177Driver._get_file_info(
        'https://www.177mh.net/202003/443514.html', None, **_para_dict)
    print(_file_info)
