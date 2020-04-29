#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
初始化的部分动画网站下载驱动
@module init_drivers_cartoon
@file init_drivers_cartoon.py
"""

import os
import sys
import re
import time
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


__MOUDLE__ = 'init_drivers_cartoon'  # 模块名
__DESCRIPT__ = u'初始化的部分动画网站下载驱动'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.04.12'  # 发布日期


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


class YouKuPlayListDriver(BaseDriverFW):
    """
    www.youku.com Youku的下载驱动
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
        _voldict = {
            'Video': index_url
        }
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
        _url_info = urlparse(vol_url)

        # 需要用动态生成的html dom对象，从第一张图片找真实地址
        _html_source = NetTool.get_web_page_dom_code(
            vol_url,
            common_options={
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': True,
                'roll_to_end': True,  # 要滚动加载更多
                'until_menthod': EC.invisibility_of_element_located((By.ID, "loadMore")),  # 没有加载更多
                'size_type': ('min' if para_dict['wd_min'] == 'y' else '')
            },
            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
        )
        _soup_source = BeautifulSoup(_html_source, 'html.parser')
        _file_list = _soup_source.find_all('li', attrs={'class': 'title short-title'})

        # 解析文件清单并拆分放入字典
        _filedict = dict()
        for _file in _file_list:
            _file_url = '%s:%s' % (_url_info.scheme, _file.a['href'])
            _file_url_info = urlparse(_file_url)
            _name = os.path.split(_file_url_info.path)[1]
            _filedict[_name] = [_file_url, 'you-get']

        return [None, _filedict]


class YouKuShowDriver(BaseDriverFW):
    """
    www.youku.com Youku的下载驱动
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
            'v.youku.com': 'YouKu播放页(视频)'
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
        _name = 'no_name'
        _spans = _soup.find_all('h1', attrs={'id': 'left-title-content-wrap'})[0].children
        for _span in _spans:
            if _span['class'][0] == 'subtitle':
                if _span.string is not None:
                    _name = _span.string
                else:
                    _name = _span.a.string
        return _name

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
        _voldict = {
            'Video': index_url
        }
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
        # _url_info = urlparse(vol_url)
        _html_code = NetTool.get_web_page_code(
            para_dict['url'], timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        _filedict = dict()

        _select_page = _soup.find_all('a', attrs={'class': 'current-page'})
        if len(_select_page) > 0:
            # 有多页的情况, 更换为通过dom方式处理
            _common_options = {
                'timeout': float(para_dict['wd_overtime']),
                'headless': (para_dict['wd_headless'] == 'y'),
                'wait_all_loaded': (para_dict['wd_wait_all_loaded'] == 'y'),
                'until_menthod': EC.presence_of_element_located((By.CLASS_NAME, "paged-wrap")),
                'size_type': ('min' if para_dict['wd_min'] == 'y' else ''),
                'quit': False
            }
            _browser = NetTool.get_webdriver_browser(
                common_options=_common_options,
                webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
                driver_options=NO_IMG_CSS_DRIVER_OPTIONS
            )
            _html_source = NetTool.get_web_page_dom_code(
                vol_url,
                browser=_browser,
                common_options=_common_options,
                webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
                driver_options=NO_IMG_CSS_DRIVER_OPTIONS
            )
            _soup_source = BeautifulSoup(_html_source, 'html.parser')

            # 点击选页标签
            _pages = _soup_source.find_all('div', attrs={'class': 'paged-wrap'})[0]
            _i = 1
            for _tag in _pages.dt.children:
                # 获得标准链接地址
                _el = _browser.find_element_by_xpath('//*[@class="paged-wrap"]/dt/a[%s]' % str(_i))
                _el.click()
                _i += 1

                # 等待1秒, 加载网页内容
                time.sleep(1)

                # 获取源码
                _soup = BeautifulSoup(_browser.page_source, 'html.parser')

                # 获取清单
                _file_list = _soup.find_all('div', attrs={'class': 'anthology-content'})[0]

                # 解析文件清单并拆分放入字典
                for _file in _file_list.children:
                    if _file.name == 'a':
                        _file_url = _file['href']
                    else:
                        _file_url = _file.a['href']

                    _file_url_info = urlparse(_file_url)
                    _name = os.path.split(_file_url_info.path)[1]
                    _filedict[_name] = [_file_url, 'you-get']
        else:
            # 只有1页， 直接取第1个
            _file_list = _soup.find_all('div', attrs={'class': 'anthology-content'})[0]

            # 解析文件清单并拆分放入字典
            for _file in _file_list.children:
                if _file.name == 'a':
                    _file_url = _file['href']
                else:
                    _file_url = _file.a['href']

                _file_url_info = urlparse(_file_url)
                _name = os.path.split(_file_url_info.path)[1]
                _filedict[_name] = [_file_url, 'you-get']

        return [None, _filedict]


class EddDriver(BaseDriverFW):
    """
    www.edddh.com EDD的下载驱动
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
            'www.edddh.com': 'EDD动漫-E站(视频, 请传入播放页url)'
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
        _name = 'no_name'
        _div = _soup.find_all('div', attrs={'class': 'player_title'})[0].div
        for _tag in _div.children:
            if _tag.name == 'a':
                _name = _tag.string
        return _name

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
        _voldict = {
            'Video': index_url
        }
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
        _url_info = urlparse(vol_url)
        _html_code = NetTool.get_web_page_code(
            para_dict['url'], timeout=float(para_dict['overtime']),
            encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
        )
        _soup = BeautifulSoup(_html_code, 'html.parser')

        # 获取当前激活的线路
        _playlists = _soup.find_all('div', attrs={'class': 'player_playlist'})[0]
        _current_list = None
        for _list in _playlists.children:
            if 'active' in _list['class']:
                _current_list = _list.children
                break

        # 每个页获取实际下载对象
        _filedict = dict()
        for _file in _current_list:
            _file_url = '%s://%s/%s' % (
                _url_info.scheme, _url_info.netloc, _file.a['href']
            )
            _file_name = _file.a.string

            _html_source = NetTool.get_web_page_code(
                _file_url, timeout=float(para_dict['overtime']),
                encoding=para_dict['encoding'], retry=int(para_dict['connect_retry'])
            )

            _soup_source = BeautifulSoup(_html_source, 'html.parser')
            _script = _soup_source.find_all(
                'div', attrs={'id': 'zanpiancms_player'}
            )[0].div.script.string
            _script = _script[_script.find('{'):].replace(
                '\\', '').replace(':null,', ':"",').rstrip(';')
            _player_para = eval(_script)
            _player_url_info = urlparse(_player_para['url'])
            if _player_url_info.netloc == 'v.youku.com':
                # 优酷的下载
                _real_file_url = _player_para['url']
                _filedict[_file_name] = [_real_file_url, 'you-get']
            elif _player_url_info.query.endswith('.mp4'):
                # 'vd=https://gss3.baidu.com/6LZ0ej3k1Qd3ote6lo7D0j9wehsv/tieba-smallvideo/607272_c32fd7e6d6f83ad280c77bf3b9b6f004.mp4'
                _filedict[_file_name+'.mp4'] = [_player_url_info.query[3:], 'http']
            elif _player_url_info.netloc in ('xs0xs.xyz'):
                # 需要从动态iframe中获取
                _retry = 0
                while True:
                    try:
                        _html_source = NetTool.get_web_page_dom_code(
                            _file_url,
                            common_options={
                                'timeout': float(para_dict['wd_overtime']),
                                'headless': (para_dict['wd_headless'] == 'y'),
                                'wait_all_loaded': False,
                                'until_menthod': EC.presence_of_element_located((By.ID, "zanpiancms_player")),
                                'size_type': ('min' if para_dict['wd_min'] == 'y' else '')
                            },
                            webdriver_type=cls.get_webdriver_type(para_dict['webdriver']),
                            driver_options=NO_IMG_CSS_DRIVER_OPTIONS
                        )
                        # 成功执行，跳出循环
                        break
                    except:
                        if _retry <= int(para_dict['connect_retry']):
                            _retry += 1
                            continue
                        else:
                            raise

                # 获取第
                _soup_source = BeautifulSoup(_html_source, 'html.parser')
                _real_src = _soup_source.find_all(
                    'iframe', attrs={'class': 'zanpiancms-play-iframe', 'allowfullscreen': 'true'}
                )[0]['src']
                if _real_src[0: 2] == '//':
                    _real_src = 'http:' + _real_src
                elif _real_src[0: 4] != 'http':
                    _real_src = 'http://' + _real_src

                # 再次获取
                _real_url = ['']
                _html_code = NetTool.get_web_page_code(
                    _real_src, timeout=float(para_dict['overtime']),
                    encoding=para_dict['encoding'], retry=int(para_dict['connect_retry']),
                    real_url=_real_url
                )
                _real_file_url = re.findall(
                    '(?:video\:\s*)\{.*\}(?=\}\);)', _html_code, re.M)[0].lstrip('video: ')
                _real_file_url = _real_file_url.replace(' ', '').replace(
                    ',}', '}').replace(',', ',\'').replace(':\'', '\':\'').replace('{', '{\'')
                _temp_dict = eval(
                    _real_file_url
                )
                _filedict[_file_name+'.mp4'] = [_temp_dict['url'], 'http']
            else:
                # 播放器
                _real_url = ['']
                _html_code = NetTool.get_web_page_code(
                    _player_para['url'], timeout=float(para_dict['overtime']),
                    encoding=para_dict['encoding'], retry=int(para_dict['connect_retry']),
                    real_url=_real_url
                )
                _m3u8_match = re.findall(
                    '(?![\'\"])https{0,1}://.*/*\.m3u8(?=[\'\"])', _html_code, re.M)
                _m3u8 = _m3u8_match[0]

                _filedict[_file_name] = [_m3u8, 'm3u8']

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
        'show_rate': 'n',
        'wd_min': 'n'
    }

    # _para_dict['url'] = 'https://v.youku.com/v_show/id_XNDM3ODM0MDM2NA==.html?spm=a2hcb.12523958.m_4392_c_25192.d_2&s=d6bc38efbfbdefbfbdef&scm=20140719.manual.4392.show_d6bc38efbfbdefbfbdef'
    _para_dict['url'] = 'http://www.edddh.com/vod/yishoumodudorohedoro/2-1.html'

    # _name = EddDriver.get_name_by_url(**_para_dict)
    # print('<>%s<>' % _name)

    # _vol_info = EddDriver._get_vol_info(_para_dict['url'], **_para_dict)
    # print(_vol_info)

    _file_info = EddDriver._get_file_info(
        'http://www.edddh.com/vod/yishoumodudorohedoro/2-1.html', None, **_para_dict)
    print(_file_info)
