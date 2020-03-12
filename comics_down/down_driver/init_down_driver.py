#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
初始化的文件下载驱动
@module init_down_driver
@file init_down_driver.py
"""
import os
import sys
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from HiveNetLib.base_tools.net_tool import NetTool
import HiveNetLib.base_tools.wget as wget
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.down_driver_fw import BaseDownDriverFW


__MOUDLE__ = 'init_down_driver'  # 模块名
__DESCRIPT__ = u'初始化的文件下载驱动'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.03.03'  # 发布日期


class HttpDownDriver(BaseDownDriverFW):
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


class FtpDownDriver(BaseDownDriverFW):
    """
    普通ftp连接的图片下载驱动
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
        return 'ftp'

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        wget.download(file_url, out=save_file, bar=None)


class MangabzDownDriver(BaseDownDriverFW):
    """
    Mangabz网站的图片下载驱动
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
        return 'Mangabz'

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        # 需要用动态生成的html dom对象，找真实图片地址
        _options = Options()
        _prefs = {"profile.managed_default_content_settings.images": 2,
                  'permissions.default.stylesheet': 2}
        _options.add_experimental_option("prefs", _prefs)
        _driver_options = {
            'chrome_options': _options
        }

        _html_source = NetTool.get_web_page_dom_code(
            file_url,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.ID, "cp_image"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=_driver_options
        )
        _soup_source = BeautifulSoup(_html_source, 'html.parser')
        _file_url = _soup_source.find_all('img', attrs={'id': 'cp_image'})[0]['src']
        _url_info = urlparse(_file_url)
        _real_url = '%s://%s%s' % (_url_info.scheme, _url_info.netloc, _url_info.path)

        # 下载文件, 需要传报文头避免防盗链
        _opener = urllib.request.build_opener()
        _opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(_opener)
        urllib.request.urlretrieve(_real_url, save_file)


class ManhuaguiDownDriver(BaseDownDriverFW):
    """
    Manhuagui网站的图片下载驱动
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
        return 'Manhuagui'

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        # 需要用动态生成的html dom对象，找真实图片地址
        _options = Options()
        _prefs = {"profile.managed_default_content_settings.images": 2,
                  'permissions.default.stylesheet': 2}
        _options.add_experimental_option("prefs", _prefs)
        _driver_options = {
            'chrome_options': _options
        }

        _browser = NetTool.get_webdriver_browser(
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.ID, "mangaFile"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=_driver_options
        )

        _html_source = NetTool.get_web_page_dom_code(
            file_url,
            browser=_browser,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.ID, "mangaFile"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=_driver_options
        )
        _soup_source = BeautifulSoup(_html_source, 'html.parser')
        _file_url = _soup_source.find_all('img', attrs={'id': 'mangaFile'})[0]['src']

        # 下载文件, 需要传报文头避免防盗链
        wget.download(_file_url, save_file, bar=None, headers={'User-agent': 'Mozilla/5.0'})


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    print(urlparse('http://image.mangabz.com/1/75/16312/3_6056.jpg?cid=16312&amp;key=4cfe964df8ce75f8c4ef7e2be4f6a3bb&amp;uk='))
