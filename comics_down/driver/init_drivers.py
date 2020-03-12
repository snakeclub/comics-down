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
import execjs  # 需要安装Node.js环境
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.base_tools.string_tool import StringTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.driver_fw import BaseDriverFW


__MOUDLE__ = 'init_drivers'  # 模块名
__DESCRIPT__ = u'初始化的部分网站下载驱动'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.03.01'  # 发布日期


# webdriver模式禁止图片和CSS下载的参数
NO_IMG_CSS_OPTIONS = Options()
NO_IMG_CSS_OPTIONS.add_experimental_option(
    "prefs",
    {
        "profile.managed_default_content_settings.images": 2,
        'permissions.default.stylesheet': 2
    }
)
NO_IMG_CSS_DRIVER_OPTIONS = {
    'chrome_options': NO_IMG_CSS_OPTIONS
}


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
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
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


class GuFengMHDriver(BaseDriverFW):
    """
    www.gufengmh.com古风漫画网的下载驱动
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
            'www.gufengmh.com': '古风漫画网'
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
        return _soup.find_all('div', attrs={'class': 'book-title'})[0].h1.span.string

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
                'class': 'chapter-body clearfix'
            }
        )
        for _chapter in _vollist:
            for _vol in _chapter.ul.children:
                if _vol.name != 'li':
                    continue

                _vol_name = _vol.a.span.string
                _vol_url = '%s://%s/%s' % (
                    _url_info.scheme, _url_info.netloc, _vol.a['href']
                )
                _i = 0
                _vol_name_plus = _vol_name
                while _vol_name_plus in _voldict.keys():
                    # 这个网站的章节有重复的情况, 自动加序号
                    _i += 1
                    _vol_name_plus = _vol_name + StringTool.fill_fix_string(str(_i), 3, '0')

                _voldict[_vol_name_plus] = _vol_url

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

        # 通过js获取文件名
        _script = _soup.find_all('body', attrs={'class': 'clearfix'})[0].script.string
        _image_path = re.findall('(?<=var chapterPath = \").*?(?=\";)', _script, re.M)[0]
        _page_image = re.findall('(?<=var pageImage = \").*?(?=\";)', _script, re.M)[0]
        _url_info = urlparse(_page_image)
        _name_list = re.findall(
            '(?<=var chapterImages = \[)".*"(?=\];)', _script, re.M)[0].split(',')

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        for _file in _name_list:
            _name = _file.strip(' "')
            _file_url = '%s://%s/%s%s' % (_url_info.scheme, _url_info.netloc, _image_path, _name)
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
                        webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
                        driver_options=NO_IMG_CSS_DRIVER_OPTIONS
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


class HhimmDriver(BaseDriverFW):
    """
    www.hhimm.com 汗汗酷漫的下载驱动
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
            'www.hhimm.com': '汗汗酷漫'
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
        return _soup.find_all('div', attrs={'id': 'about_kit'})[0].ul.li.h1.next_element.string.strip(' \r\n')

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
            注：
            (1)应用会根据vol_next_url判断要不要循环获取卷信息
            (2)卷名可以通过标签‘{$path_split$}’来设置卷保存的子目录
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
                'class': 'cVolTag'
            }
        )
        _vol_type_num = len(_vollist)
        for _chapter in _vollist:
            _sub_path = _chapter.string
            if _vol_type_num == 1:
                _sub_path = ''

            for _vol in _chapter.next_sibling.children:
                if _vol.name != 'li':
                    continue

                _vol_name = _vol.a.string
                if _sub_path != '':
                    _vol_name = '%s{$path_split$}%s' % (_sub_path, _vol_name)

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

        _url_info = urlparse(vol_url)
        _js_ctx = cls._complie_get_name_js()
        _domain = _soup.find_all('input', attrs={
            'id': 'hdDomain'
        })[0]['value'].split('|')[0]
        _page_count = int(_soup.find_all('input', attrs={
            'id': 'hdPageCount'
        })[0]['value'])

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        _i = 1
        while _i <= _page_count:
            _i += 1
            _name_code = _soup.find_all('input', attrs={
                'id': 'hdNextImg'
            })[0].previous_sibling['name']

            _file_url = '%s%s' % (
                _domain, cls._call_get_name_jsfun(_js_ctx, _name_code)
            )
            _name = os.path.split(_file_url)[1]
            _filedict[_name] = [_file_url, 'http']

            # 下一页
            _next_url = '%s://%s%s?%s' % (
                _url_info.scheme, _url_info.hostname,
                _url_info.path.replace('/1.html', '/%d.html' % _i), _url_info.query
            )
            _html_code = NetTool.get_web_page_code(
                _next_url, timeout=float(para_dict['overtime']),
                encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
            )
            _soup = BeautifulSoup(_html_code, 'html.parser')

        return [None, _filedict]

    #############################
    # 内部函数 - 执行js函数
    #############################
    @classmethod
    def _complie_get_name_js(cls):
        """
        编译要获取图片名称的js函数
        """
        return execjs.compile("""
        function unsuan(s)
        {
            sw="44123.com|hhcool.com|hhimm.com";
            su = "www.hhimm.com".toLowerCase();
            b=false;
            for(i=0;i<sw.split("|").length;i++) {
                if(su.indexOf(sw.split("|")[i])>-1) {
                    b=true;
                    break;
                }
            }
            if(!b)return "";

            x = s.substring(s.length-1);
            w="abcdefghijklmnopqrstuvwxyz";
            xi=w.indexOf(x)+1;
            sk = s.substring(s.length-xi-12,s.length-xi-1);
            s=s.substring(0,s.length-xi-12);
            k=sk.substring(0,sk.length-1);
            f=sk.substring(sk.length-1);
            for(i=0;i<k.length;i++) {
                eval("s=s.replace(/"+ k.substring(i,i+1) +"/g,'"+ i +"')");
            }
            ss = s.split(f);
            s="";
            for(i=0;i<ss.length;i++) {
                s+=String.fromCharCode(ss[i]);
            }
            return s;
        }
        """)

    @classmethod
    def _call_get_name_jsfun(cls, js_ctx, name_code):
        """
        执行获取图片名字的函数

        @param {[type]} js_ctx - <description>
        @param {[type]} name_code - <description>
        """
        return js_ctx.call('unsuan', name_code)


class ManhuaguiDriver(BaseDriverFW):
    """
    www.manhuagui.com 漫画柜的下载驱动
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
            'www.manhuagui.com': '漫画柜 - 未解决文件下载问题'
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
        return _soup.find_all('div', attrs={'class': 'book-title'})[0].h1.string

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
            注：
            (1)应用会根据vol_next_url判断要不要循环获取卷信息
            (2)卷名可以通过标签‘{$path_split$}’来设置卷保存的子目录
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
                'class': 'chapter-list cf mt10'
            }
        )
        _vol_type_num = len(_vollist)
        for _chapter in _vollist:
            _sub_path = _chapter.previous_sibling.span.string
            if _vol_type_num == 1:
                _sub_path = ''

            for _vol in _chapter.ul.children:
                if _vol.name != 'li':
                    continue

                _vol_name = _vol.a['title']
                if _sub_path != '':
                    _vol_name = '%s{$path_split$}%s' % (_sub_path, _vol_name)

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

        # 获取页数
        _page_size = int(_soup.find_all('span', attrs={'id': 'page'})[0].next_sibling.strip('/)'))

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        _i = 1
        while _i <= _page_size:
            _name = StringTool.fill_fix_string(str(_i), 6, '0')
            _file_url = vol_url + '#p=' + str(_i)
            _filedict[_name] = [_file_url, 'Manhuagui']
            _i += 1

        return [None, _filedict]


class MangabzDriver(BaseDriverFW):
    """
    http://www.mangabz.com/ Mangabz的下载驱动
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
            'www.mangabz.com': 'Mangabz(下载需频繁打开页面处理,效率低)'
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
        # 直接获取源码方式会超时
        _html_source = NetTool.get_web_page_dom_code(
            para_dict['url'],
            common_options={
                'timeout': 10,
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': 'n',
                'until_menthod': None
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
        )
        _soup = BeautifulSoup(_html_source, 'html.parser')

        # 返回漫画名
        return _soup.find_all('p', attrs={'class': 'detail-info-title'})[0].string.strip()

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

        # 直接获取源码方式会超时, 禁止下载图片和css
        _html_source = NetTool.get_web_page_dom_code(
            index_url,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': 'n',
                'until_menthod': EC.presence_of_element_located((By.ID, "chapterlistload"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
        )
        _soup = BeautifulSoup(_html_source, 'html.parser')

        _voldict = dict()
        _vollist = _soup.find_all(
            'div', attrs={
                'id': 'chapterlistload',
                'class': 'detail-list-form-con'
            }
        )[0]
        for _vol in _vollist.children:
            if _vol.name != 'a':
                continue

            _vol_name = _vol.next.string.strip()
            _vol_url = '%s://%s/%s' % (
                _url_info.scheme, _url_info.netloc, _vol['href']
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

        # 需要用动态生成的html dom对象，从第一张图片找真实地址
        _html_source = NetTool.get_web_page_dom_code(
            vol_url,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.ID, "lbcurrentpage"))
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
        )
        _soup_source = BeautifulSoup(_html_source, 'html.parser')
        _page = _soup_source.find_all('span', attrs={'id': 'lbcurrentpage'})[0].next_sibling.string
        _page = int(_page[1:])

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        _i = 1
        while _i <= _page:
            _name = StringTool.fill_fix_string(str(_i), 5, '0')
            _file_url = os.path.join(vol_url, '#ipg%d' % _i)
            _filedict[_name] = [_file_url, 'Mangabz']
            _i += 1

        return [None, _filedict]


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

    _para_dict['url'] = 'https://www.manhuagui.com/comic/18423/'

    # _name = ManhuaguiDriver.get_name_by_url(**_para_dict)
    # print('<>%s<>' % _name)

    # _vol_info = ManhuaguiDriver._get_vol_info(_para_dict['url'], **_para_dict)
    # print(_vol_info)

    _file_info = ManhuaguiDriver._get_file_info(
        'https://www.manhuagui.com//comic/18423/203289.html', None, **_para_dict)
    print(_file_info)

    # https://www.manhuadb.com/manhua/9391
    # http://www.ccdm13.com/
    # http://www.veryimapp.com/
    # http://www.fmhuaaa.net/
    # http://manhua.dmzj.com/
    # https://www.manhuagui.com/
    # https://www.tohomh123.com/
