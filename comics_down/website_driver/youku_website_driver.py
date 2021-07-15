#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
优酷网站下载驱动
@module youku_website_driver
@file youku_website_driver.py
"""

import os
import sys
import time
import copy
from HiveNetLib.base_tools.string_tool import StringTool
from HiveNetLib.html_parser import HtmlParser
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseWebSiteDriverFW
from comics_down.lib.webdriver_tool import WebDriverTool


class YouKuPlayListDriver(BaseWebSiteDriverFW):
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

        @return {str} - 漫画名
        """
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
        return {
            'vol_next_url': '',
            'vols': {
                'Video': {'url': index_url}
            }
        }

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
        # 解析页面代码
        print('get_file_info: ', vol_url)
        # _url_info = urlparse(vol_url)

        # 需要用动态生成的html dom对象, 指定某些特定的参数
        _para_dict = copy.deepcopy(para_dict)
        _para_dict['wd_wait_all_loaded'] = 'y'
        _para_dict['wd_no_image'] = 'y'

        # 需要操作页面，因此打开浏览器方式处理
        _parser = WebDriverTool(_para_dict)
        time.sleep(5)
        _filedict = dict()
        _current_more_page = 0
        while True:
            # _html_source = _webdriver.get_current_dom()
            # _parser = HtmlParser(_html_source)

            _file_list = _parser.find_elements([
                ['xpath', '//div[@class="anthology-content" and @data-spm and @data-spm-max-idx]/a[@href]']
            ])

            # 解析文件清单并拆分放入字典
            for _file in _file_list:
                _file_url = _file.get_attribute('href')  # 获取访问url
                _title = _file.get_attribute('title')  # 当前集的标题

                # 获取集数
                _vol_num = '1'
                _span = _parser.find_elements(
                    [['xpath', './/span[@class="label-text"]']], parent=_file
                )
                if len(_span) > 0:
                    _vol_num = _span[0].text

                _name = '%s-%s' % (
                    StringTool.fill_fix_string(_vol_num, 5, fill_char='0', left=True), _title
                )

                # 添加到下载集合
                _filedict[_name] = {'url': _file_url, 'downtype': 'you-get'}

            # 判断是否有选集的情况
            _current_page = _parser.find_elements(
                [['xpath', '//div[@class="paged-wrap"]/dt/a[@class="current-page"]']]
            )
            if len(_current_page) == 0:
                # 没有选集的情况
                break

            if _current_more_page == 0:
                # 还没有点到更多视频
                _next_page = _parser.find_elements(
                    [['xpath', './following-sibling::a[1]']], parent=_current_page[0]
                )
                if len(_next_page) > 0:
                    if len(_parser.find_elements([['xpath', './span/i']], parent=_next_page[0])) > 0:
                        # 下一个是更多视频，需要点击并选集
                        _parser.do_script(
                            [
                                ['click'],  # 点击更多调整，弹出更多选集的菜单
                                ['wait', '1'],  # 等待
                                ['find', 'xpath', '//div[@class="paged-wrap"]/dd/a[1]'],  # 获取第一个元素
                                # ['scroll_into_view'],  # 滚动到视线范围
                                ['click'],  # 点击换页
                            ],
                            parent=_next_page[0]
                        )
                        _current_more_page += 2
                    else:
                        # 下一个还是直接选集，点击就好
                        _next_page[0].click()

                    time.sleep(1)
                    continue
                else:
                    # 是最后一个，选项，退出
                    break
            else:
                # 更多选集的处理
                if len(_parser.find_elements([['xpath', '//div[@class="paged-wrap"]/dd/a[%d]' % _current_more_page]])) == 0:
                    # 已经到最后一个了
                    break

                # 执行下一个的点击
                _parser.do_script(
                    [
                        ['find', 'xpath', '//div[@class="paged-wrap"]/dt/a[@class="current-page"]'],
                        ['click'],  # 点击更多调整，弹出更多选集的菜单
                        ['wait', '1'],  # 等待
                        ['find', 'xpath', '//div[@class="paged-wrap"]/dd/a[%d]' %
                            _current_more_page],  # 获取第一个元素
                        # ['scroll_into_view'],  # 滚动到视线范围
                        ['click'],  # 点击换页
                        ['wait', '1']  # 等待
                    ]
                )
                _current_more_page += 1

        return {
            'next_tran_para': None,
            'files': _filedict
        }
